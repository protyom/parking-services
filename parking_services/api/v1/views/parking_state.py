from datetime import timedelta

from django.db.models import Max
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from parking_services.api.v1.serializers.parking_state import (
    ParkingStateSerializer
)
from parking_services.core.models import ParkingState


class ParkingStateViewSet(ReadOnlyModelViewSet):

    serializer_class = ParkingStateSerializer

    def get_queryset(self):
        max_created_photo_at = \
            ParkingState.objects.aggregate(
                max_created=Max('created_photo_at'))['max_created']
        if not max_created_photo_at:
            return ParkingState.objects.all()

        return ParkingState.objects.filter(
            created_photo_at__gte=max_created_photo_at - timedelta(seconds=1),
        ).select_related('section')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        response_data = {
            "phrase": ', '.join([f'{state["section"]["verbose_name"]} - {state["free_places"]}' for state in data]),
            "data": data
        }
        return Response(response_data)
