from django.contrib import admin
from .models import DestinatarioTelegram

@admin.register(DestinatarioTelegram)
class DestinatarioTelegramAdmin(admin.ModelAdmin):
    list_display = ("nome", "chat_id", "ativo", "recebe_vencimentos_hoje", "recebe_atrasados")
    search_fields = ("nome", "chat_id")
    list_filter = ("ativo", "recebe_vencimentos_hoje", "recebe_atrasados")