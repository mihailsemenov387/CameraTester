from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
)

from .CameraTypeConfig import CAMERA_CONFIG_REGISTRY

# TODO: add loader for camera type
# class CameraSelectionDialog(QDialog):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setWindowTitle("Подключение")

#         main_layout = QVBoxLayout(self)

#         self.type_combo = QComboBox()
#         self.type_combo.addItem("USB Camera", "UVC")
#         self.type_combo.addItem("RTSP Stream", "RTSP")
#         main_layout.addWidget(QLabel("Тип:"))
#         main_layout.addWidget(self.type_combo)

#         self.pages = QStackedWidget()
#         self.uvc_page = UVCConfigPage()
#         self.rtsp_page = RTSPConfigPage()

#         self.pages.addWidget(self.uvc_page)
#         self.pages.addWidget(self.rtsp_page)
#         main_layout.addWidget(self.pages)

#         self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
#         self.buttons.accepted.connect(self.accept)
#         self.buttons.rejected.connect(self.reject)
#         main_layout.addWidget(self.buttons)

#         self.type_combo.currentIndexChanged.connect(self.pages.setCurrentIndex)


# FIXME: selection dialog size
class CameraSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Подключение")

        self.main_layout = QVBoxLayout(self)

        self.main_layout.addWidget(QLabel("Тип:"))
        self.type_combo = QComboBox()
        self.main_layout.addWidget(self.type_combo)

        self.pages = QStackedWidget()

        self.pages.setSizePolicy(
            self.pages.sizePolicy().horizontalPolicy(), QSizePolicy.Policy.Minimum
        )

        self.main_layout.addWidget(self.pages)

        self.load_workspaces()

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.main_layout.addWidget(self.buttons)

        # Переключаем страницы при изменении выбора в комбобоксе
        self.type_combo.currentIndexChanged.connect(self.pages.setCurrentIndex)
        self.adjustSize()

    def load_workspaces(self):
        for typ, (title, cls) in CAMERA_CONFIG_REGISTRY.items():
            self._create_item(title, typ, cls)

    def _create_item(self, title, typ, cls):

        self.type_combo.addItem(title, typ)
        widget_instance = cls()
        self.pages.addWidget(widget_instance)

    def get_camera_config(self) -> dict:
        cam_type = self.type_combo.currentData()

        config = self.pages.currentWidget().get_values()

        config["type"] = cam_type
        return config
