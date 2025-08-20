# vendas/admin.py
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import Venda, Parcela
from .forms import VendaAdminForm
from .utils import gerar_parcelas_automaticas


# ===== Ações das parcelas =====
@admin.action(description="Marcar como PAGO (data hoje)")
def marcar_pago(modeladmin, request, queryset):
    hoje = timezone.now().date()
    for p in queryset:
        p.status = "PAGO"
        if not p.data_pagamento:
            p.data_pagamento = hoje
        p.save()


@admin.action(description="Marcar como PENDENTE")
def marcar_pendente(modeladmin, request, queryset):
    queryset.update(status="PENDENTE", data_pagamento=None)


@admin.action(description="Marcar como VENCIDO")
def marcar_vencido(modeladmin, request, queryset):
    queryset.update(status="VENCIDO", data_pagamento=None)


# ===== Inline de parcelas (agora com comprovante) =====
class ParcelaInline(admin.TabularInline):
    model = Parcela
    extra = 0
    fields = (
        "numero",
        "valor",
        "vencimento",
        "status",
        "data_pagamento",
        "comprovante",          # ⬅ upload direto na parcela
        "link_comprovante",     # ⬅ link pra visualizar
    )
    readonly_fields = ("link_comprovante",)

    @admin.display(description="Comprovante (ver)")
    def link_comprovante(self, obj: Parcela):
        if obj and obj.comprovante:
            return format_html('<a href="{}" target="_blank">ver/baixar</a>', obj.comprovante.url)
        return "—"


# ===== Venda =====
@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    form = VendaAdminForm

    list_display = (
        "id",
        "cliente",
        "lote",
        "valor_total",
        "entrada_bruta",
        "parcelas_total",
        "data_venda",
        "forma_pagamento",
        "tem_comprovante_bool",   # ⬅ indicador
        "link_comprovante",       # ⬅ atalho
    )
    search_fields = ("cliente__nome", "lote__numero", "lote__quadra")
    list_filter = ("data_venda", "forma_pagamento")
    inlines = [ParcelaInline]

    fieldsets = (
        ("Dados principais", {
            "fields": ("cliente", "lote", "data_venda")
        }),
        ("Valores", {
            "fields": ("valor_total", "entrada_bruta", "desconto", "comissao_percent")
        }),
        ("Parcelamento (geração automática)", {
            "fields": ("forma_pagamento", "parcelas_total", "juros_mensal", "data_inicio_parcelamento")
        }),
        ("Comprovante", {
            "fields": ("comprovante", "link_comprovante")
        }),
    )
    readonly_fields = ("link_comprovante",)

    @admin.display(boolean=True, description="Tem comp.")
    def tem_comprovante_bool(self, obj: Venda):
        return bool(obj.comprovante)

    @admin.display(description="Comprovante (ver)")
    def link_comprovante(self, obj: Venda):
        if obj.comprovante:
            return format_html('<a href="{}" target="_blank">ver/baixar</a>', obj.comprovante.url)
        return "—"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # mantém seu comportamento: recria as parcelas conforme regras
        gerar_parcelas_automaticas(obj, recriar=True)


# ===== Parcela =====
@admin.register(Parcela)
class ParcelaAdmin(admin.ModelAdmin):
    list_display = (
        "venda",
        "numero",
        "valor",
        "vencimento",
        "status",
        "data_pagamento",
        "tem_comprovante_bool",   # ⬅ indicador
        "link_comprovante",       # ⬅ atalho
    )
    list_filter = ("status", "vencimento", "data_pagamento")
    search_fields = ("venda__cliente__nome", "venda__id")
    actions = [marcar_pago, marcar_pendente, marcar_vencido]
    readonly_fields = ("link_comprovante",)

    @admin.display(boolean=True, description="Tem comp.")
    def tem_comprovante_bool(self, obj: Parcela):
        return bool(obj.comprovante)

    @admin.display(description="Comprovante (ver)")
    def link_comprovante(self, obj: Parcela):
        if obj.comprovante:
            return format_html('<a href="{}" target="_blank">ver/baixar</a>', obj.comprovante.url)
        return "—"