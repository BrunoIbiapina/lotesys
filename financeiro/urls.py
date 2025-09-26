# financeiro/urls.py
from django.urls import path
from . import views
from .debug_views import debug_media

app_name = "financeiro"

urlpatterns = [
    path("ping/", views.ping, name="ping"),
    path("extrato/", views.extrato, name="extrato"),
    path("extrato/pdf/", views.extrato_pdf, name="extrato_pdf"),
    path("relatorio-mensal/", views.relatorio_mensal_api, name="relatorio_mensal_api"),
    path("debug-media/", debug_media, name="debug_media"),
]