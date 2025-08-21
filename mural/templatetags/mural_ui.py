# mural/templatetags/mural_ui.py
from datetime import timedelta

from django import template
from django.utils import timezone
from django.utils.html import format_html

from mural.models import Mensagem

register = template.Library()


# ------------------------------
# Contador para o badge do menu
# ------------------------------
def _qtd_recentes(dias: int) -> int:
    limite = timezone.now() - timedelta(days=int(dias))
    return Mensagem.objects.filter(criada_em__gte=limite).count()


@register.simple_tag(takes_context=True)
def mural_badge(context, recentes_dias=7):
    try:
        dias = int(recentes_dias)
    except Exception:
        dias = 7

    qtd = _qtd_recentes(dias)
    if qtd <= 0:
        return ""
    return format_html(
        '<span class="absolute -top-1 -right-1 inline-flex items-center justify-center '
        'text-[10px] leading-none font-bold rounded-full bg-red-600 text-white w-4 h-4">{}</span>',
        qtd,
    )


# -----------------------------------------------------
# Filtros de estilo por TIPO (info | aviso | alerta)
# -----------------------------------------------------
_TIPO_STYLES = {
    "info": {
        "icon": "i",
        "card": "border-s-4 border-blue-300 bg-white",
        "chip": "bg-blue-100 text-blue-800",
        "icon_wrap": "bg-blue-50 text-blue-600 ring-1 ring-blue-100",
        "title": "text-blue-900",
    },
    "aviso": {
        "icon": "!",
        "card": "border-s-4 border-amber-300 bg-white",
        "chip": "bg-amber-100 text-amber-800",
        "icon_wrap": "bg-amber-50 text-amber-700 ring-1 ring-amber-100",
        "title": "text-amber-900",
    },
    "alerta": {
        "icon": "⚠",
        "card": "border-s-4 border-red-300 bg-white",
        "chip": "bg-red-100 text-red-800",
        "icon_wrap": "bg-red-50 text-red-700 ring-1 ring-red-100",
        "title": "text-red-900",
    },
}

# Defaults se vier um tipo fora da lista
_DEFAULT_STYLE = {
    "icon": "●",
    "card": "border-s-4 border-gray-300 bg-white",
    "chip": "bg-gray-100 text-gray-800",
    "icon_wrap": "bg-gray-50 text-gray-700 ring-1 ring-gray-100",
    "title": "text-gray-900",
}


def _style_for(tipo: str):
    if not tipo:
        return _DEFAULT_STYLE
    return _TIPO_STYLES.get(tipo.lower().strip(), _DEFAULT_STYLE)


@register.filter
def tipo_card(tipo: str) -> str:
    """Classe do card (borda colorida do lado)."""
    return _style_for(tipo)["card"]


@register.filter
def tipo_chip(tipo: str) -> str:
    """Classe do chip do tipo."""
    return _style_for(tipo)["chip"]


@register.filter
def tipo_iconwrap(tipo: str) -> str:
    """Classe da bolinha do ícone."""
    return _style_for(tipo)["icon_wrap"]


@register.filter
def tipo_title(tipo: str) -> str:
    """Classe de título por tipo (contraste melhor)."""
    return _style_for(tipo)["title"]


@register.filter
def tipo_icon(tipo: str) -> str:
    """Símbolo simples por tipo (pode trocar por SVG depois)."""
    return _style_for(tipo)["icon"]