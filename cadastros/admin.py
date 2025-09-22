from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Empreendimento, Cliente, Lote

@admin.register(Empreendimento)
class EmpreendimentoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cidade', 'estado', 'total_lotes', 'vendidos')
    list_filter = ('estado', 'cidade')
    search_fields = ('nome', 'cidade', 'estado')
    ordering = ('nome',)
    
    def total_lotes(self, obj):
        return obj.lote_set.count()
    total_lotes.short_description = '🏘️ Total Lotes'
    
    def vendidos(self, obj):
        vendidos = obj.lote_set.filter(status='VENDIDO').count()
        total = obj.lote_set.count()
        if total > 0:
            percentage = (vendidos / total) * 100
            color = 'green' if percentage > 70 else 'orange' if percentage > 30 else 'red'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}/{} ({}%)</span>',
                color, vendidos, total, round(percentage, 1)
            )
        return '0/0'
    vendidos.short_description = '🎯 Vendidos'

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf_cnpj_masked', 'telefone', 'email', 'total_compras')
    search_fields = ('nome', 'cpf_cnpj', 'telefone', 'email')
    ordering = ('nome',)
    
    fieldsets = (
        ('Informações Pessoais', {
            'fields': ('nome', 'cpf_cnpj')
        }),
        ('Contato', {
            'fields': ('telefone', 'email')
        }),
        ('Endereço', {
            'fields': ('endereco',),
            'classes': ('collapse',)
        })
    )
    
    def cpf_cnpj_masked(self, obj):
        if obj.cpf_cnpj:
            if len(obj.cpf_cnpj) == 11:  # CPF
                return f"{obj.cpf_cnpj[:3]}.{obj.cpf_cnpj[3:6]}.{obj.cpf_cnpj[6:9]}-{obj.cpf_cnpj[9:]}"
            elif len(obj.cpf_cnpj) == 14:  # CNPJ
                return f"{obj.cpf_cnpj[:2]}.{obj.cpf_cnpj[2:5]}.{obj.cpf_cnpj[5:8]}/{obj.cpf_cnpj[8:12]}-{obj.cpf_cnpj[12:]}"
        return obj.cpf_cnpj
    cpf_cnpj_masked.short_description = '📄 CPF/CNPJ'
    
    def total_compras(self, obj):
        try:
            from vendas.models import Venda
            vendas = Venda.objects.filter(cliente=obj)
            total = vendas.count()
            if total > 0:
                valor_total = sum(v.valor_total for v in vendas if v.valor_total)
                return format_html(
                    '<span style="color: green; font-weight: bold;">{} vendas<br>R$ {}</span>',
                    total, f"{valor_total:,.2f}"
                )
            return 'Nenhuma'
        except Exception as e:
            return f'Erro: {str(e)}'
    total_compras.short_description = '🛒 Compras'

@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ('identificacao', 'empreendimento', 'area_m2', 'preco_tabela_formatted', 'status_colored', 'tem_venda')
    list_filter = ('empreendimento', 'status', 'quadra')
    search_fields = ('quadra', 'numero', 'empreendimento__nome')
    ordering = ('empreendimento', 'quadra', 'numero')
    list_per_page = 50
    
    fieldsets = (
        ('Identificação', {
            'fields': ('empreendimento', 'quadra', 'numero')
        }),
        ('Características', {
            'fields': ('area_m2', 'preco_tabela', 'observacoes')
        }),
        ('Status', {
            'fields': ('status',)
        })
    )
    
    def identificacao(self, obj):
        return f"Q{obj.quadra} - L{obj.numero}"
    identificacao.short_description = '🏠 Lote'
    
    def preco_tabela_formatted(self, obj):
        if obj.preco_tabela:
            return format_html(
                '<span style="font-weight: bold; color: #059669;">R$ {}</span>',
                f"{obj.preco_tabela:,.2f}"
            )
        return '-'
    preco_tabela_formatted.short_description = '💰 Preço'
    
    def status_colored(self, obj):
        colors = {
            'DISP': '#10b981',  # green
            'RESV': '#f59e0b',   # yellow
            'VEND': '#3b82f6',     # blue
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            colors.get(obj.status, '#6b7280'),
            obj.get_status_display()
        )
    status_colored.short_description = '📊 Status'
    
    def tem_venda(self, obj):
        from vendas.models import Venda
        venda = Venda.objects.filter(lote=obj).first()
        if venda:
            url = reverse('admin:vendas_venda_change', args=[venda.id])
            return format_html(
                '<a href="{}" style="color: #3b82f6; text-decoration: none;">✓ Ver Venda</a>',
                url
            )
        return '-'
    tem_venda.short_description = '🔗 Venda'
    
    def get_queryset(self, request):
        # Otimizar consultas para melhor performance
        return super().get_queryset(request).select_related('empreendimento')