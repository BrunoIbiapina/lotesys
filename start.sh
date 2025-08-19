#!/usr/bin/env bash
set -e

# Ajusta a porta padrão que o Render injeta
export PORT="${PORT:-10000}"

echo "🗃️ migrate..."
python manage.py migrate --noinput

# (Opcional) Criar superusuário automático se variáveis existirem
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  echo "👤 garantindo superusuário…"
  python manage.py shell <<'PY'
import os
from django.contrib.auth import get_user_model
User = get_user_model()
u, created = User.objects.get_or_create(
    username=os.getenv("DJANGO_SUPERUSER_USERNAME"),
    defaults={"email": os.getenv("DJANGO_SUPERUSER_EMAIL","admin@example.com"),
              "is_staff": True, "is_superuser": True}
)
if created:
    u.set_password(os.getenv("DJANGO_SUPERUSER_PASSWORD"))
    u.save()
    print("✅ superusuário criado")
else:
    print("ℹ️ superusuário já existe")
PY
fi

echo "🚀 gunicorn…"
exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --log-file -