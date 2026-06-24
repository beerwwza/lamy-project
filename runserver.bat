@echo off
set DJANGO_SECRET_KEY=test-secret-key-for-local-dev-only-not-for-production
set DJANGO_DEBUG=True
python manage.py runserver 8001 --noreload
