import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Optional

import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

from utils.Signals import GlobalBus


# структура для настроек камеры
@dataclass
class CameraParameter:
    id: str
    label: str
    min_value: Any
    max_value: Any
    current_value: Any
    setter: Callable[[Any], None]
    default_value: Any
    step_value: int = 1  # НОВОЕ: шаг изменения для промышленных камер
    has_auto: bool = False
    auto_setter: Optional[Callable[[bool], None]] = None
    is_auto_now: bool = False


class AbstractCamera(ABC):
    @abstractmethod
    def open(self) -> bool:
        pass

    @abstractmethod
    def get_frame(self) -> np.ndarray:
        pass

    @abstractmethod
    def get_fps(self) -> float:
        pass

    @abstractmethod
    def set_exposure(self, value: int):
        pass

    @abstractmethod
    def set_brightness(self, value):
        pass

    @abstractmethod
    def set_contrast(self, value):
        pass

    @abstractmethod
    def set_gamma(self, value):
        pass

    @abstractmethod
    def set_gain(self, value):
        pass

    @abstractmethod
    def set_auto_exposure(self, is_auto):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def get_parameters(self):
        pass


class CameraThread(QThread):
    camera_opened = Signal()
    camera_error = Signal(str)

    def __init__(self, camera: AbstractCamera, name: str):
        super().__init__()
        self.camera = camera
        self.cam_name = name  # Теперь поток знает, как называется его камера
        self.running = False

    def run(self):
        if not self.camera.open():
            self.camera_error.emit("Ошибка открытия")
            return
        self.camera_opened.emit()
        self.running = True

        while self.running:
            frame = self.camera.get_frame()
            if frame is None:
                continue

            # send raw frame to bus
            GlobalBus.instance().raw_frame_sent.emit(self.cam_name, frame)
            time.sleep(0.05)

        self.camera.close()

    def stop(self):
        self.running = False

        if not self.wait(500):
            self.terminate()
            self.wait()


class CameraFactory:
    @staticmethod
    def _get_types():
        from .HarvesterCamera import HarvesterCamera
        from .UVCCamera import UVCCamera

        return {"UVC": UVCCamera, "HARVESTER": HarvesterCamera}

    # @staticmethod
    # def create(config: dict) -> AbstractCamera:
    #     cam_type = config.get("type")
    #     camera_class = CameraFactory._types.get(cam_type)

    #     if not camera_class:
    #         return None

    #     # У каждой камеры свои параметры.
    #     # UVC нужен index, RTSP нужен будет url.
    #     if cam_type == "UVC":
    #         return camera_class(index=config.get("index"))

    #     # Здесь можно будет добавить логику для других типов:
    #     # elif cam_type == "RTSP":
    #     #     return camera_class(url=config.get("url"))

    #     return None

    @staticmethod
    def create(config: dict) -> AbstractCamera:
        cam_type = config.get("type")
        types = CameraFactory._get_types()
        camera_class = types.get(cam_type)

        if not camera_class:
            return None

        if cam_type == "UVC":
            return camera_class(index=config.get("index"))

        if cam_type == "HARVESTER":
            return camera_class(
                cti_path=config.get("cti_path"), serial=config.get("serial")
            )

        return None
