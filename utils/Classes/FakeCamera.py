import numpy as np
import cv2
from scipy.special import j1

from .AbstractCamera import AbstractCamera, CameraParameter
from .CameraRegistry import register_camera


@register_camera(typ="FAKECAM", title="Fake Camera")
class FakeAiryCamera(AbstractCamera):
    def __init__(self, index=0):
        self.index = index

        self.width = 640
        self.height = 480
        self.fps = 30

        self._exposure = -5
        self._gamma = 100
        self._gain = 4
        self._contrast = 127
        self._brightness = 0
        self._is_auto_exposure = False

    def open(self):
        return True

    def get_fps(self):
        return self.fps

    def get_frame(self):
        # 1. Задаем базовый масштаб диска Эйри.
        # Привяжем его к экспозиции: чем больше экспозиция, тем больше "размытие" (пятно)
        # Экспозиция от -10 до 0 -> масштаб от 0.05 (крупный) до 0.3 (мелкий)
        exp_normalized = (self._exposure - (-10)) / 10.0  # от 0.0 до 1.0
        scale = 0.3 - (exp_normalized * 0.25)  # чем больше экспозиция, тем меньше scale (шире диск)

        # 2. Генерируем сетку координат относительно центра
        x = np.linspace(-self.width / 2, self.width / 2, self.width)
        y = np.linspace(-self.height / 2, self.height / 2, self.height)
        X, Y = np.meshgrid(x, y)
        R = np.sqrt(X**2 + Y**2) * scale

        # 3. Считаем интенсивность диска Эйри
        I = np.ones_like(R)
        mask = R != 0
        I[mask] = (2 * j1(R[mask]) / R[mask]) ** 2

        # 4. Применяем параметры Яркости (Brightness) и Усиления (Gain)
        # Базовая максимальная интенсивность зависит от Gain
        base_intensity = 50 * self._gain  # Gain (4..8) даст базовую яркость 200..400
        img = I * base_intensity + self._brightness

        # 5. Применяем Контраст (Contrast)
        # Формула контраста: фактор * (пиксель - 127) + 127
        contrast_factor = (self._contrast / 127.0)
        img = contrast_factor * (img - 127.0) + 127.0

        # 6. Применяем Гамму (Gamma)
        # Нормализуем гамму (100 -> 1.0). Формула: ((пиксель / 255) ^ (1 / gamma)) * 255
        gamma_factor = self._gamma / 100.0
        img = np.clip(img, 0, 255) / 255.0
        img = np.power(img, 1.0 / gamma_factor) * 255.0

        # Ограничиваем диапазон и переводим в 8-битный формат
        img_gray = np.clip(img, 0, 255).astype(np.uint8)

        # Возвращаем 3-канальное BGR изображение, как это делает OpenCV
        return cv2.cvtColor(img_gray, cv2.COLOR_GRAY2BGR)

    # Сеттеры просто сохраняют значения в память класса
    def set_exposure(self, value):
        self._exposure = int(value)

    def set_brightness(self, value):
        self._brightness = int(value)

    def set_contrast(self, value):
        self._contrast = int(value)

    def set_gamma(self, value):
        self._gamma = int(value)

    def set_gain(self, value):
        self._gain = int(value)

    def set_auto_exposure(self, is_auto: bool):
        self._is_auto_exposure = is_auto
        if is_auto:
            self._exposure = -5  # Имитируем работу автоматики (сброс в дефолт)
        print(f"Фейковая автоэкспозиция: {'ВКЛ' if is_auto else 'ВЫКЛ'}")

    def get_parameters(self) -> dict[str, CameraParameter]:
        # Возвращаем структуру с нашими внутренними переменными
        return {
            "exposure": CameraParameter(
                id="exposure",
                label="Экспозиция:",
                min_value=-10,
                max_value=0,
                default_value=-5,
                current_value=self._exposure,
                setter=self.set_exposure,
                has_auto=True,
                auto_setter=self.set_auto_exposure,
                is_auto_now=self._is_auto_exposure,
            ),
            "gamma": CameraParameter(
                id="gamma",
                label="Gamma:",
                min_value=90,
                max_value=150,
                default_value=100,
                current_value=self._gamma,
                setter=self.set_gamma,
            ),
            "gain": CameraParameter(
                id="gain",
                label="Gain:",
                min_value=4,
                max_value=8,
                default_value=4,
                current_value=self._gain,
                setter=self.set_gain,
            ),
            "contrast": CameraParameter(
                id="contrast",
                label="Contrast:",
                min_value=0,
                max_value=255,
                default_value=127,
                current_value=self._contrast,
                setter=self.set_contrast,
            ),
            "brightness": CameraParameter(
                id="brightness",
                label="Brightness:",
                min_value=-127,
                max_value=127,
                default_value=0,
                current_value=self._brightness,
                setter=self.set_brightness,
            ),
        }

    def close(self):
        pass
