# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    # Dashboard (página inicial)
    path("", include("dashboard.urls")),

    # Financeiro
    path("financeiro/", include(("financeiro.urls", "financeiro"), namespace="financeiro")),

    # Usuários (login/logout)
    path("usuarios/", include(("usuarios.urls", "usuarios"), namespace="usuarios")),

    # Vendas
    path("vendas/", include(("vendas.urls", "vendas"), namespace="vendas")),
]

# Arquivos enviados (apenas em desenvolvimento com DEBUG=True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)