from parking_services.celery import app

from django.conf import settings

from parking_services.core.models import ParkingState
from parking_services.core.vision.camera import Camera, CameraCluster

from ultralytics import YOLO


@app.task
def update_parking_places() -> None:

    all_cameras_config = settings.CAMERA_CONF

    camera_cluster = CameraCluster(all_cameras_config)

    model = YOLO(settings.YOLO_PATH)
    results = model(camera_cluster.images, conf=0.3, save=False)

    states = camera_cluster.get_parking_states_by_sectors(results)

    ParkingState.objects.bulk_create(states)
