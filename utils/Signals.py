from PySide6.QtCore import QObject, Signal


class GlobalBus(QObject):
    # Камера кидает сюда сырой кадр
    raw_frame_sent = Signal(str, object)

    # Анализ кидает сюда результаты Гаусса
    analysis_results_sent = Signal(str, dict)
    analysis_many_results_sent = Signal(str, dict)

    is_draw_fit = Signal(bool)
    is_draw_cross = Signal(bool)

    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
