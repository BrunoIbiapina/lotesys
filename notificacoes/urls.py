# notificacoes/urls.py
from django.urls import path, re_path
from .views import task_notify, telegram_webhook

urlpatterns = [
    # Trigger HTTP para rodar o management command
    path("run/", task_notify, name="task_notify"),

    # Webhook do Telegram — aceita /telegram/<secret> e /telegram/<secret>/
    re_path(r"^telegram/(?P<secret>[^/]+)/?$", telegram_webhook, name="telegram_webhook"),
]