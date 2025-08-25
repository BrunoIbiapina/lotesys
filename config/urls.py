from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as media_serve
import os

from notificacoes.views import telegram_webhook

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", include("dashboard.urls")),
    path("financeiro/", include(("financeiro.urls", "financeiro"), namespace="financeiro")),
    path("usuarios/", include(("usuarios.urls", "usuarios"), namespace="usuarios")),
    path("vendas/", include(("vendas.urls", "vendas"), namespace="vendas")),
    path("mural/", include(("mural.urls", "mural"), namespace="mural")),
    path("relatorios/", include(("relatorios.urls", "relatorios"), namespace="relatorios")),
    path("telegram/<str:secret>/", telegram_webhook, name="telegram_webhook"),
    # <<< SEM CONDICIONAL >>>
   path("notificacoes/", include("notificacoes.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if os.getenv("SERVE_MEDIA", "False") == "True":
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", media_serve, {"document_root": settings.MEDIA_ROOT}),
    ]