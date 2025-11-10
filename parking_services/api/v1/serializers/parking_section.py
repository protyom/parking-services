from django.db import transaction
from rest_framework import serializers

from parking_services.core.models import ParkingSection


class ParkingSectionListSerializer(serializers.ListSerializer):
    def create(self, validated_data: list[dict]) -> list[ParkingSection]:

        old_sections = set(ParkingSection.objects.all())
        new_sections = {ParkingSection(**item) for item in validated_data}

        with transaction.atomic():
            sections_to_delete = old_sections.difference(new_sections)
            ParkingSection.objects.filter(id__in=[section.id for section in sections_to_delete]).delete()

            sections_to_update = old_sections.intersection(new_sections)
            ParkingSection.objects.bulk_update(sections_to_update, ('name', 'full_name'))

            sections_to_create = new_sections.difference(old_sections)
            ParkingSection.objects.bulk_create(sections_to_create)

        return list(new_sections)


class ParkingSectionSerializer(serializers.ModelSerializer):

    class Meta:
        model = ParkingSection
        fields = ('name', 'verbose_name',)
        list_serializer_class = ParkingSectionListSerializer
