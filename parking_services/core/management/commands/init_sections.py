# Django
from django.conf import settings
from django.core.management import BaseCommand
from django.db import transaction

from parking_services.core.models import ParkingSection


class Command(BaseCommand):

    def handle(self, *args, **options):

        old_sections = set(ParkingSection.objects.all())
        new_sections = set()

        for camera_data in settings.CAMERA_CONF["cameras"]:
            for section_data in camera_data["sections"]:
                new_sections.add(
                    ParkingSection(
                        name=section_data["name"],
                        verbose_name=section_data["verbose_name"],
                        capacity=section_data["capacity"]
                    )
                )

        with transaction.atomic():
            sections_to_delete = old_sections.difference(new_sections)
            ParkingSection.objects.filter(name__in=[section.name for section in sections_to_delete]).delete()

            sections_to_update = old_sections.intersection(new_sections)
            ParkingSection.objects.bulk_update(sections_to_update, ('verbose_name', 'capacity'))

            sections_to_create = new_sections.difference(old_sections)
            ParkingSection.objects.bulk_create(sections_to_create)
