from django.contrib import admin
from .models import Despesa, ReceitaExtra

@admin.register(Despesa)
class DespesaAdmin(admin.ModelAdmin):
    list_display = ('data','categoria','descricao','valor','status','origem')
    list_filter = ('categoria','status','origem')
    search_fields = ('descricao',)

@admin.register(ReceitaExtra)
class ReceitaExtraAdmin(admin.ModelAdmin):
    list_display = ('data','descricao','valor')
    search_fields = ('descricao',)