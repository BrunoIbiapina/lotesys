# config/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("dashboard.urls")),
    path("financeiro/", include("financeiro.urls")),
    path("usuarios/", include(("usuarios.urls", "usuarios"), namespace="usuarios")),  # <- assim
    path("vendas/", include(("vendas.urls", "vendas"), namespace="vendas")),
]