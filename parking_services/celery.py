import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parking_services.settings')

app = Celery('parking_services')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


CELERYBEAT_SCHEDULE = {
    'actualize-parking-state': {
        'task': 'parking_services.core.tasks.update_parking_places',
        'schedule': crontab(minute="*/2"),
    },
}


app.conf.update(
    # BROKER_URL='amqp://guest:guest@localhost:5672//',
    BROKER_URL='redis://:{}@{}:{}/0'.format(
        settings.REDIS_PASSWORD, settings.REDIS_ADDR, settings.REDIS_PORT),
    # CELERY_TASK_RESULT_EXPIRES=3600,
    BROKER_CONNECTION_MAX_RETRIES=None,
    BROKER_CONNECTION_RETRY=True,
    CELERY_TIMEZONE='UTC',
    CELERYD_LOG_LEVEL='DEBUG',
    CELERY_SEND_EVENTS=True,
    CELERY_ACCEPT_CONTENT=['pickle', 'json'],
    # CELERY_RESULT_BACKEND='djcelery.backends.database:DatabaseBackend',
    CELERY_RESULT_BACKEND='redis://:{}@{}:{}/1'.format(
        settings.REDIS_PASSWORD, settings.REDIS_ADDR, settings.REDIS_PORT
    ),
    CELERYBEAT_SCHEDULE=CELERYBEAT_SCHEDULE,
)
