import sys
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
    id: str  # Уникальный ключ (например, "exposure")
    label: str  # Имя для интерфейса (например, "Экспозиция")
    min_value: Any
    max_value: Any
    current_value: Any  # ТЕКУЩЕЕ значение из камеры
    default_value: Any
    setter: Callable[[Any], None]  # Ссылка на метод установки
    has_auto: bool = False  # Есть ли авто-режим
    auto_setter: Optional[Callable[[bool], None]] = None  # Стод авто-режима
    is_auto_now: bool = False  # ТЕКУЩЕЕ состояние авто-режима


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


class UVCCamera(AbstractCamera):
    def __init__(self, index=0):
        self.index = index
        self.cap = None

    # def open(self):
    #     self.cap = cv2.VideoCapture(self.index)
    #     return self.cap.isOpened()

    def open(self):
        if sys.platform.startswith("win"):
            backend = cv2.CAP_DSHOW
        else:
            backend = cv2.CAP_ANY

        self.cap = cv2.VideoCapture(self.index, backend)

        if not self.cap.isOpened():
            return False

        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))

        return True

    def get_fps(self):
        return self.cap.get(cv2.CAP_PROP_FPS)

    def get_frame(self):
        ret, frame = self.cap.read()
        return frame if ret else None

    def set_exposure(self, value):
        self.cap.set(cv2.CAP_PROP_EXPOSURE, value)

    def set_brightness(self, value):
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, value)

    def set_contrast(self, value):
        self.cap.set(cv2.CAP_PROP_CONTRAST, value)

    def set_gamma(self, value):
        self.cap.set(cv2.CAP_PROP_GAMMA, value)

    def set_gain(self, value):
        self.cap.set(cv2.CAP_PROP_GAIN, value)

    # def set_auto_exposure(self, is_auto: bool):
    #     if self.cap:
    #         val = 3 if is_auto else 1
    #         self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, val)
    #         print(f"Автоэкспозиция: {'ВКЛ' if is_auto else 'ВЫКЛ'}")

    def set_auto_exposure(self, is_auto: bool):
        if not self.cap or not self.cap.isOpened():
            return

        if sys.platform.startswith("win"):
            val = 1 if is_auto else 0
        else:
            val = 3 if is_auto else 1

        success = self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, val)
        print(f"Автоэкспозиция: {'ВКЛ' if is_auto else 'ВЫКЛ'} (Статус: {success})")

    def get_parameters(self) -> dict[str, CameraParameter]:
        # ЕСЛИ КАМЕРА ЕЩЕ НЕ ОТКРЫТА — берем безопасные дефолты и не трогаем self.cap
        # if not self.cap or not self.cap.isOpened():
        #     curr_exp, curr_gam, curr_gain, curr_cnt, curr_brg = -5, 100, 1, 127, 0
        #     is_auto_now = False
        # else:
        # Если открыта — честно опрашиваем железку
        curr_exp = self.cap.get(cv2.CAP_PROP_EXPOSURE)
        curr_gam = self.cap.get(cv2.CAP_PROP_GAMMA)
        curr_gain = self.cap.get(cv2.CAP_PROP_GAIN)
        curr_cnt = self.cap.get(cv2.CAP_PROP_CONTRAST)
        curr_brg = self.cap.get(cv2.CAP_PROP_BRIGHTNESS)

        auto_val = self.cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)
        is_auto_now = (
            (auto_val == 1) if sys.platform.startswith("win") else (auto_val == 3)
        )

        return {
            "exposure": CameraParameter(
                id="exposure",
                label="Экспозиция:",
                min_value=-10,
                max_value=0,
                default_value=-5,
                current_value=int(curr_exp),
                setter=self.set_exposure,
                has_auto=True,
                auto_setter=self.set_auto_exposure,
                is_auto_now=is_auto_now,
            ),
            "gamma": CameraParameter(
                id="gamma",
                label="Gamma:",
                min_value=90,
                max_value=150,
                default_value=100,
                current_value=int(curr_gam),
                setter=self.set_gamma,
            ),
            "gain": CameraParameter(
                id="gain",
                label="Gain:",
                min_value=4,
                max_value=8,
                default_value=1,
                current_value=int(curr_gain),
                setter=self.set_gain,
            ),
            "contrast": CameraParameter(
                id="contrast",
                label="Contrast:",
                min_value=0,
                max_value=255,
                default_value=127,
                current_value=int(curr_cnt),
                setter=self.set_contrast,
            ),
            "brightness": CameraParameter(
                id="brightness",
                label="Brightness:",
                min_value=-127,
                max_value=127,
                default_value=0,
                current_value=int(curr_brg),
                setter=self.set_brightness,
            ),
        }

    def close(self):
        if self.cap:
            self.cap.release()


class CameraThread(QThread):
    # Оставляем frame_ready только для локальной быстрой отрисовки, если нужно
    # frame_ready = Signal(QImage)
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

            # TODO: fix if lag (use opengl thing and raw_frame)
            # rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # h, w, ch = rgb_frame.shape

            # temp_img = QImage(rgb_frame.data, w, h, ch * w, QImage.Format_RGB888)
            # q_img = QImage(temp_img)  # for copy
            # self.frame_ready.emit(q_img)

        self.camera.close()

    def stop(self):
        self.running = False

        if not self.wait(500):
            self.terminate()
            self.wait()


class CameraFactory:
    _types = {
        "UVC": UVCCamera,
        # "RTSP": RTSPCamera, # Добавишь, когда напишешь класс
    }

    @staticmethod
    def create(config: dict) -> AbstractCamera:
        cam_type = config.get("type")
        camera_class = CameraFactory._types.get(cam_type)

        if not camera_class:
            return None

        # У каждой камеры свои параметры.
        # UVC нужен index, RTSP нужен будет url.
        if cam_type == "UVC":
            return camera_class(index=config.get("index"))

        # Здесь можно будет добавить логику для других типов:
        # elif cam_type == "RTSP":
        #     return camera_class(url=config.get("url"))

        return None
