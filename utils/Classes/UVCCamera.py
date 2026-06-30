import sys

import cv2

from .AbstractCamera import AbstractCamera, CameraParameter


class UVCCamera(AbstractCamera):
    def __init__(self, index=0):
        self.index = index
        self.cap = None

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
