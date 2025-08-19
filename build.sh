#!/usr/bin/env bash
# build.sh
set -o errexit  # interrompe se qualquer comando falhar

# 1) deps
pip install -r requirements.txt

# 2) assets estáticos
python manage.py collectstatic --noinput

# 3) migrações
python manage.py migrate --noinput