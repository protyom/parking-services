#!/usr/bin/env sh
rm /app/celerybeat.pid -f && rm /app/celerybeat-schedule -f && celery -A parking_services beat