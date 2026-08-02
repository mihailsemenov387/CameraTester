from PySide6.QtCore import QObject, Signal


class GlobalBus(QObject):
    raw_frame_sent = Signal(str, object)
    # обрезанный по ROI кадр для анализа (ссылка на копию)
    frame_to_use = Signal(str, object)

    analysis_results_sent = Signal(str, dict)
    analysis_many_results_sent = Signal(str, dict)
    # max_intensity_found = Signal(dict)

    analysis_cleared = Signal()


    is_draw_fit = Signal(bool)
    is_draw_cross = Signal(bool)

    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
