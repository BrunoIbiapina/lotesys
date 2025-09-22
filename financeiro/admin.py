from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Despesa, ReceitaExtra

@admin.register(Despesa)
class DespesaAdmin(admin.ModelAdmin):
    list_display = ('data', 'categoria', 'descricao_truncated', 'valor_formatted', 'status_colored', 'origem_colored')
    list_filter = ('categoria', 'status', 'origem', 'data')
    search_fields = ('descricao', 'valor')
    date_hierarchy = 'data'
    ordering = ('-data',)
    list_per_page = 50
    
    fieldsets = (
        ('📋 Informações Básicas', {
            'fields': ('data', 'categoria', 'descricao'),
            'classes': ('wide',)
        }),
        ('💰 Valores', {
            'fields': ('valor', 'status'),
            'classes': ('wide',)
        }),
        ('🔄 Sistema', {
            'fields': ('origem',),
            'classes': ('collapse',)
        })
    )
    
    def descricao_truncated(self, obj):
        if len(obj.descricao) > 50:
            return format_html(
                '<span title="{}">{}</span>',
                obj.descricao,
                obj.descricao[:50] + '...'
            )
        return obj.descricao
    descricao_truncated.short_description = '📝 Descrição'
    
    def valor_formatted(self, obj):
        return format_html(
            '<span style="font-weight: bold; color: #ef4444; font-size: 1.1em;">R$ {}</span>',
            f"{obj.valor:,.2f}"
        )
    valor_formatted.short_description = '💸 Valor'
    
    def status_colored(self, obj):
        colors = {
            'PAGO': '#10b981',
            'PENDENTE': '#f59e0b',
            'CANCELADO': '#6b7280'
        }
        icons = {
            'PAGO': '✅',
            'PENDENTE': '⏱️', 
            'CANCELADO': '❌'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            colors.get(obj.status, '#6b7280'),
            icons.get(obj.status, '●'),
            obj.get_status_display()
        )
    status_colored.short_description = '📊 Status'
    
    def origem_colored(self, obj):
        colors = {
            'MANUAL': '#3b82f6',
            'COMISSAO': '#7c3aed'
        }
        icons = {
            'MANUAL': '✏️',
            'COMISSAO': '🤝'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            colors.get(obj.origem, '#6b7280'),
            icons.get(obj.origem, '●'),
            obj.origem or 'Manual'
        )
    origem_colored.short_description = '🏷️ Origem'

@admin.register(ReceitaExtra)
class ReceitaExtraAdmin(admin.ModelAdmin):
    list_display = ('data', 'descricao_truncated', 'valor_formatted', 'data_cadastro')
    search_fields = ('descricao',)
    date_hierarchy = 'data'
    ordering = ('-data',)
    list_per_page = 50
    
    fieldsets = (
        ('📋 Informações da Receita', {
            'fields': ('data', 'descricao', 'valor'),
            'classes': ('wide',)
        }),
    )
    
    readonly_fields = ('data_cadastro',)
    
    def descricao_truncated(self, obj):
        if len(obj.descricao) > 60:
            return format_html(
                '<span title="{}">{}</span>',
                obj.descricao,
                obj.descricao[:60] + '...'
            )
        return obj.descricao
    descricao_truncated.short_description = '📝 Descrição'
    
    def valor_formatted(self, obj):
        return format_html(
            '<span style="font-weight: bold; color: #10b981; font-size: 1.1em;">R$ {}</span>',
            f"{obj.valor:,.2f}"
        )
    valor_formatted.short_description = '💚 Valor'
    
    def data_cadastro(self, obj):
        if hasattr(obj, 'data_criacao'):
            return obj.data_criacao.strftime('%d/%m/%Y %H:%M')
        return '-'
    data_cadastro.short_description = '📅 Cadastro'