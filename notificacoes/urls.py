# notificacoes/urls.py
from django.urls import path
from . import views

app_name = "notificacoes"

urlpatterns = [
    # Webhook do Telegram (se usar)
    path("webhook/<str:secret>/", views.telegram_webhook, name="telegram_webhook"),

    # Runner HTTP dos avisos (trigger por cron externo/Render)
    path("run/", views.task_notify, name="task_notify"),
]