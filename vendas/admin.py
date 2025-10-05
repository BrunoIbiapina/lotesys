# vendas/admin.py
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, Count

from .models import Venda, Parcela
from .forms import VendaAdminForm
from .utils import gerar_parcelas_automaticas


# ===== Ações das parcelas =====
@admin.action(description="✅ Marcar como PAGO (data hoje)")
def marcar_pago(modeladmin, request, queryset):
    hoje = timezone.now().date()
    count = 0
    for p in queryset:
        p.status = "PAGO"
        if not p.data_pagamento:
            p.data_pagamento = hoje
        p.save()
        count += 1
    
    modeladmin.message_user(request, f"{count} parcela(s) marcada(s) como PAGO.")

@admin.action(description="⏱️ Marcar como PENDENTE")
def marcar_pendente(modeladmin, request, queryset):
    count = queryset.update(status="PENDENTE", data_pagamento=None)
    modeladmin.message_user(request, f"{count} parcela(s) marcada(s) como PENDENTE.")

@admin.action(description="⚠️ Marcar como VENCIDO")
def marcar_vencido(modeladmin, request, queryset):
    count = queryset.update(status="VENCIDO", data_pagamento=None)
    modeladmin.message_user(request, f"{count} parcela(s) marcada(s) como VENCIDO.")


# ===== Inline de parcelas melhorado =====
class ParcelaInline(admin.TabularInline):
    model = Parcela
    extra = 0
    classes = ['collapse']
    
    fields = (
        "numero",
        "valor_formatted",
        "vencimento",
        "status_colored",
        "data_pagamento",
        "comprovante",
        "link_comprovante",
    )
    readonly_fields = ("valor_formatted", "status_colored", "link_comprovante")

    def valor_formatted(self, obj):
        if obj.valor:
            return format_html(
                '<span style="font-weight: bold; color: #059669;">R$ {}</span>',
                f"{obj.valor:,.2f}"
            )
        return '-'
    valor_formatted.short_description = '💰 Valor'

    def status_colored(self, obj):
        colors = {
            'PAGO': '#10b981',
            'PENDENTE': '#f59e0b', 
            'VENCIDO': '#ef4444'
        }
        icons = {
            'PAGO': '✅',
            'PENDENTE': '⏱️',
            'VENCIDO': '⚠️'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            colors.get(obj.status, '#6b7280'),
            icons.get(obj.status, '●'),
            obj.get_status_display()
        )
    status_colored.short_description = '📊 Status'

    def link_comprovante(self, obj):
        if obj and obj.comprovante:
            return format_html(
                '<a href="{}" target="_blank" style="color: #3b82f6; text-decoration: none;">📄 Ver</a>', 
                obj.comprovante.url
            )
        return "—"
    link_comprovante.short_description = "📎 Arquivo"


