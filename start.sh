#!/usr/bin/env bash
set -e

# Porta padrão local; no Render a variável PORT já vem setada.
export PORT="${PORT:-10000}"

echo "🔧 ambiente"
echo " - PYTHON: $(python --version 2>/dev/null || true)"
echo " - DJANGO_SETTINGS_MODULE: ${DJANGO_SETTINGS_MODULE:-config.settings}"
echo " - PORT: $PORT"
echo " - WEB_CONCURRENCY: ${WEB_CONCURRENCY:-2}"

# Coleta de estáticos (idempotente). Se já tiver sido feito no build, isso termina rápido.
echo "🎒 collectstatic (idempotente)…"
python manage.py collectstatic --noinput || true

# Migrações
echo "🗃️ migrate…"
python manage.py migrate --noinput

# Garante diretório de uploads (não dá persistência no Render Free, apenas evita 404 locais)
echo "📂 preparando /media (uploads)…"
mkdir -p "${MEDIA_ROOT:-./media}"

# Criação/garantia de superusuário
echo "👤 garantindo superusuário…"
python manage.py shell <<'PY'
import os
from django.contrib.auth import get_user_model

User = get_user_model()

username = os.getenv("DJANGO_SUPERUSER_USERNAME", "admin")
email    = os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "admin123")

u, created = User.objects.get_or_create(
    username=username,
    defaults={"email": email, "is_staff": True, "is_superuser": True},
)
if created:
    u.set_password(password)
    u.save()
    print(f"✅ superusuário criado: {username}")
else:
    changed = False
    if not u.is_staff:
        u.is_staff = True; changed = True
    if not u.is_superuser:
        u.is_superuser = True; changed = True
    if changed:
        u.save()
    print(f"ℹ️ superusuário já existe: {username}")
PY

# Inicia o Gunicorn
# - WEB_CONCURRENCY permite escalar workers sem mexer no script
# - worker-tmp-dir=/dev/shm ajuda em sistemas com disco lento
# - timeout maior evita matar requests de migração/boot mais demorados
echo "🚀 gunicorn…"
exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --worker-tmp-dir "/dev/shm" \
  --timeout 120 \
  --log-file -