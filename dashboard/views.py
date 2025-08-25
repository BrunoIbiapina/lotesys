# dashboard/views.py
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import TruncMonth, Coalesce
from django.http import HttpRequest
from django.shortcuts import render
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from vendas.models import Venda
from financeiro.models import Despesa
try:
    from vendas.models import Parcela
except Exception:
    from financeiro.models import Parcela


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        y, m, d = map(int, s.split("-"))
        return date(y, m, d)
    except Exception:
        return None


@login_required
def index(request: HttpRequest):
    hoje = timezone.localdate()

    # ---------- Período (padrão = mês atual) ----------
    inicio = _parse_date(request.GET.get("inicio")) or hoje.replace(day=1)
    fim = _parse_date(request.GET.get("fim")) or hoje

    # ================= KPIs do período =================
    a_receber = (
        Parcela.objects.filter(status__iexact="PENDENTE", vencimento__range=[inicio, fim])
        .aggregate(total=Coalesce(Sum("valor"), Decimal("0.00")))["total"]
        or Decimal("0")
    )

    vencidas_qs = Parcela.objects.filter(status__iexact="PENDENTE", vencimento__lt=hoje)
    vencidas_valor = (
        vencidas_qs.aggregate(total=Coalesce(Sum("valor"), Decimal("0.00")))["total"]
        or Decimal("0")
    )
    vencidas_qtd = vencidas_qs.count()

    proximos_7_fim = hoje + timedelta(days=7)
    prox7_qs = Parcela.objects.filter(
        status__iexact="PENDENTE", vencimento__range=[hoje, proximos_7_fim]
    )
    prox7_valor = (
        prox7_qs.aggregate(total=Coalesce(Sum("valor"), Decimal("0.00")))["total"]
        or Decimal("0")
    )
    prox7_qtd = prox7_qs.count()

    pagas = (
        Parcela.objects.filter(status__iexact="PAGO", data_pagamento__range=[inicio, fim])
        .aggregate(total=Coalesce(Sum("valor"), Decimal("0.00")))["total"]
        or Decimal("0")
    )

    # Entradas líquidas no período (somatório por venda)
    entradas_liquidas = sum(
        (v.entrada_liquida for v in Venda.objects.filter(data_venda__range=[inicio, fim])),
        Decimal("0.00"),
    )

    despesas_pagas = (
        Despesa.objects.filter(status__iexact="PAGA", data__range=[inicio, fim])
        .aggregate(total=Coalesce(Sum("valor"), Decimal("0.00")))["total"]
        or Decimal("0")
    )

    despesas_previstas = (
        Despesa.objects.filter(status__iexact="PREVISTA", data__range=[inicio, fim])
        .aggregate(total=Coalesce(Sum("valor"), Decimal("0.00")))["total"]
        or Decimal("0")
    )

    fluxo_liquido = (pagas + entradas_liquidas) - despesas_pagas

    # ---------- PARCELAS QUE VENCEM HOJE ----------
    vencem_hoje_qs = (
        Parcela.objects.filter(status__iexact="PENDENTE", vencimento=hoje)
        .select_related("venda", "venda__cliente")
        .order_by("vencimento", "venda_id", "numero")
    )
    total_vencem_hoje = vencem_hoje_qs.aggregate(s=Sum("valor"))["s"] or Decimal("0")
    vencem_hoje_count = vencem_hoje_qs.count()

    # ================= Resumo de HOJE =================
    parcelas_pagas_hoje = (
        Parcela.objects.filter(status__iexact="PAGO", data_pagamento=hoje)
        .aggregate(total=Coalesce(Sum("valor"), Decimal("0.00")))["total"]
        or Decimal("0")
    )
    entradas_liquidas_vendas_hoje = sum(
        (v.entrada_liquida for v in Venda.objects.filter(data_venda=hoje)),
        Decimal("0.00"),
    )
    entradas_hoje = parcelas_pagas_hoje + entradas_liquidas_vendas_hoje

    despesas_hoje = (
        Despesa.objects.filter(status__iexact="PAGA", data=hoje)
        .aggregate(total=Coalesce(Sum("valor"), Decimal("0.00")))["total"]
        or Decimal("0")
    )
    fluxo_hoje = entradas_hoje - despesas_hoje

    # ================= Séries (últimos 6 meses) =================
    meses_qs = (
        Parcela.objects.filter(status__iexact="PAGO")
        .annotate(mes=TruncMonth("data_pagamento"))
        .values("mes")
        .annotate(recebido=Coalesce(Sum("valor"), Decimal("0.00")))
    )
    despesas_qs = (
        Despesa.objects.filter(status__iexact="PAGA")
        .annotate(mes=TruncMonth("data"))
        .values("mes")
        .annotate(gasto=Coalesce(Sum("valor"), Decimal("0.00")))
    )

    def to_map(qs, key, val):
        out = {}
        for r in qs:
            if r[key]:
                out[r[key].strftime("%Y-%m")] = r[val]
        return out

    rec_map = to_map(meses_qs, "mes", "recebido")
    des_map = to_map(despesas_qs, "mes", "gasto")

    labels, recebido_series, gasto_series, fluxo_series = [], [], [], []
    year, month = hoje.year, hoje.month
    for i in range(5, -1, -1):
        m = month - i
        y = year
        if m <= 0:
            m += 12
            y -= 1
        key = f"{y:04d}-{m:02d}"
        labels.append(key)
        r = rec_map.get(key, Decimal("0.00"))
        g = des_map.get(key, Decimal("0.00"))
        recebido_series.append(float(r))
        gasto_series.append(float(g))
        fluxo_series.append(float(r - g))

    # ================= Amostras p/ cards =================
    ultimas_parcelas = (
        Parcela.objects.select_related("venda", "venda__cliente")
        .order_by("-vencimento")[:10]
    )
    despesas_periodo = Despesa.objects.filter(data__range=[inicio, fim]).order_by("-data")[:10]
    parcelas_pagas_periodo = (
        Parcela.objects.filter(status__iexact="PAGO", data_pagamento__range=[inicio, fim])
        .select_related("venda", "venda__cliente")
        .order_by("-data_pagamento")[:10]
    )

    ctx = dict(
        # filtros
        inicio=inicio,
        fim=fim,
        hoje=hoje,

        # KPIs principais do período
        a_receber=float(a_receber),
        vencidas=float(vencidas_valor),
        pagas=float(pagas),
        entradas_liquidas=float(entradas_liquidas),
        despesas_pagas=float(despesas_pagas),
        despesas_previstas=float(despesas_previstas),
        fluxo_liquido=float(fluxo_liquido),

        # Resumo HOJE (mantém Decimal; template usa |brl)
        entradas_hoje=entradas_hoje,
        despesas_hoje=despesas_hoje,
        fluxo_hoje=fluxo_hoje,

        # Séries p/ Chart.js
        labels=labels,
        recebido_series=recebido_series,
        gasto_series=gasto_series,
        fluxo_series=fluxo_series,

        # Listas
        ultimas_parcelas=ultimas_parcelas,
        despesas_periodo=despesas_periodo,
        parcelas_pagas_periodo=parcelas_pagas_periodo,

        # Alertas
        vencidas_qtd=vencidas_qtd,
        vencidas_valor=float(vencidas_valor),
        prox7_qtd=prox7_qtd,
        prox7_valor=float(prox7_valor),

        # Vencem HOJE
        vencem_hoje=vencem_hoje_qs,
        total_vencem_hoje=total_vencem_hoje,
        vencem_hoje_count=vencem_hoje_count,
    )
    return render(request, "dashboard/index.html", ctx)