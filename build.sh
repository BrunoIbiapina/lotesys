#!/usr/bin/env bash
# build.sh — passo de build no Render
set -e

echo "[build] collectstatic…"
python -m pip install --upgrade pip
python manage.py collectstatic --noinput