from django.contrib import admin
from .models import Mensagem

@admin.register(Mensagem)
class MensagemAdmin(admin.ModelAdmin):
    list_display = ("titulo", "tipo", "fixada", "criada_em", "autor")
    list_filter  = ("tipo", "fixada", "criada_em")
    search_fields = ("titulo", "conteudo", "autor__username", "autor__first_name", "autor__last_name")
    ordering = ("-fixada", "-criada_em")