from harvesters.core import Harvester
from PySide6.QtCore import QTimer
from PySide6.QtMultimedia import QMediaDevices
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
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
        layout.addStretch()
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
        layout.addStretch()

    def get_values(self):
        return {"url": self.url_input.text(), "name": "IP Camera"}


@register_congig_page("Harvester camera", "HARVESTER")
class HarvesterConfigPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QFormLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Поле для пути к .cti
        self.cti_input = QLineEdit()
        self.cti_input.setPlaceholderText("Выберите файл .cti драйвера")

        self.browse_btn = QPushButton("Обзор...")
        self.browse_btn.clicked.connect(self._browse_cti)

        # НОВОЕ: Комбобокс для выбора конкретной камеры
        self.camera_select = QComboBox()
        self.camera_select.addItem("Сначала выберите .cti файл", None)
        self.camera_select.setDisabled(True)

        layout.addRow("Драйвер:", self.cti_input)
        layout.addRow("", self.browse_btn)
        layout.addRow("Камера:", self.camera_select)

    def _browse_cti(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите GenTL драйвер (.cti)",
            "C:\\Program Files",
            "GenTL Producers (*.cti)",
        )
        if file_path:
            self.cti_input.setText(file_path)
            # Как только файл выбран — запускаем сканирование камер!
            self._scan_cameras(file_path)

    def _scan_cameras(self, cti_path):
        """Временный запуск Harvester для поиска всех доступных камер"""
        self.camera_select.clear()
        try:
            h = Harvester()
            h.add_file(cti_path)
            h.update()

            if len(h.device_info_list) == 0:
                self.camera_select.addItem("Камеры не найдены", None)
                self.camera_select.setDisabled(True)
                return

            # Заполняем комбобокс найденными камерами
            for dev in h.device_info_list:
                # Отображаем модель и серийник, а внутрь (в userData) сохраняем только серийник
                display_name = f"{dev.model} ({dev.serial_number})"
                self.camera_select.addItem(display_name, dev.serial_number)

            self.camera_select.setDisabled(False)
            h.reset()  # Обязательно освобождаем драйвер!

        except Exception as e:
            self.camera_select.addItem("Ошибка сканирования драйвера", None)
            self.camera_select.setDisabled(True)

    def get_values(self) -> dict:
        # Получаем серийный номер выбранной в списке камеры
        selected_serial = self.camera_select.currentData()

        return {
            "name": self.camera_select.currentText()
            if selected_serial
            else "Harvester Cam",
            "cti_path": self.cti_input.text(),
            "serial": selected_serial,  # Передаем строгий серийник в фабрику
        }
