from abc import ABC, abstractmethod

import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

from utils.Signals import GlobalBus


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


class UVCCamera(AbstractCamera):
    def __init__(self, index=0):
        self.index = index
        self.cap = None

    def open(self):
        self.cap = cv2.VideoCapture(self.index)
        return self.cap.isOpened()

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

    def set_auto_exposure(self, is_auto: bool):
        if self.cap:
            val = 3 if is_auto else 1
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, val)
            print(f"Автоэкспозиция: {'ВКЛ' if is_auto else 'ВЫКЛ'}")

    def close(self):
        if self.cap:
            self.cap.release()


class CameraThread(QThread):
    # Оставляем frame_ready только для локальной быстрой отрисовки, если нужно
    frame_ready = Signal(QImage)
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

            # ВЕЩАЕМ В ШИНУ НАПРЯМУЮ: "Я Камера Х, вот мой кадр"
            GlobalBus.instance().raw_frame_sent.emit(self.cam_name, frame)

            # Конвертация для UI (опционально, можно тоже через шину)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            q_img = QImage(rgb_frame.data, w, h, ch * w, QImage.Format_RGB888)
            self.frame_ready.emit(q_img.copy())

        self.camera.close()

    def stop(self):
        self.running = False

        if not self.wait(500):
            print("Поток камеры завис в OpenCV, принудительное завершение...")
            self.terminate()
            self.wait()  # Ждем завершения после терминации, пока метод run() реально завершится


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
