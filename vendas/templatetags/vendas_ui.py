# mural/templatetags/mural_ui.py
from django import template
from django.utils import timezone
from datetime import timedelta
from mural.models import Mensagem

register = template.Library()

@register.simple_tag(takes_context=True)
def mural_novas_qtd(context, recentes_dias=7):
    """
    Retorna um número com a quantidade de mensagens 'novas' (criada nos últimos X dias).
    Você pode sofisticar depois para per-user (não lidas), etc.
    """
    try:
        dias = int(recentes_dias)
    except Exception:
        dias = 7
    limite = timezone.now() - timedelta(days=dias)
    return Mensagem.objects.filter(created_at__gte=limite).count()

@register.inclusion_tag("mural/_badge.html", takes_context=True)
def mural_badge(context, recentes_dias=7):
    """
    Renderiza o badge (bolinha vermelha) com a contagem.
    Usa o mesmo critério de 'novas' dos últimos X dias.
    """
    qtd = mural_novas_qtd(context, recentes_dias=recentes_dias)
    return {"qtd": qtd}