from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Categoria, Pergunta


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'preview_cor', 'preview_icone', 'ativo', 'total_perguntas', 'criado_em']
    list_filter = ['ativo', 'criado_em']
    search_fields = ['nome', 'descricao']
    list_editable = ['ativo']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'descricao', 'ativo')
        }),
        ('Aparência', {
            'fields': ('cor', 'icone'),
            'description': 'Configure a aparência visual da categoria'
        }),
    )
    
    def preview_cor(self, obj):
        return format_html(
            '<span style="display: inline-block; width: 20px; height: 20px; '
            'background-color: {}; border: 1px solid #ccc; border-radius: 3px;"></span>',
            obj.cor
        )
    preview_cor.short_description = 'Cor'
    
    def preview_icone(self, obj):
        return format_html('<i class="{}" style="font-size: 18px;"></i>', obj.icone)
    preview_icone.short_description = 'Ícone'
    
    def total_perguntas(self, obj):
        return obj.pergunta_set.count()
    total_perguntas.short_description = 'Total de Perguntas'


@admin.register(Pergunta)
class PerguntaAdmin(admin.ModelAdmin):
    list_display = [
        'titulo', 'usuario', 'categoria', 'status', 
        'publica', 'tem_resposta', 'criado_em'
    ]
    list_filter = ['status', 'categoria', 'publica', 'criado_em', 'respondido_em']
    search_fields = ['titulo', 'pergunta', 'resposta', 'usuario__first_name', 'usuario__username']
    list_editable = ['status', 'publica']
    readonly_fields = ['criado_em', 'atualizado_em', 'respondido_em']
    
    fieldsets = (
        ('Pergunta', {
            'fields': ('titulo', 'pergunta', 'categoria', 'usuario', 'publica')
        }),
        ('Resposta', {
            'fields': ('resposta', 'respondido_por'),
            'description': 'Adicione uma resposta para marcar como respondida automaticamente'
        }),
        ('Status e Controle', {
            'fields': ('status',),
        }),
        ('Informações do Sistema', {
            'fields': ('criado_em', 'atualizado_em', 'respondido_em'),
            'classes': ('collapse',)
        }),
    )
    
    def tem_resposta(self, obj):
        if obj.resposta:
            return format_html('<i class="fas fa-check-circle" style="color: green;"></i>')
        return format_html('<i class="fas fa-times-circle" style="color: red;"></i>')
    tem_resposta.short_description = 'Respondida'
    
    def save_model(self, request, obj, form, change):
        # Se uma resposta foi adicionada e não há respondente, definir o usuário atual
        if obj.resposta and not obj.respondido_por:
            obj.respondido_por = request.user
            if not obj.respondido_em:
                obj.respondido_em = timezone.now()
        super().save_model(request, obj, form, change)
    
    actions = ['marcar_como_respondida', 'marcar_como_publica', 'marcar_como_privada']
    
    def marcar_como_respondida(self, request, queryset):
        count = queryset.update(status='respondida')
        self.message_user(request, f'{count} perguntas marcadas como respondidas.')
    marcar_como_respondida.short_description = "Marcar como respondida"
    
    def marcar_como_publica(self, request, queryset):
        count = queryset.update(publica=True)
        self.message_user(request, f'{count} perguntas marcadas como públicas.')
    marcar_como_publica.short_description = "Marcar como pública"
    
    def marcar_como_privada(self, request, queryset):
        count = queryset.update(publica=False)
        self.message_user(request, f'{count} perguntas marcadas como privadas.')
    marcar_como_privada.short_description = "Marcar como privada"
