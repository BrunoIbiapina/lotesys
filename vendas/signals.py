# vendas/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Venda
from .services import gerar_parcelas
from financeiro.models import Despesa

@receiver(post_save, sender=Venda)
def apos_salvar_venda(sender, instance: Venda, created, **kwargs):
    # (re)gera as parcelas sempre que a venda for salva
    gerar_parcelas(instance)

    # cria despesa de comissão na primeira criação da venda
    if created:
        Despesa.objects.create(
            data=instance.data_venda,
            categoria='COMISSAO',
            descricao=f'Comissão venda #{instance.pk}',
            valor=instance.comissao_valor,
            status='PAGA',
            origem='Empresa',
        )