from django.urls import path
from .views import telegram_webhook, task_notify

urlpatterns = [
    path("<str:secret>/", telegram_webhook, name="telegram_webhook"),
    path("task-notify/", task_notify, name="task_notify"),  # opcional
]