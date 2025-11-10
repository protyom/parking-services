import json
from typing import Any

import cv2
from django.utils import timezone
from sympy import Point, Polygon
from ultralytics import YOLO
from PIL import Image, ImageDraw

from parking_services.core.models import ParkingSection, ParkingState


def iterable_to_polygon(tuple_polygon):
    points = [Point(point[0], point[1]) for point in tuple_polygon]
    return Polygon(*points)


class Sector:
    def __init__(self, name: str, polygon: list[list[int]], db_obj: ParkingSection, **kwargs) -> None:
        self.name = name
        self.points = [(point[0], point[1]) for point in polygon]
        self.polygon = iterable_to_polygon(polygon)
        self.db_obj = db_obj
        self.car_count = 0


class Camera:

    def __init__(self, connection: str, sections: list[dict[str, Any]]) -> None:
        self.connection = connection
        self.sections = [Sector(**section_data) for section_data in sections]
        self.frame_image = None
        self.total_car_count = 0

    @property
    def image(self) -> Image:
        cap = cv2.VideoCapture(self.connection)
        if cap.isOpened():
            ret, frame = cap.read()
            frame =  frame[:, :, ::-1]
            self.frame_image = Image.fromarray(frame, "RGB")
            return self.frame_image



    def show_sections(self) -> None:
        draw = ImageDraw.Draw(self.frame_image)
        for section in self.sections:
            draw.polygon(section.points)
        self.frame_image.show()

    def divide_by_sectors(self, result):
        self.total_car_count = 0
        for section in self.sections:
            section.car_count = 0

        for box in result.boxes:
            if int(box.cls[0]) != 2:
                continue
            self.total_car_count += 1
            coords = box.xyxy.tolist()[0]
            center = Point((coords[0] + coords[2]) / 2,
                           (coords[1] + coords[3]) / 2)
            for section in self.sections:
                if section.polygon.encloses(center):
                    section.car_count += 1
        print('Total count:', self.total_car_count)
        results = []
        for section in self.sections:
            results.append(
                ParkingState(
                    section=section.db_obj,
                    free_places=section.db_obj.capacity - section.car_count
                )
            )
        return results


class CameraCluster:
    def __init__(self, all_cameras_config: dict):
        section_name_mapping = {section.name: section for section in ParkingSection.objects.all()}
        self.cameras = []

        for camera_data in all_cameras_config["cameras"]:
            for section in camera_data["sections"]:
                section["db_obj"] = section_name_mapping[section["name"]]
            self.cameras.append(Camera(**camera_data))

    @property
    def images(self) -> list[Image]:
        self.created_photo_at = timezone.now()
        return [camera.image for camera in self.cameras]

    def get_parking_states_by_sectors(self, results) -> list[ParkingState]:
        result = []
        for camera, vision_result in zip(self.cameras, results):
            result.extend(camera.divide_by_sectors(vision_result))

        return result
