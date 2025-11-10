from parking_services.core.models import ParkingState, ParkingSection
from parking_services.core.vision.camera import CameraCluster


def get_parking_states_by_sectors(camera_cluster: CameraCluster, results) -> list[ParkingState]:
    result = []
    for camera, vision_result in zip(camera_cluster.cameras, results):
        pass

    return result