# ===== Venda Admin Melhorado =====
@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    form = VendaAdminForm

    list_display = (
        "id_link",
        "cliente_link", 
        "lote_info",
        "valor_total_formatted",
        "parcelas_info",
        "data_venda",
        "status_venda",
    )
    
    list_display_links = None  # Remove links automáticos
    search_fields = ("cliente__nome", "lote__numero", "lote__quadra", "id")
    list_filter = ("data_venda", "forma_pagamento", "lote__empreendimento")
    date_hierarchy = 'data_venda'
    ordering = ('-data_venda',)
    list_per_page = 25
    
    inlines = [ParcelaInline]

    fieldsets = (
        ("📋 Dados Principais", {
            "fields": ("cliente", "lote", "data_venda"),
            "classes": ("wide",)
        }),
        ("💰 Valores Financeiros", {
            "fields": ("valor_total", "entrada_bruta", "desconto", "comissao_percent"),
            "classes": ("wide",)
        }),
        ("📅 Parcelamento", {
            "fields": ("forma_pagamento", "parcelas_total", "juros_mensal", "data_inicio_parcelamento"),
            "description": "Configure o parcelamento. As parcelas serão geradas automaticamente.",
            "classes": ("wide",)
        }),
        ("📎 Documentos", {
            "fields": ("comprovante", "link_comprovante_edit"),
            "classes": ("collapse",)
        }),
    )
    readonly_fields = ("link_comprovante_edit",)

    def id_link(self, obj):
        url = reverse('admin:vendas_venda_change', args=[obj.id])
        return format_html(
            '<a href="{}" style="color: #3b82f6; font-weight: bold; text-decoration: none;">#{}</a>',
            url, obj.id
        )
    id_link.short_description = '🆔 ID'

    def cliente_link(self, obj):
        url = reverse('admin:cadastros_cliente_change', args=[obj.cliente.id])
        return format_html(
            '<a href="{}" style="color: #059669; text-decoration: none; font-weight: 500;">{}</a>',
            url, obj.cliente.nome
        )
    cliente_link.short_description = '👤 Cliente'

    def lote_info(self, obj):
        url = reverse('admin:cadastros_lote_change', args=[obj.lote.id])
        return format_html(
            '<a href="{}" style="color: #7c3aed; text-decoration: none;">🏠 Q{} - L{}<br><small style="color: #6b7280;">{}</small></a>',
            url, obj.lote.quadra, obj.lote.numero, obj.lote.empreendimento.nome
        )
    lote_info.short_description = '🏘️ Lote'

    def valor_total_formatted(self, obj):
        return format_html(
            '<span style="font-weight: bold; color: #059669; font-size: 1.1em;">R$ {}</span>',
            f"{obj.valor_total:,.2f}"
        )
    valor_total_formatted.short_description = '💵 Valor Total'

    def entrada_liquida_formatted(self, obj):
        return format_html(
            '<span style="font-weight: bold; color: #3b82f6;">R$ {}</span>',
            f"{obj.entrada_liquida:,.2f}"
        )
    entrada_liquida_formatted.short_description = '💰 Entrada Líq.'

    def parcelas_info(self, obj):
        parcelas = obj.parcelas.all()
        pagas = parcelas.filter(status='PAGO').count()
        total = parcelas.count()
        
        if total > 0:
            percentage = (pagas / total) * 100
            color = '#10b981' if percentage == 100 else '#f59e0b' if percentage > 0 else '#ef4444'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}/{}<br><small>({}%)</small></span>',
                color, pagas, total, round(percentage, 1)
            )
        return format_html('<span style="color: #6b7280;">À vista</span>')
    parcelas_info.short_description = '📊 Parcelas'

    def status_venda(self, obj):
        parcelas = obj.parcelas.all()
        if not parcelas.exists():
            return format_html('<span style="color: #10b981; font-weight: bold;">✅ À Vista</span>')
        
        todas_pagas = all(p.status == 'PAGO' for p in parcelas)
        tem_vencida = any(p.status == 'VENCIDO' for p in parcelas)
        
        if todas_pagas:
            return format_html('<span style="color: #10b981; font-weight: bold;">✅ Quitado</span>')
        elif tem_vencida:
            return format_html('<span style="color: #ef4444; font-weight: bold;">⚠️ Em Atraso</span>')
        else:
            return format_html('<span style="color: #f59e0b; font-weight: bold;">⏱️ Em Andamento</span>')
    status_venda.short_description = '🎯 Status'

    def tem_comprovante_bool(self, obj):
        return bool(obj.comprovante)
    tem_comprovante_bool.boolean = True
    tem_comprovante_bool.short_description = "📄 Comp."

    def link_comprovante_edit(self, obj):
        if obj.comprovante:
            return format_html(
                '<a href="{}" target="_blank" style="color: #3b82f6; text-decoration: none;">📄 Visualizar Comprovante</a>', 
                obj.comprovante.url
            )
        return "Nenhum arquivo enviado"
    link_comprovante_edit.short_description = "📎 Arquivo Atual"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        gerar_parcelas_automaticas(obj, recriar=True)
        
        if change:
            self.message_user(request, f"Venda #{obj.id} atualizada e parcelas regeneradas com sucesso!")
        else:
            self.message_user(request, f"Venda #{obj.id} criada com sucesso! Parcelas geradas automaticamente.")


