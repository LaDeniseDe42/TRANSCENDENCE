#!/bin/bash
echo "Django is starting..."
sleep 10
env > ./.env
python /app/transcendence/manage.py makemigrations
python /app/transcendence/manage.py migrate

# Créer superuser
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('${DJANGO_SUPERUSER_USERNAME}', '${DJANGO_SUPERUSER_EMAIL}', '${DJANGO_SUPERUSER_PASSWORD}')" | python /app/transcendence/manage.py shell

# Lancer le serveur Daphne
daphne -b 0.0.0.0 -p 8000 transcendence.asgi:application
