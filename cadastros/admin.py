from django.contrib import admin
from .models import Empreendimento, Cliente, Lote

@admin.register(Empreendimento)
class EmpreendimentoAdmin(admin.ModelAdmin):
    list_display = ('nome','cidade','estado')
    search_fields = ('nome','cidade')

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome','cpf_cnpj','telefone','email')
    search_fields = ('nome','cpf_cnpj')

@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ('empreendimento','quadra','numero','area_m2','preco_tabela','status')
    list_filter = ('empreendimento','status')
    search_fields = ('quadra','numero')