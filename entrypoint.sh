#!/bin/bash
set -e

echo "Ma'lumotlar bazasi tayyor bo'lishini kutmoqda..."
until python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.db import connection
connection.ensure_connection()
print('DB tayyor!')
" 2>/dev/null; do
  echo "DB hali tayyor emas, 2 soniya kutilmoqda..."
  sleep 2
done

echo "Migratsiya fayllari yaratilmoqda..."
python manage.py makemigrations users --noinput
python manage.py makemigrations tests --noinput
python manage.py makemigrations news --noinput

echo "Migratsiyalar bajarilmoqda..."
python manage.py migrate --noinput

echo "Static fayllar yig'ilmoqda..."
python manage.py collectstatic --noinput

echo "Gunicorn ishga tushirilmoqda..."
exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
