# config/urls.py
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as media_serve
import os

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

# Desenvolvimento: serve /media/ via Django
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Produção (Render): habilitar via env SERVE_MEDIA=True para servir /media/ pelo Django
# OBS: é quebra-galho; ideal no longo prazo é usar S3/django-storages.
if os.getenv("SERVE_MEDIA", "False") == "True":
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", media_serve, {"document_root": settings.MEDIA_ROOT}),
    ]