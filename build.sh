#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput

if [[ -n "${DJANGO_BOOTSTRAP_ADMIN_USERNAME:-}" && -n "${DJANGO_BOOTSTRAP_ADMIN_PASSWORD:-}" ]]; then
    python manage.py shell < crm/bootstrap_admin.py
fi
