from django.contrib import admin
from parking_services.core.models import ParkingSection, ParkingState


admin.site.register(ParkingSection)
admin.site.register(ParkingState)
