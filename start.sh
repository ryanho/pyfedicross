#!/bin/sh
cd /app
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py rundramatiq &
gunicorn pyfedicross.wsgi -b 0.0.0.0