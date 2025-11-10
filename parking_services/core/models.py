from django.db import models
from django.utils.timezone import now


class ParkingSection(models.Model):

    name = models.CharField(max_length=255, primary_key=True)
    verbose_name = models.CharField(blank=True)
    capacity = models.SmallIntegerField(default=0)


class ParkingState(models.Model):

    section = models.ForeignKey(
        "ParkingSection",
        on_delete=models.CASCADE,
        related_name="states",
    )
    free_places = models.SmallIntegerField(default=0)
    created_photo_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_photo_at"]
        get_latest_by = "created_photo_at"
