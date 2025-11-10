# Django
from django.conf import settings
from django.core.management import BaseCommand

from parking_services.core.tasks import update_parking_places


class Command(BaseCommand):

    def handle(self, *args, **options):
        update_parking_places.apply_async()
