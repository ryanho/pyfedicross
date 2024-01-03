#!/bin/sh
cd /app
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn pyfedicross.wsgi -b 0.0.0.0