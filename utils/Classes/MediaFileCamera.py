from abc import abstractmethod

from .AbstractCamera import AbstractCamera, CameraParameter


class MediaFileCamera(AbstractCamera):
    """Базовая «камера» на основе медиафайла (фото / видео).

    Вся общая логика уже здесь: открытие, интерфейс кадра, заглушки для
    настроек (к файлу они не применимы). Наследнику нужно реализовать только
    два метода:
      - `_open_source(path)` — загрузить источник (фото или видео);
      - `_next_frame()`      — вернуть следующий кадр (BGR np.ndarray).

    Добавление поддержки видео = новый класс-наследник (~15 строк) +
    переиспользование конфиг-страницы (см. MediaFileConfigPage).
    """

    def __init__(self, path=""):
        self.path = path
        self.fps = 1.0
        self._frame = None

    def open(self) -> bool:
        if not self.path:
            return False
        return self._open_source(self.path)

    @abstractmethod
    def _open_source(self, path: str) -> bool:
        """Загружает источник по пути. True при успехе."""

    @abstractmethod
    def _next_frame(self):
        """Возвращает следующий кадр (BGR np.ndarray) или None."""

    def get_frame(self):
        return self._next_frame()

    def get_fps(self):
        return self.fps

    # К файлу настройки не применимы — заглушки (интерфейс AbstractCamera).
    def set_exposure(self, value):
        pass

    def set_brightness(self, value):
        pass

    def set_contrast(self, value):
        pass

    def set_gamma(self, value):
        pass

    def set_gain(self, value):
        pass

    def set_auto_exposure(self, is_auto):
        pass

    def get_parameters(self) -> dict[str, CameraParameter]:
        return {}

    def close(self):
        self._frame = None
