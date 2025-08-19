#!/usr/bin/env bash
# build.sh

echo "🚀 Rodando migrações..."
python manage.py migrate --noinput

echo "👤 Criando superusuário padrão (se não existir)..."
echo "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
" | python manage.py shell

echo "✅ Build finalizado!"