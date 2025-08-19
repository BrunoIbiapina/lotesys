# vendas/templatetags/compat.py
from django import template

register = template.Library()

@register.filter(name="length_is")
def length_is(value, arg):
    """
    Compat: reproduz o filtro removido no Django 5.
    Retorna True se len(value) == int(arg).
    """
    try:
        return len(value) == int(arg)
    except Exception:
        return False