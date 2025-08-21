# mural/templatetags/mural_tags.py
from datetime import timedelta
from django import template
from django.utils import timezone

register = template.Library()

@register.simple_tag(takes_context=True)
def mural_count(context, *, recentes_dias: int = 7) -> int:
    """
    Retorna um número para mostrar no badge do Mural.
    Para já funcionar sem depender de 'lidas', usamos:
      - total de mensagens fixadas OU
      - total de mensagens criadas nos últimos 'recentes_dias'
    Se quiser, depois alteramos para “não lidas por usuário”.
    """
    try:
        # Importa aqui dentro p/ evitar problemas no setup de apps
        from mural.models import Mensagem
    except Exception:
        return 0

    agora = timezone.now()
    recentes = agora - timedelta(days=recentes_dias)

    # conta: fixadas + recentes (distinct)
    qs = Mensagem.objects.all()
    count = qs.filter(fixada=True).count() + qs.filter(criado_em__gte=recentes, fixada=False).count()
    return count


@register.inclusion_tag("mural/_badge.html", takes_context=True)
def mural_badge(context, *, recentes_dias: int = 7):
    """
    Rende um “badge/bolinha” para colocar ao lado do link 'Mural'.
    Aparece:
      - como bolinha (sem número) quando count == 0 (nada de especial)
      - como bolinha com número quando count > 0
    """
    count = mural_count(context, recentes_dias=recentes_dias)
    return {"count": count}