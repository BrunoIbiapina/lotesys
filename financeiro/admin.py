from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Despesa, ReceitaExtra

@admin.register(Despesa)
class DespesaAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'categoria', 
        'descricao', 
        'valor_formatted',
        'has_comprovante',
        'data',
        'status_colored',
        'criado_em'
    ]
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
        ('� Comprovante', {
            'fields': ('comprovante',),
            'classes': ('wide',),
            'description': 'Anexe o comprovante da despesa (PDF, imagem, etc.)'
        }),
        ('�🔄 Sistema', {
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
            'PREVISTA': '#f59e0b',  # amarelo
            'PAGA': '#10b981',      # verde
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_colored.short_description = '🎯 Status'
    
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
    
    def has_comprovante(self, obj):
        """Indicador simples se tem comprovante"""
        return obj.comprovante and obj.comprovante.name
    has_comprovante.boolean = True
    has_comprovante.short_description = '📎'

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
        ('📎 Comprovante', {
            'fields': ('comprovante',),
            'classes': ('wide',),
            'description': 'Anexe o comprovante da receita (PDF, imagem, etc.)'
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
    
    def has_comprovante(self, obj):
        """Indicador simples se tem comprovante"""
        return obj.comprovante and obj.comprovante.name
    has_comprovante.boolean = True
    has_comprovante.short_description = '📎'
    
    def data_cadastro(self, obj):
        if hasattr(obj, 'data_criacao'):
            return obj.data_criacao.strftime('%d/%m/%Y %H:%M')
        return '-'
    data_cadastro.short_description = '📅 Cadastro'