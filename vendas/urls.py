# vendas/urls.py
from django.urls import path
from . import views

app_name = "vendas"

urlpatterns = [
    path("", views.vendas_list, name="vendas_list"),
    path("<int:pk>/", views.venda_detail, name="venda_detail"),

    # ações de parcelas (POST, restritas a staff)
    path("parcelas/<int:pk>/pagar/", views.parcela_pagar, name="parcela_pagar"),
    path("parcelas/<int:pk>/desfazer/", views.parcela_desfazer, name="parcela_desfazer"),
]