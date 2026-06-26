from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDockWidget,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class AnalysisSettingsWidget(QDockWidget):
    speed_changed = Signal(int)
    enabled_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__("Параметры анализа", parent)
        # Разрешаем крепить только СЛЕВА или СПРАВА
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )

        container = QWidget()
        layout = QVBoxLayout(container)

        self.enable_cb = QCheckBox("Включить расчет Гаусса")
        self.enable_cb.setChecked(False)
        self.enable_cb.toggled.connect(self.enabled_changed.emit)

        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(50, 2000)
        self.speed_spin.setSuffix(" ms")
        self.speed_spin.setValue(200)
        self.speed_spin.valueChanged.connect(self.speed_changed.emit)

        layout.addWidget(self.enable_cb)
        layout.addWidget(QLabel("Период обновления:"))
        layout.addWidget(self.speed_spin)
        layout.addStretch()

        container.setLayout(layout)
        self.setWidget(container)
