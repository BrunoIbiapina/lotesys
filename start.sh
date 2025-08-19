#!/usr/bin/env bash
set -e
export PORT="${PORT:-10000}"

echo "🗃️ migrate..."
python manage.py migrate --noinput

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
    # Garante flags corretas caso alguém tenha mudado depois
    changed = False
    if not u.is_staff: 
        u.is_staff = True; changed = True
    if not u.is_superuser: 
        u.is_superuser = True; changed = True
    if changed: 
        u.save()
    print(f"ℹ️ superusuário já existe: {username}")
PY

echo "🚀 gunicorn…"
exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --log-file -