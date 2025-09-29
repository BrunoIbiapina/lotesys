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
    
    class Media:
        css = {
            'all': ('admin/css/custom.css',)
        }
    list_display = [
        'id', 'titulo_curto', 'nome_usuario', 'categoria', 'status', 
        'publica', 'tem_resposta', 'criado_em'
    ]
    list_filter = ['status', 'categoria', 'publica', 'criado_em', 'respondido_em']
    search_fields = ['titulo', 'pergunta', 'resposta', 'usuario__first_name', 'usuario__username', 'usuario__email']
    list_editable = ['status', 'publica']
    readonly_fields = ['criado_em', 'atualizado_em', 'respondido_em']
    ordering = ['-criado_em']
    list_per_page = 25
    
    fieldsets = (
        ('📝 Pergunta', {
            'fields': ('titulo', 'pergunta', 'categoria', 'usuario', 'publica'),
            'description': 'Informações da pergunta enviada pelo usuário'
        }),
        ('💬 Resposta', {
            'fields': ('resposta', 'respondido_por', 'status'),
            'description': 'Adicione uma resposta completa e marque o status como "Respondida"'
        }),
        ('📊 Informações do Sistema', {
            'fields': ('criado_em', 'atualizado_em', 'respondido_em'),
            'classes': ('collapse',)
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        """Personaliza o formulário do admin"""
        form = super().get_form(request, obj, **kwargs)
        
        # Melhora o widget da resposta
        if 'resposta' in form.base_fields:
            form.base_fields['resposta'].widget.attrs.update({
                'rows': 8,
                'placeholder': 'Digite aqui a resposta completa para a pergunta...'
            })
        
        # Melhora o widget da pergunta (readonly mas mais legível)
        if 'pergunta' in form.base_fields:
            form.base_fields['pergunta'].widget.attrs.update({
                'rows': 4,
                'readonly': True
            })
            
        return form
    
    def titulo_curto(self, obj):
        """Mostra o título truncado com tooltip completo"""
        if len(obj.titulo) > 50:
            return format_html(
                '<span title="{}">{}..</span>',
                obj.titulo,
                obj.titulo[:47]
            )
        return obj.titulo
    titulo_curto.short_description = 'Título'
    
    def nome_usuario(self, obj):
        """Mostra nome completo ou username do usuário"""
        nome = obj.usuario.get_full_name()
        if nome:
            return format_html('<strong>{}</strong><br><small>{}</small>', nome, obj.usuario.username)
        return obj.usuario.username
    nome_usuario.short_description = 'Usuário'
    
    def tem_resposta(self, obj):
        if obj.resposta and obj.resposta.strip():
            return format_html(
                '<span style="color: green; font-weight: bold;">✅ Sim</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">❌ Não</span>'
        )
    tem_resposta.short_description = 'Tem Resposta'
    
    def save_model(self, request, obj, form, change):
        # Lógica automática para resposta
        if obj.resposta and obj.resposta.strip():
            # Se há resposta, marcar como respondida automaticamente
            obj.status = 'respondida'
            
            # Se não há respondente, definir o usuário atual
            if not obj.respondido_por:
                obj.respondido_por = request.user
                
            # Se não há data de resposta, definir agora
            if not obj.respondido_em:
                obj.respondido_em = timezone.now()
        else:
            # Se não há resposta, não pode estar respondida
            if obj.status == 'respondida':
                obj.status = 'pendente'
            obj.respondido_por = None
            obj.respondido_em = None
            
        super().save_model(request, obj, form, change)
    
    actions = [
        'marcar_como_pendente', 
        'marcar_como_respondida', 
        'marcar_como_arquivada',
        'marcar_como_publica', 
        'marcar_como_privada'
    ]
    
    def marcar_como_pendente(self, request, queryset):
        count = queryset.update(status='pendente')
        self.message_user(request, f'✅ {count} perguntas marcadas como pendentes.')
    marcar_como_pendente.short_description = "🔄 Marcar como pendente"
    
    def marcar_como_respondida(self, request, queryset):
        # Só marca como respondida se tiver resposta
        count = 0
        for pergunta in queryset:
            if pergunta.resposta and pergunta.resposta.strip():
                pergunta.status = 'respondida'
                if not pergunta.respondido_por:
                    pergunta.respondido_por = request.user
                if not pergunta.respondido_em:
                    pergunta.respondido_em = timezone.now()
                pergunta.save()
                count += 1
        
        if count > 0:
            self.message_user(request, f'✅ {count} perguntas marcadas como respondidas.')
        else:
            self.message_user(request, '⚠️ Nenhuma pergunta foi marcada (precisam ter resposta).', level='warning')
    marcar_como_respondida.short_description = "✅ Marcar como respondida (só com resposta)"
    
    def marcar_como_arquivada(self, request, queryset):
        count = queryset.update(status='arquivada')
        self.message_user(request, f'📦 {count} perguntas arquivadas.')
    marcar_como_arquivada.short_description = "📦 Arquivar perguntas"
    
    def marcar_como_publica(self, request, queryset):
        count = queryset.update(publica=True)
        self.message_user(request, f'🌐 {count} perguntas marcadas como públicas.')
    marcar_como_publica.short_description = "🌐 Tornar públicas"
    
    def marcar_como_privada(self, request, queryset):
        count = queryset.update(publica=False)
        self.message_user(request, f'🔒 {count} perguntas marcadas como privadas.')
    marcar_como_privada.short_description = "🔒 Tornar privadas"
