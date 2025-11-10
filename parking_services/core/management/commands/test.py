from django.core.management import BaseCommand
from rest_framework_api_key.models import APIKey


class Command(BaseCommand):

    def handle(self, *args, **options):
        obj, key = APIKey.objects.create_key(name='home')
        print(key)
