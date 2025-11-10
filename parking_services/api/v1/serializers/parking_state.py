from rest_framework import serializers

from parking_services.api.v1.serializers.parking_section import \
    ParkingSectionSerializer
from parking_services.core.models import ParkingState, ParkingSection


class ParkingStateSerializer(serializers.ModelSerializer):

    section = ParkingSectionSerializer()

    class Meta:
        model = ParkingState
        fields = ('section', 'free_places', 'created_photo_at',)


