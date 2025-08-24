from django.urls import path
from . import views
import os

WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "secret")

urlpatterns = [
    path("run/", views.task_notify, name="task_notify"),
    path(f"webhook/{WEBHOOK_SECRET}/", views.telegram_webhook, name="telegram_webhook"),
]