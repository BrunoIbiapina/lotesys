# dashboard/views.py
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import TruncMonth, Coalesce
from django.http import HttpRequest
from django.shortcuts import render
from django.utils import timezone
from financeiro.views import _monta_contexto_extrato

from financeiro.models import Despesa
from vendas.models import Venda, Parcela


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        y, m, d = map(int, s.split("-"))
        return date(y, m, d)
    except Exception:
        return None

def _month_bounds(any_day: date) -> tuple[date, date]:
    start = any_day.replace(day=1)
    if start.month == 12:
        next_start = start.replace(year=start.year + 1, month=1)
    else:
        next_start = start.replace(month=start.month + 1)
    end = next_start - timedelta(days=1)
    return start, end


@login_required
def index(request: HttpRequest):
    hoje = timezone.localdate()

    # ---------- Período (padrão = mês atual) ----------
    inicio = _parse_date(request.GET.get("inicio")) or hoje.replace(day=1)
    fim = _parse_date(request.GET.get("fim")) or hoje

    # ================= KPIs do período =================
    ctx_periodo = _monta_contexto_extrato(inicio, fim)

    a_receber = ctx_periodo["total_a_receber"]

    vencidas_qs = Parcela.objects.filter(status__iexact="PENDENTE", vencimento__lt=hoje)
    vencidas_valor = (
        vencidas_qs.aggregate(total=Coalesce(Sum("valor"), Decimal("0.00")))
        ["total"]
        or Decimal("0")
    )
    vencidas_qtd = vencidas_qs.count()

    proximos_7_fim = hoje + timedelta(days=7)
    prox7_qs = Parcela.objects.filter(
        status__iexact="PENDENTE", vencimento__range=[hoje, proximos_7_fim]
    )
    prox7_valor = (
        prox7_qs.aggregate(total=Coalesce(Sum("valor"), Decimal("0.00")))
        ["total"]
        or Decimal("0")
    )
    prox7_qtd = prox7_qs.count()

    pagas = ctx_periodo["total_parcelas_pagas"]
    entradas_liquidas = ctx_periodo["total_entradas_liquidas"]
    despesas_pagas = ctx_periodo["total_despesas_pagas"]            # contábil (card informativo)
    despesas_previstas = ctx_periodo["total_despesas_previstas"]

    # Fluxo líquido do período (idêntico ao Extrato)
    fluxo_liquido = ctx_periodo["fluxo_liquido"]

    # ---------- PARCELAS QUE VENCEM HOJE ----------
    vencem_hoje_qs = (
        Parcela.objects.filter(status__iexact="PENDENTE", vencimento=hoje)
        .select_related("venda", "venda__cliente")
        .order_by("vencimento", "venda_id", "numero")
    )
    total_vencem_hoje = vencem_hoje_qs.aggregate(s=Sum("valor"))["s"] or Decimal("0")
    vencem_hoje_count = vencem_hoje_qs.count()

    # ================= Resumo de HOJE =================
    ctx_hoje = _monta_contexto_extrato(hoje, hoje)
    entradas_hoje = ctx_hoje["total_receitas"]
    despesas_hoje = ctx_hoje["total_despesas_pagas_fluxo"]
    fluxo_hoje = ctx_hoje["fluxo_liquido"]

    # ================= Séries (últimos 6 meses) =================
    labels, recebido_series, gasto_series, fluxo_series = [], [], [], []

    first_of_this_month = hoje.replace(day=1)
    months: list[date] = []
    y, m = first_of_this_month.year, first_of_this_month.month
    for i in range(5, -1, -1):
        mm = m - i
        yy = y
        while mm <= 0:
            mm += 12
            yy -= 1
        months.append(date(yy, mm, 1))

    for month_start in months:
        m_start, m_end = _month_bounds(month_start)
        ctx_m = _monta_contexto_extrato(m_start, m_end)
        labels.append(f"{m_start:%Y-%m}")
        recebido_series.append(float(ctx_m["total_receitas"] or 0))
        gasto_series.append(float(ctx_m["total_despesas_pagas"] or 0))   # contábil no gráfico
        fluxo_series.append(float(ctx_m["fluxo_liquido"] or 0))          # fluxo ajustado

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

    # ===== Listas detalhadas para os cards (limitadas) =====
    vencidas_list_qs = (
        vencidas_qs.select_related("venda", "venda__cliente")
        .order_by("vencimento", "venda_id", "numero")
    )
    prox7_list_qs = (
        prox7_qs.select_related("venda", "venda__cliente")
        .order_by("vencimento", "venda_id", "numero")
    )
    VISIBLE_MAX = 5
    vencidas_list = list(vencidas_list_qs[:VISIBLE_MAX])
    prox7_list = list(prox7_list_qs[:VISIBLE_MAX])
    vencidas_has_more = vencidas_list_qs.count() > VISIBLE_MAX
    prox7_has_more = prox7_list_qs.count() > VISIBLE_MAX

    # total de cards presentes (para o grid do template)
    alerts_count = int(bool(vencidas_qtd)) + int(bool(vencem_hoje_count)) + int(bool(prox7_qtd))

    ctx = dict(
        # filtros
        inicio=inicio,
        fim=fim,
        hoje=hoje,

        # KPIs principais do período
        a_receber=a_receber,
        vencidas=vencidas_valor,
        pagas=pagas,
        entradas_liquidas=entradas_liquidas,
        despesas_pagas=despesas_pagas,
        despesas_previstas=despesas_previstas,
        fluxo_liquido=fluxo_liquido,

        # Adicionais úteis
        despesas_pagas_fluxo=ctx_periodo["total_despesas_pagas_fluxo"],
        comissao_paga_no_periodo=ctx_periodo["total_despesas_comissao_pagas"],

        # Resumo HOJE (mantém Decimal; o template usa |brl)
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

        # Alertas (contagens/valores)
        vencidas_qtd=vencidas_qtd,
        vencidas_valor=vencidas_valor,
        prox7_qtd=prox7_qtd,
        prox7_valor=prox7_valor,

        # Vencem HOJE
        vencem_hoje=vencem_hoje_qs,
        total_vencem_hoje=total_vencem_hoje,
        vencem_hoje_count=vencem_hoje_count,

        # Listas dos cards + flags
        vencidas_list=vencidas_list,
        prox7_list=prox7_list,
        vencidas_has_more=vencidas_has_more,
        prox7_has_more=prox7_has_more,

        # Para o grid responsivo dos alertas
        alerts_count=alerts_count,
    )
    return render(request, "dashboard/index.html", ctx)