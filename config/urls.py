# config/urls.py
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as media_serve
import os

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", include("dashboard.urls")),
    path("financeiro/", include(("financeiro.urls", "financeiro"), namespace="financeiro")),
    path("usuarios/", include(("usuarios.urls", "usuarios"), namespace="usuarios")),
    path("vendas/", include(("vendas.urls", "vendas"), namespace="vendas")),
    path("mural/", include(("mural.urls", "mural"), namespace="mural")),

    # <<< SEMPRE HABILITADO >>>
    path("notificacoes/", include(("notificacoes.urls", "notificacoes"), namespace="notificacoes")),
]

# Dev: servir /media/
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Render: “quebra-galho” de /media/
if os.getenv("SERVE_MEDIA", "False") == "True":
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", media_serve, {"document_root": settings.MEDIA_ROOT}),
    ]