from decimal import Decimal
from dateutil.relativedelta import relativedelta
from .models import Venda, Parcela

def gerar_parcelas(venda: Venda):
    # remove antigas (recria se atualizar a venda)
    Parcela.objects.filter(venda=venda).delete()

    if venda.forma_pagamento == 'AVISTA' or venda.parcelas_total == 0:
        return

    base = venda.data_inicio_parcelamento or venda.data_venda
    restante = venda.valor_total - venda.desconto - venda.entrada_bruta
    if restante < 0:
        restante = Decimal('0.00')

    valor_base = (restante / venda.parcelas_total).quantize(Decimal('0.01'))

    for n in range(1, venda.parcelas_total + 1):
        venc = base + relativedelta(months=n-1)
        Parcela.objects.create(
            venda=venda,
            numero=n,
            valor=valor_base,
            vencimento=venc,
        )