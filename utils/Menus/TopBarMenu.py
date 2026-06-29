from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QStackedWidget,
    QVBoxLayout,
)

from .CameraTypeConfig import RTSPConfigPage, UVCConfigPage


# TODO: add loader for camera type
class CameraSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Подключение")

        main_layout = QVBoxLayout(self)

        self.type_combo = QComboBox()
        self.type_combo.addItem("USB Camera", "UVC")
        self.type_combo.addItem("RTSP Stream", "RTSP")
        main_layout.addWidget(QLabel("Тип:"))
        main_layout.addWidget(self.type_combo)

        self.pages = QStackedWidget()
        self.uvc_page = UVCConfigPage()
        self.rtsp_page = RTSPConfigPage()

        self.pages.addWidget(self.uvc_page)
        self.pages.addWidget(self.rtsp_page)
        main_layout.addWidget(self.pages)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        main_layout.addWidget(self.buttons)

        self.type_combo.currentIndexChanged.connect(self.pages.setCurrentIndex)

    def get_camera_config(self) -> dict:
        cam_type = self.type_combo.currentData()

        config = self.pages.currentWidget().get_values()

        config["type"] = cam_type
        return config
