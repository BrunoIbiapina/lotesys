# financeiro/views.py
from datetime import date
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import TruncMonth, Coalesce
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from vendas.models import Parcela, Venda
from .models import Despesa


def _parse_date(s: str | None):
    """Transforma 'YYYY-MM-DD' em date ou None."""
    if not s:
        return None
    try:
        y, m, d = map(int, s.split("-"))
        return date(y, m, d)
    except Exception:
        return None


@login_required
def ping(request):
    return HttpResponse("financeiro ok")


@login_required
def extrato(request):
    hoje = timezone.now().date()
    inicio = _parse_date(request.GET.get("inicio")) or hoje.replace(day=1)
    fim = _parse_date(request.GET.get("fim")) or hoje

    # -----------------------------
    # DESPESAS (detalhado no período)
    # -----------------------------
    despesas = (
        Despesa.objects
        .filter(data__range=[inicio, fim])
        .order_by("-data", "-id")
    )

    total_despesas_pagas = despesas.filter(status="PAGA").aggregate(
        v=Coalesce(Sum("valor"), Decimal("0.00"))
    )["v"]

    total_despesas_previstas = despesas.filter(status="PREVISTA").aggregate(
        v=Coalesce(Sum("valor"), Decimal("0.00"))
    )["v"]

    # ---------------------------------------------
    # RECEITAS (parcelas pagas + entradas de vendas)
    # ---------------------------------------------
    # Parcelas pagas (detalhe no período)
    parcelas_pagas = (
        Parcela.objects
        .select_related("venda", "venda__cliente")
        .filter(status="PAGO", data_pagamento__range=[inicio, fim])
        .order_by("-data_pagamento", "-id")
    )
    total_parcelas_pagas = parcelas_pagas.aggregate(
        v=Coalesce(Sum("valor"), Decimal("0.00"))
    )["v"]

    # Entradas de vendas no período (detalhe)
    vendas_periodo = (
        Venda.objects
        .select_related("cliente")
        .filter(data_venda__range=[inicio, fim])
    )

    entradas_detalhe: list[dict] = []
    total_entradas_brutas = Decimal("0.00")
    total_comissoes = Decimal("0.00")          # comissão paga na entrada (limitada pela entrada)
    total_entradas_liquidas = Decimal("0.00")

    for v in vendas_periodo:
        if v.entrada_bruta and v.entrada_bruta > 0:
            entrada_bruta = v.entrada_bruta                  # Decimal
            comissao_entrada = v.comissao_paga_na_entrada    # << usa a propriedade limitada
            entrada_liquida = v.entrada_liquida              # Decimal

            entradas_detalhe.append(
                {
                    "venda": v,
                    "entrada_bruta": entrada_bruta,
                    "comissao": comissao_entrada,            # mostrado na tabela
                    "entrada_liquida": entrada_liquida,
                }
            )
            total_entradas_brutas += entrada_bruta
            total_comissoes += comissao_entrada
            total_entradas_liquidas += entrada_liquida

    total_receitas = (total_parcelas_pagas or Decimal("0.00")) + (total_entradas_liquidas or Decimal("0.00"))

    # -----------------------------------------------------------
    # PARCELAS VENCIDAS (em atraso até hoje)
    # -----------------------------------------------------------
    vencidas = (
        Parcela.objects
        .select_related("venda", "venda__cliente")
        .filter(status="PENDENTE", vencimento__lt=hoje)
        .order_by("vencimento", "id")
    )
    total_vencidas = vencidas.aggregate(
        v=Coalesce(Sum("valor"), Decimal("0.00"))
    )["v"]

    # -----------------------------------------------------------
    # PROJEÇÃO (a receber futuro: parcelas PENDENTES a partir de hoje)
    # -----------------------------------------------------------
    pendentes = (
        Parcela.objects
        .select_related("venda", "venda__cliente")
        .filter(status="PENDENTE", vencimento__gte=hoje)
        .order_by("vencimento", "id")
    )

    total_a_receber = pendentes.aggregate(
        v=Coalesce(Sum("valor"), Decimal("0.00"))
    )["v"]

    por_mes_qs = (
        pendentes
        .annotate(mes=TruncMonth("vencimento"))
        .values("mes")
        .order_by("mes")
        .annotate(total=Coalesce(Sum("valor"), Decimal("0.00")))
    )

    por_mes = []
    for r in por_mes_qs:
        if r["mes"]:
            por_mes.append(
                {"mes_label": r["mes"].strftime("%m/%Y"), "valor": r["total"]}
            )

    # -----------------
    # Contexto da view (mantemos Decimal)
    # -----------------
    ctx = dict(
        hoje=hoje,
        inicio=inicio,
        fim=fim,

        # Despesas
        despesas=despesas,
        total_despesas_pagas=total_despesas_pagas,
        total_despesas_previstas=total_despesas_previstas,

        # Receitas: parcelas pagas
        parcelas_pagas=parcelas_pagas,
        total_parcelas_pagas=total_parcelas_pagas,

        # Receitas: entradas de vendas (detalhe + totais)
        entradas_detalhe=entradas_detalhe,
        total_entradas_brutas=total_entradas_brutas,
        total_comissoes=total_comissoes,              # comissão paga na entrada
        total_entradas_liquidas=total_entradas_liquidas,

        # Total geral de receitas
        total_receitas=total_receitas,

        # Vencidas
        vencidas=vencidas,
        total_vencidas=total_vencidas,

        # Projeção (a receber)
        pendentes=pendentes,
        total_a_receber=total_a_receber,
        por_mes=por_mes,
    )

    return render(request, "financeiro/extrato.html", ctx)