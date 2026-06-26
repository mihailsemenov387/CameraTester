from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMainWindow,
    QStackedWidget,  # Переключатель панелей
    QVBoxLayout,
)

from utils.Widgets.CameraTypeConfig import RTSPConfigPage, UVCConfigPage


class CameraSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Подключение")

        main_layout = QVBoxLayout(self)

        # 1. Выбор типа
        self.type_combo = QComboBox()
        self.type_combo.addItem("USB Camera", "UVC")
        self.type_combo.addItem("RTSP Stream", "RTSP")
        main_layout.addWidget(QLabel("Тип:"))
        main_layout.addWidget(self.type_combo)

        # 2. Стек из наших новых виджетов
        self.pages = QStackedWidget()
        self.uvc_page = UVCConfigPage()
        self.rtsp_page = RTSPConfigPage()

        self.pages.addWidget(self.uvc_page)  # Индекс 0
        self.pages.addWidget(self.rtsp_page)  # Индекс 1
        main_layout.addWidget(self.pages)

        # Кнопки
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        main_layout.addWidget(self.buttons)

        # При смене типа в комбобоксе - меняем страницу в стеке
        self.type_combo.currentIndexChanged.connect(self.pages.setCurrentIndex)

    def get_camera_config(self) -> dict:
        # Получаем тип (UVC или RTSP)
        cam_type = self.type_combo.currentData()

        # Просто берем значения из ТЕКУЩЕЙ активной страницы
        config = self.pages.currentWidget().get_values()

        # Добавляем тип в словарь и возвращаем
        config["type"] = cam_type
        return config
