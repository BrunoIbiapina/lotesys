from django import template
from django.utils.html import format_html

register = template.Library()

@register.filter
def brl(value):
    """Formata número em Real (R$)."""
    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ 0,00"

@register.simple_tag
def badge_status(status):
    """Renderiza badge colorida para status (Parcela/Despesa)."""
    mapping = {
        "PAGO": ("bg-green-100 text-green-800", "Pago"),
        "PAGA": ("bg-green-100 text-green-800", "Paga"),
        "PENDENTE": ("bg-yellow-100 text-yellow-800", "Pendente"),
        "PREVISTA": ("bg-yellow-100 text-yellow-800", "Prevista"),
        "VENCIDO": ("bg-red-100 text-red-800", "Vencido"),
    }
    css, label = mapping.get(status, ("bg-gray-100 text-gray-800", status))
    return format_html(
        '<span class="px-2 py-1 text-xs font-semibold rounded-full whitespace-nowrap {}">{}</span>',
        css,
        label
    )