# ===== Parcela Admin Melhorado =====
@admin.register(Parcela)
class ParcelaAdmin(admin.ModelAdmin):
    list_display = (
        "venda_link",
        "parcela_info", 
        "valor_formatted",
        "vencimento",
        "status_colored",
        "data_pagamento",
        "atraso_dias",
        "tem_comprovante_bool",
    )
    
    list_filter = ("status", "vencimento", "data_pagamento", "venda__lote__empreendimento")
    search_fields = ("venda__cliente__nome", "venda__id", "numero")
    date_hierarchy = 'vencimento'
    ordering = ('-vencimento',)
    actions = [marcar_pago, marcar_pendente, marcar_vencido]
    list_per_page = 50
    
    fieldsets = (
        ("📋 Informações da Parcela", {
            "fields": ("venda", "numero", "valor", "vencimento"),
            "classes": ("wide",)
        }),
        ("💳 Pagamento", {
            "fields": ("status", "data_pagamento"),
            "classes": ("wide",)
        }),
        ("📎 Comprovante", {
            "fields": ("comprovante", "link_comprovante_edit"),
            "classes": ("collapse",)
        }),
    )
    readonly_fields = ("link_comprovante_edit",)

    def venda_link(self, obj):
        url = reverse('admin:vendas_venda_change', args=[obj.venda.id])
        return format_html(
            '<a href="{}" style="color: #3b82f6; font-weight: bold; text-decoration: none;">Venda #{}<br><small style="color: #6b7280;">{}</small></a>',
            url, obj.venda.id, obj.venda.cliente.nome
        )
    venda_link.short_description = '🔗 Venda'

    def parcela_info(self, obj):
        return format_html(
            '<span style="font-weight: bold; color: #7c3aed;">Parcela {}/{}</span>',
            obj.numero, obj.venda.parcelas_total
        )
    parcela_info.short_description = '📄 Parcela'

    def valor_formatted(self, obj):
        return format_html(
            '<span style="font-weight: bold; color: #059669; font-size: 1.1em;">R$ {}</span>',
            f"{obj.valor:,.2f}"
        )
    valor_formatted.short_description = '💰 Valor'

    def status_colored(self, obj):
        colors = {
            'PAGO': '#10b981',
            'PENDENTE': '#f59e0b', 
            'VENCIDO': '#ef4444'
        }
        icons = {
            'PAGO': '✅',
            'PENDENTE': '⏱️',
            'VENCIDO': '⚠️'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            colors.get(obj.status, '#6b7280'),
            icons.get(obj.status, '●'),
            obj.get_status_display()
        )
    status_colored.short_description = '📊 Status'

    def atraso_dias(self, obj):
        if obj.status != 'PAGO' and obj.vencimento:
            hoje = timezone.now().date()
            if obj.vencimento < hoje:
                dias = (hoje - obj.vencimento).days
                return format_html(
                    '<span style="color: #ef4444; font-weight: bold;">{} dias</span>',
                    dias
                )
        return '-'
    atraso_dias.short_description = '⏰ Atraso'

    def tem_comprovante_bool(self, obj):
        return bool(obj.comprovante)
    tem_comprovante_bool.boolean = True
    tem_comprovante_bool.short_description = "📄 Comp."

    def link_comprovante_edit(self, obj):
        if obj.comprovante:
            return format_html(
                '<a href="{}" target="_blank" style="color: #3b82f6; text-decoration: none;">📄 Visualizar Comprovante</a>', 
                obj.comprovante.url
            )
        return "Nenhum arquivo enviado"
    link_comprovante_edit.short_description = "📎 Arquivo Atual"