"""
Django settings for config project.
"""
from pathlib import Path
import os  # <-- novo

# ===================== BASE =====================
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-qigmwiful=y_&a_r+ar!@dvvz4nqs)^1*2p(8b$tl&4jq6pji3"
DEBUG = True

# Permite localhost e o host público do Render (se existir)
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
# Render expõe o host em uma env var; usamos o que estiver disponível
RENDER_HOST = (
    os.environ.get("RENDER_EXTERNAL_HOSTNAME")
    or os.environ.get("RENDER_EXTERNAL_URL", "").replace("https://", "").replace("http://", "").strip("/")
)
if RENDER_HOST:
    ALLOWED_HOSTS.append(RENDER_HOST)

# Confia nos domínios para CSRF (útil para admin/login no Render)
CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1",
    "http://localhost",
]
if RENDER_HOST:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_HOST}")

# ===================== APPS =====================
INSTALLED_APPS = [
    # Tema do Admin (precisa vir ANTES do admin)
    "jazzmin",

    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Apps do projeto
    "usuarios",
    "dashboard",
    "cadastros",
    "vendas.apps.VendasConfig",   # garante o AppConfig (signals etc.)
    "financeiro",
]

# ===================== MIDDLEWARE =====================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
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
        # Pasta global de templates do projeto
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            # Torna disponível o filtro length_is (compat) em TODOS os templates, inclusive do admin/Jazzmin
            "builtins": ["vendas.templatetags.compat"],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ===================== DATABASE =====================
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
# Produção (collectstatic)
STATIC_ROOT = BASE_DIR / "staticfiles"
# Desenvolvimento: servir ./static/
STATICFILES_DIRS = [BASE_DIR / "static"]

# ===================== DEFAULTS =====================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ===================== AUTH REDIRECTS =====================
# Use os names com namespace do app 'usuarios' e 'dashboard'
LOGIN_URL = "usuarios:login"
LOGIN_REDIRECT_URL = "dashboard:dashboard_index"   # <— evita NoReverseMatch
LOGOUT_REDIRECT_URL = "usuarios:login"

# ===================== JAZZMIN =====================
JAZZMIN_SETTINGS = {
    "site_title": "LoteSys Admin",
    "site_header": "LoteSys",
    "site_brand": "LoteSys",
    "welcome_sign": "Bem-vindo ao LoteSys",

    # Sem logo custom (ajustes finos via CSS abaixo)
    "site_logo": None,

    # Carrega nosso CSS com pequenos ajustes do admin
    # (crie: static/css/admin.css)
    "custom_css": "css/admin.css",

    "show_ui_builder": False,

    # Ícones (Font Awesome)
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

    # Ordem dos apps no menu lateral
    "order_with_respect_to": ["auth", "cadastros", "financeiro", "vendas"],

    # Links do topo
    "topmenu_links": [
        {"name": "Dashboard", "url": "/", "permissions": ["auth.view_user"]},
        {"name": "Extrato", "url": "financeiro:extrato"},
        {"name": "Vendas", "url": "vendas:list"},
    ],

    "copyright": "LoteSys",
}

JAZZMIN_UI_TWEAKS = {
    "theme": "darkly",           # troque p/ "flatly" se quiser claro
    "navbar": "navbar-dark",
    "no_navbar_border": True,
    "sidebar_fixed": True,
    "layout_fixed": True,
    "show_sidebar": True,
}