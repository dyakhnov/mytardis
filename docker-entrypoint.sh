#!/bin/bash

python manage.py migrate - noinput
python manage.py collectstatic - noinput

gunicorn wsgi:application -b 0.0.0.0:8000 --config gunicorn_settings.py
