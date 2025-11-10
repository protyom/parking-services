from rest_framework import mixins, viewsets

from parking_services.api.v1.serializers.parking_section import \
    ParkingSectionSerializer
from parking_services.core.models import ParkingSection


class ParkingSectionViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):

    queryset = ParkingSection.objects.all()
    serializer_class = ParkingSectionSerializer(many=True)
