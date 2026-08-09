import cv2
import numpy as np

from .CameraRegistry import register_camera
from .MediaFileCamera import MediaFileCamera


@register_camera(typ="PHOTO", title="Photo (из файла)")
class PhotoCamera(MediaFileCamera):
    """«Камера», которая постоянно отдаёт одно статичное изображение из файла.

    Кадр читается один раз при открытии и возвращается каждый раз —
    в конвейер попадает одно и то же фото (BGR, как от OpenCV-камер).

    ВАЖНО: читаем файл через Python `open()` + `cv2.imdecode`, а не через
    `cv2.imread` — последний на Windows не понимает Unicode/кириллические
    пути вроде «схема_3_комплекса_вэпп-2000.png».
    """

    def _open_source(self, path: str) -> bool:
        try:
            with open(path, "rb") as f:
                buf = np.frombuffer(f.read(), dtype=np.uint8)
        except OSError:
            return False
        img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        if img is None:
            return False
        self._frame = img
        self.fps = 1.0
        return True

    def _next_frame(self):
        return self._frame
