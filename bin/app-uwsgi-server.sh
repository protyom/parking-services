#!/usr/bin/env bash
python3 manage.py collectstatic --noinput && python3 manage.py migrate && uwsgi --ini /app/config/uwsgi/uwsgi.ini