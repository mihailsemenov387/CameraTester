from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from utils.Classes.AbstractCamera import AbstractCamera


class CameraSettingsWidget(QDockWidget):
    def __init__(self, camera: AbstractCamera):
        super().__init__("Настройки камеры")
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)

        settings_widget = QWidget()
        self.layout = QVBoxLayout()

        self.add_slider(
            "Экспозиция:", -10, 0, -5, camera.set_exposure, camera.set_auto_exposure
        )
        self.add_slider("Gamma:", 90, 150, 100, camera.set_gamma)
        self.add_slider("Gain:", 4, 8, 1, camera.set_gain)
        self.add_slider("Contrast:", 0, 255, 127, camera.set_contrast)
        self.add_slider("Brightness:", -127, 127, 0, camera.set_brightness)

        self.layout.addStretch()
        settings_widget.setLayout(self.layout)
        self.setWidget(settings_widget)

    def add_slider(
        self, label_text, min_val, max_val, start_val, connect_func, auto_func=None
    ):
        row_layout = QHBoxLayout()

        label = QLabel(label_text)
        label.setMinimumWidth(80)
        row_layout.addWidget(label)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(start_val)

        spinbox = QSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(start_val)
        spinbox.setFixedWidth(50)

        slider.valueChanged.connect(spinbox.setValue)
        spinbox.valueChanged.connect(slider.setValue)
        slider.valueChanged.connect(connect_func)

        row_layout.addWidget(slider)
        row_layout.addWidget(spinbox)

        if auto_func:
            auto_cb = QCheckBox("Авто")
            auto_cb.toggled.connect(slider.setDisabled)
            auto_cb.toggled.connect(spinbox.setDisabled)
            auto_cb.toggled.connect(auto_func)
            row_layout.addWidget(auto_cb)
        else:
            spacer = QWidget()
            spacer.setFixedWidth(55)
            row_layout.addWidget(spacer)

        self.layout.addLayout(row_layout)
