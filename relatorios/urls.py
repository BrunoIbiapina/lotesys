# relatorios/urls.py
from django.urls import path
from .views import comissoes_pagas

app_name = "relatorios"

urlpatterns = [
    path("comissoes/", comissoes_pagas, name="comissoes_pagas"),
]