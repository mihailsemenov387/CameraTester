from PySide6.QtCore import QTimer
from PySide6.QtMultimedia import QMediaDevices
from PySide6.QtWidgets import (
    QComboBox,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

CAMERA_CONFIG_REGISTRY = {}


def register_congig_page(title: str, typ: str):
    def wrapper(cls):
        CAMERA_CONFIG_REGISTRY[typ] = (title, cls)
        return cls

    return wrapper


@register_congig_page(title="USB Camera(UVC)", typ="UVC")
class UVCConfigPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.combo = QComboBox()
        layout.addWidget(self.combo)

        QTimer.singleShot(100, self.refresh)

    def refresh(self):
        self.combo.clear()
        for i, cam in enumerate(QMediaDevices.videoInputs()):
            self.combo.addItem(cam.description(), i)

    def get_values(self):
        return {"index": self.combo.currentData(), "name": self.combo.currentText()}


@register_congig_page("RTSP Stream", "RTSP")
class RTSPConfigPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("rtsp://...")
        layout.addWidget(self.url_input)

    def get_values(self):
        return {"url": self.url_input.text(), "name": "IP Camera"}
