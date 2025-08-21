"""
Django settings for config project.
"""
from pathlib import Path
import os

# ===================== BASE =====================
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-qigmwiful=y_&a_r+ar!@dvvz4nqs)^1*2p(8b$tl&4jq6pji3",
)
# Use a env var padronizada no Render
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"

# ===================== HOSTS / CSRF =====================
# Host fixo + hostname injetado pelo Render (se existir)
RENDER_HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "lotesys.onrender.com"]
if RENDER_HOST and RENDER_HOST not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_HOST)

CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1",
    "http://localhost",
    "https://lotesys.onrender.com",
]
if RENDER_HOST:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_HOST}")

# Django atrás de proxy (Render/Cloudflare)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# Cookies seguros quando em produção
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# ===================== APPS =====================
INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "usuarios",
    "dashboard",
    "cadastros",
    "vendas.apps.VendasConfig",
    "financeiro",
]

# ===================== MIDDLEWARE =====================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise logo após SecurityMiddleware
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

# ===================== TEMPLATES =====================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            # Filtros/templatetags compat em todos os templates (inclui admin/Jazzmin)
            "builtins": ["vendas.templatetags.compat"],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ===================== DATABASE =====================
import dj_database_url

if os.getenv("DATABASE_URL"):
    # Postgres do Render (persistente)
    DATABASES = {
        "default": dj_database_url.parse(
            os.environ["DATABASE_URL"],
            conn_max_age=600,
            ssl_require=True,
        )
    }
else:
    # SQLite local (não persiste no Render)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ===================== PASSWORDS =====================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ===================== I18N / TZ =====================
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Recife"
USE_I18N = True
USE_TZ = True

# ===================== STATIC =====================
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# WhiteNoise para servir estáticos no Render
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ===================== DEFAULTS =====================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ===================== AUTH REDIRECTS =====================
LOGIN_URL = "usuarios:login"
LOGIN_REDIRECT_URL = "dashboard:dashboard_index"
LOGOUT_REDIRECT_URL = "usuarios:login"

# ===================== JAZZMIN =====================
JAZZMIN_SETTINGS = {
    "site_title": "LoteSys Admin",
    "site_header": "LoteSys",
    "site_brand": "LoteSys",
    "welcome_sign": "Bem-vindo ao LoteSys",
    "site_logo": None,
    "custom_css": "css/admin.css",
    "show_ui_builder": False,
    "icons": {
        "auth.User": "fas fa-user",
        "auth.Group": "fas fa-users-cog",
        "cadastros.Cliente": "fas fa-id-card",
        "cadastros.Empreendimento": "fas fa-city",
        "cadastros.Lote": "fas fa-th-large",
        "financeiro.Despesa": "fas fa-receipt",
        "financeiro.ReceitaExtra": "fas fa-plus-circle",
        "vendas.Venda": "fas fa-shopping-cart",
        "vendas.Parcela": "fas fa-money-check-alt",
    },
    "order_with_respect_to": ["auth", "cadastros", "financeiro", "vendas"],
    # Usa link fixo p/ evitar erro de reverse em produção
    "topmenu_links": [
        {"name": "Dashboard", "url": "/", "permissions": ["auth.view_user"]},
        {"name": "Extrato", "url": "financeiro:extrato"},
        {"name": "Vendas", "url": "/vendas/"},
    ],
    "copyright": "LoteSys",
}

JAZZMIN_UI_TWEAKS = {
    "theme": "darkly",
    "navbar": "navbar-dark",
    "no_navbar_border": True,
    "sidebar_fixed": True,
    "layout_fixed": True,
    "show_sidebar": True,
}