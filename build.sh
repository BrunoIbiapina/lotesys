#!/usr/bin/env bash
# build.sh — passos de build/deploy no Render
set -e

echo "📦 collectstatic…"
python manage.py collectstatic --noinput || true

echo "🗃️ migrate…"
python manage.py migrate --noinput

echo "👤 Garantindo superusuário…"
python manage.py shell <<'PY'
import os
from django.contrib.auth import get_user_model

User = get_user_model()

username = os.getenv("DJANGO_SUPERUSER_USERNAME", "admin")
email = os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "admin123")

u, created = User.objects.get_or_create(
    username=username,
    defaults={"email": email, "is_staff": True, "is_superuser": True},
)
if created:
    u.set_password(password)
    u.save()
    print(f"✅ Superusuário criado: {username}")
else:
    print(f"ℹ️ Superusuário já existe: {username}")
PY

echo "✅ build.sh finalizado!"