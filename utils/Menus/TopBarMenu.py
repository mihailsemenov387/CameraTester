from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
)

from utils.Classes.CameraRegistry import CAMERA_REGISTRY

# Импорт обязателен: здесь конфиг-страницы регистрируются в CAMERA_REGISTRY
from . import CameraTypeConfig  # noqa: F401


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

        self.load_camera_config_page()

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.main_layout.addWidget(self.buttons)

        # Переключаем страницы при изменении выбора в комбобоксе
        self.type_combo.currentIndexChanged.connect(self.pages.setCurrentIndex)
        self.adjustSize()

    def load_camera_config_page(self):
        for entry in CAMERA_REGISTRY.values():
            if not entry.is_complete():
                continue
            self._create_item(entry.title, entry.typ, entry.config_cls)

    def _create_item(self, title, typ, cls):

        self.type_combo.addItem(title, typ)
        widget_instance = cls()
        self.pages.addWidget(widget_instance)

    def get_camera_config(self) -> dict:
        cam_type = self.type_combo.currentData()

        config = self.pages.currentWidget().get_values()

        config["type"] = cam_type
        return config
