from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from utils.Classes.AbstractCamera import AbstractCamera, CameraParameter


class CameraSettingsWidget(QWidget):
    def __init__(self, camera: AbstractCamera):
        super().__init__()
        self.camera = camera

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)

        self.loading_label = QLabel("Ожидание подключения камеры...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.loading_label)

    def setup_ui(self):
        self.main_layout.removeWidget(self.loading_label)
        self.loading_label.deleteLater()
        self.loading_label = None

        self.parameters = self.camera.get_parameters()

        for param_id, param in self.parameters.items():
            self._build_parameter(param)

        self.main_layout.addStretch()

    def _build_parameter(self, param: CameraParameter):
        row_layout = QHBoxLayout()

        label = QLabel(param.label)
        label.setMinimumWidth(80)
        row_layout.addWidget(label)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(param.min_value, param.max_value)
        slider.setValue(param.current_value)

        spinbox = QSpinBox()
        spinbox.setRange(param.min_value, param.max_value)
        spinbox.setValue(param.current_value)
        spinbox.setFixedWidth(50)

        slider.valueChanged.connect(spinbox.setValue)
        spinbox.valueChanged.connect(slider.setValue)
        slider.valueChanged.connect(param.setter)

        row_layout.addWidget(slider)
        row_layout.addWidget(spinbox)

        if param.has_auto and param.auto_setter:
            auto_cb = QCheckBox("Авто")
            auto_cb.toggled.connect(slider.setDisabled)
            auto_cb.toggled.connect(spinbox.setDisabled)
            auto_cb.toggled.connect(param.auto_setter)
            row_layout.addWidget(auto_cb)
        else:
            spacer = QWidget()
            spacer.setFixedWidth(55)
            row_layout.addWidget(spacer)

        self.main_layout.addLayout(row_layout)
