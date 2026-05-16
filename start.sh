#!/bin/sh
set -e

echo "==> Ejecutando migraciones..."
python manage.py migrate --noinput

echo "==> Creando superusuario si no existe..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homie.settings')
django.setup()
from accounts.models import CustomUser
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@homie.app')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin1234')
if not CustomUser.objects.filter(username=username).exists():
    CustomUser.objects.create_superuser(username=username, email=email, password=password)
    print(f'Superusuario {username} creado.')
else:
    print(f'Superusuario {username} ya existe.')
"

echo "==> Sembrando logros si no existen..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homie.settings')
django.setup()
from accounts.models import Achievement
if Achievement.objects.count() == 0:
    exec(open('scripts/setup_achievements.py').read())
    print('Logros creados.')
else:
    print(f'{Achievement.objects.count()} logros ya existen.')
"

echo "==> Iniciando Gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 homie.wsgi:application
