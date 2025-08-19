# vendas/utils.py
from __future__ import annotations
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from dateutil.relativedelta import relativedelta

from .models import Parcela, Venda


def _round2(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _datas(venda: Venda, qtd: int):
    """
    Primeira parcela em:
      - venda.data_inicio_parcelamento, se informado
      - senão: 1 mês após data_venda
    Demais: mês a mês.
    """
    if venda.data_inicio_parcelamento:
        base = venda.data_inicio_parcelamento
    else:
        base = venda.data_venda + relativedelta(months=+1)
    return [base + relativedelta(months=+i) for i in range(qtd)]


def _dividir_iguais(total: Decimal, n: int) -> list[Decimal]:
    """
    Divide 'total' em n partes quase iguais (2 casas),
    ajustando a última para fechar exato.
    """
    if n <= 0:
        return []
    base = (total / Decimal(n)).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    vals = [base] * n
    diff = total - sum(vals)
    vals[-1] = _round2(vals[-1] + diff)
    return vals


def gerar_parcelas_automaticas(venda: Venda, *, recriar: bool = True) -> int:
    """
    Gera parcelas automaticamente:
      - saldo = valor_total - entrada_bruta - desconto
      - precisa forma_pagamento='PARCELADO' e parcelas_total>0 e saldo>0
      - divide igualmente e ajusta a última
      - recriar=True apaga as parcelas existentes antes de gerar
    Retorna a quantidade gerada.
    """
    # Sempre limpamos se não for parcelado
    if venda.forma_pagamento != "PARCELADO":
        if recriar:
            venda.parcelas.all().delete()
        return 0

    qtd = int(venda.parcelas_total or 0)
    if qtd <= 0:
        if recriar:
            venda.parcelas.all().delete()
        return 0

    saldo = _round2(venda.valor_total - venda.entrada_bruta - venda.desconto)
    if saldo <= 0:
        if recriar:
            venda.parcelas.all().delete()
        return 0

    datas = _datas(venda, qtd)
    valores = _dividir_iguais(saldo, qtd)

    if recriar:
        venda.parcelas.all().delete()

    objs = []
    for i in range(qtd):
        objs.append(
            Parcela(
                venda=venda,
                numero=i + 1,
                valor=_round2(valores[i]),
                vencimento=datas[i],
                status="PENDENTE",
            )
        )
    Parcela.objects.bulk_create(objs)
    return len(objs)