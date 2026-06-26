from abc import ABC, abstractmethod

import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage


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
        self.cap = (
            None  # Здесь можно использовать встроенный cv2 чисто как драйвер-доставщик
        )

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
            # В OpenCV флаг автоэкспозиции зависит от драйвера.
            # Обычно 3 - это Авто, а 1 или 0.25 - это ручной режим.
            val = 3 if is_auto else 1
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, val)
            print(f"Автоэкспозиция: {'ВКЛ' if is_auto else 'ВЫКЛ'}")

    def close(self):
        if self.cap:
            self.cap.release()


class CameraThread(QThread):
    frame_ready = Signal(QImage)

    def __init__(self, camera: AbstractCamera):
        super().__init__()
        self.camera = camera
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            frame = self.camera.get_frame()
            if frame is not None:
                # ---> ЗДЕСЬ МОГЛА БЫ БЫТЬ ВАША МАТЕМАТИКА (ГАУССИАНА) <---

                # Конвертируем OpenCV BGR кадр в формат RGB для интерфейса Qt
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_frame.shape
                bytes_per_line = ch * w

                # Создаем картинку Qt и отправляем в интерфейс
                q_img = QImage(
                    rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888
                )
                self.frame_ready.emit(q_img)

    def stop(self):
        self.running = False
        self.wait()  # Ждем завершения потока
