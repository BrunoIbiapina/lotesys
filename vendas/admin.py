# vendas/admin.py
from django.contrib import admin
from django.utils import timezone

from .models import Venda, Parcela
from .forms import VendaAdminForm
from .utils import gerar_parcelas_automaticas


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


class ParcelaInline(admin.TabularInline):
    model = Parcela
    extra = 0
    fields = ("numero", "valor", "vencimento", "status", "data_pagamento")
    readonly_fields = ()


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    form = VendaAdminForm

    list_display = (
        "id",
        "cliente",
        "lote",                # <-- ADICIONADO
        "valor_total",
        "entrada_bruta",
        "parcelas_total",
        "data_venda",
        "forma_pagamento",
    )
    search_fields = ("cliente__nome", "lote__numero", "lote__quadra")
    list_filter = ("data_venda", "forma_pagamento")
    inlines = [ParcelaInline]

    fieldsets = (
        ("Dados principais", {"fields": ("cliente", "lote", "data_venda")}),  # <-- ADICIONADO lote
        ("Valores", {"fields": ("valor_total", "entrada_bruta", "desconto", "comissao_percent")}),
        ("Parcelamento (geração automática)", {
            "fields": ("forma_pagamento", "parcelas_total", "juros_mensal", "data_inicio_parcelamento")
        }),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        gerar_parcelas_automaticas(obj, recriar=True)


@admin.register(Parcela)
class ParcelaAdmin(admin.ModelAdmin):
    list_display = ("venda", "numero", "valor", "vencimento", "status", "data_pagamento")
    list_filter = ("status", "vencimento", "data_pagamento")
    search_fields = ("venda__cliente__nome", "venda__id")
    actions = [marcar_pago, marcar_pendente, marcar_vencido]