from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from utils.Signals import GlobalBus


class AnalysisSettingsWidget(QWidget):
    speed_changed = Signal(int)
    mode_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Выключено", 0)
        self.mode_combo.addItem("Одиночный Гаусс", 1)
        self.mode_combo.addItem("Много пиков (MTF)", 2)

        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)

        # 2. Группа отрисовки (Оверлей)
        self.is_draw_fit = QCheckBox("Отоброзить фит на главном выходе")
        self.is_draw_fit.toggled.connect(GlobalBus.instance().is_draw_fit.emit)

        # Спинбокс
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(50, 2000)
        self.speed_spin.setSuffix(" ms")
        self.speed_spin.setValue(200)
        self.speed_spin.valueChanged.connect(self.speed_changed.emit)

        # Компонуем
        layout.addWidget(QLabel("<b>АЛГОРИТМ</b>"))
        layout.addWidget(self.mode_combo)
        layout.addWidget(QLabel("<b>ВИЗУАЛИЗАЦИЯ</b>"))
        layout.addWidget(self.is_draw_fit)
        layout.addWidget(QLabel("<b>ТАЙМИНГ</b>"))
        layout.addWidget(self.speed_spin)
        layout.addStretch()

        self._on_mode_changed()

    def _on_mode_changed(self):
        current_mode = self.mode_combo.currentData()

        self.mode_changed.emit(current_mode)

        need_draw_cross = current_mode == 1
        GlobalBus.instance().is_draw_cross.emit(need_draw_cross)
