# financeiro/urls.py
from django.urls import path
from . import views

app_name = "financeiro"

urlpatterns = [
    path("ping/", views.ping, name="ping"),        # rota de teste
    path("extrato/", views.extrato, name="extrato")  # página do extrato
]