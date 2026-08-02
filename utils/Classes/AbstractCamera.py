import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Optional

import numpy as np
from PySide6.QtCore import QThread, Signal

from utils.Signals import GlobalBus


@dataclass
class CameraParameter:
    id: str
    label: str
    min_value: Any
    max_value: Any
    current_value: Any
    setter: Callable[[Any], None]
    default_value: Any
    step_value: int = 1
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
        self.cam_name = name
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

        if not self.wait(2000):
            # Крайний случай: захват кадра заблокирован в драйвере.
            # terminate() опасен (может оставить драйвер в грязном состоянии),
            # поэтому только предупреждаем, а не убиваем поток насильно.
            print("[WARN] Поток камеры не остановился за 2с, оставляем как есть")



