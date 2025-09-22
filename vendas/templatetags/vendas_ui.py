# vendas/templatetags/vendas_ui.py
from django import template
from django.utils import timezone
from datetime import timedelta

register = template.Library()

@register.filter
def parcelas_pagas_porcentagem(venda):
    """
    Calcula a porcentagem de parcelas pagas de uma venda.
    Retorna um número entre 0 e 100.
    """
    if not venda or not hasattr(venda, 'parcelas'):
        return 0
    
    total_parcelas = venda.parcelas_total or 0
    if total_parcelas == 0:
        return 0
    
    parcelas_pagas = venda.parcelas.filter(status='PAGO').count()
    porcentagem = (parcelas_pagas * 100) // total_parcelas
    return porcentagem

@register.filter  
def parcelas_pagas_count(venda):
    """
    Retorna a quantidade de parcelas pagas de uma venda.
    """
    if not venda or not hasattr(venda, 'parcelas'):
        return 0
    return venda.parcelas.filter(status='PAGO').count()