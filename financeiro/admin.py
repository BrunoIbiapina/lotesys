# -*- coding: utf-8 -*-
from django.contrib import admin
from django.utils.html import format_html
from .models import Despesa, ReceitaExtra


def _brl(value) -> str:
    """Formata número em moeda brasileira (R$ 12.345,67)."""
    try:
        v = float(value or 0)
    except Exception:
        v = 0.0
    s = f"{v:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


# ==================== DESPESA ====================

@admin.register(Despesa)
class DespesaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "categoria",
        "descricao_truncated",
        "valor_formatted",
        "has_comprovante",
        "data",
        "status_colored",
        "origem_colored",
        "data_cadastro",
    )
    list_filter = ("categoria", "status", "origem", "data")
    search_fields = ("descricao",)
    date_hierarchy = "data"
    ordering = ("-data",)
    list_per_page = 50

    fieldsets = (
        ("📋 Informações Básicas", {
            "fields": ("data", "categoria", "descricao"),
            "classes": ("wide",),
        }),
        ("💰 Valores", {
            "fields": ("valor", "status"),
            "classes": ("wide",),
        }),
        ("📎 Comprovante", {
            "fields": ("comprovante",),
            "classes": ("wide",),
            "description": "Anexe o comprovante da despesa (PDF, imagem, etc.)",
        }),
        ("🔄 Sistema", {
            "fields": ("origem",),
            "classes": ("collapse",),
        }),
    )

    # ----- helpers de exibição -----
    def descricao_truncated(self, obj):
        texto = getattr(obj, "descricao", "") or ""
        if len(texto) > 50:
            return format_html('<span title="{}">{}...</span>', texto, texto[:50])
        return texto
    descricao_truncated.short_description = "📝 Descrição"

    def valor_formatted(self, obj):
        return format_html(
            '<span style="font-weight:bold; font-size:1.05em;">{}</span>',
            _brl(getattr(obj, "valor", 0)),
        )
    valor_formatted.short_description = "💸 Valor"

    def status_colored(self, obj):
        colors = {
            "PREVISTA": "#f59e0b",  # amarelo
            "PAGA": "#10b981",      # verde
        }
        status_value = getattr(obj, "status", "")
        color = colors.get(status_value, "#6b7280")
        label = getattr(obj, "get_status_display", lambda: status_value)()
        return format_html('<span style="color:{}; font-weight:bold;">{}</span>', color, label)
    status_colored.short_description = "🎯 Status"

    def origem_colored(self, obj):
        colors = {"MANUAL": "#3b82f6", "COMISSAO": "#7c3aed"}
        icons = {"MANUAL": "✏️", "COMISSAO": "🤝"}
        origem = (getattr(obj, "origem", "") or "MANUAL").upper()
        return format_html(
            '<span style="color:{}; font-weight:bold;">{} {}</span>',
            colors.get(origem, "#6b7280"),
            icons.get(origem, "●"),
            origem.title(),
        )
    origem_colored.short_description = "🏷️ Origem"

    def has_comprovante(self, obj):
        comp = getattr(obj, "comprovante", None)
        return bool(comp and getattr(comp, "name", ""))
    has_comprovante.boolean = True
    has_comprovante.short_description = "📎"

    def data_cadastro(self, obj):
        # Tenta diferentes nomes comuns para data de criação
        for attr in ("criado_em", "data_criacao", "created_at"):
            if hasattr(obj, attr) and getattr(obj, attr):
                dt = getattr(obj, attr)
                try:
                    return dt.strftime("%d/%m/%Y %H:%M")
                except Exception:
                    return str(dt)
        return "-"
    data_cadastro.short_description = "📅 Cadastro"


# ==================== RECEITA EXTRA ====================

@admin.register(ReceitaExtra)
class ReceitaExtraAdmin(admin.ModelAdmin):
    list_display = ("data", "descricao_truncated", "valor_formatted", "has_comprovante", "data_cadastro")
    search_fields = ("descricao",)
    date_hierarchy = "data"
    ordering = ("-data",)
    list_per_page = 50

    fieldsets = (
        ("📋 Informações da Receita", {
            "fields": ("data", "descricao", "valor"),
            "classes": ("wide",),
        }),
        ("📎 Comprovante", {
            "fields": ("comprovante",),
            "classes": ("wide",),
            "description": "Anexe o comprovante da receita (PDF, imagem, etc.)",
        }),
    )

    readonly_fields = ("data_cadastro",)

    def descricao_truncated(self, obj):
        texto = getattr(obj, "descricao", "") or ""
        if len(texto) > 60:
            return format_html('<span title="{}">{}...</span>', texto, texto[:60])
        return texto
    descricao_truncated.short_description = "📝 Descrição"

    def valor_formatted(self, obj):
        return format_html(
            '<span style="font-weight:bold; font-size:1.05em;">{}</span>',
            _brl(getattr(obj, "valor", 0)),
        )
    valor_formatted.short_description = "💚 Valor"

    def has_comprovante(self, obj):
        comp = getattr(obj, "comprovante", None)
        return bool(comp and getattr(comp, "name", ""))
    has_comprovante.boolean = True
    has_comprovante.short_description = "📎"

    def data_cadastro(self, obj):
        for attr in ("criado_em", "data_criacao", "created_at"):
            if hasattr(obj, attr) and getattr(obj, attr):
                dt = getattr(obj, attr)
                try:
                    return dt.strftime("%d/%m/%Y %H:%M")
                except Exception:
                    return str(dt)
        return "-"
    data_cadastro.short_description = "📅 Cadastro"