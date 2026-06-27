from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
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

        # 1. Группа выбора режима (Расчет)
        self.enable_cb = QCheckBox("Расчет: Одиночный Гаусс")
        self.enable_cb_many = QCheckBox("Расчет: Много пиков (MTF)")
        


        
        # 2. Группа отрисовки (Оверлей)
        self.single_gauss_cb = QCheckBox("Отрисовка: Одиночный")
        self.many_gauss_cb = QCheckBox("Отрисовка: Много пиков")

        # 3. Настройка логики исключения (чтобы не включить оба сразу)
        self.enable_cb.toggled.connect(self._on_single_toggled)
        self.enable_cb_many.toggled.connect(self._on_many_toggled)

        # 4. Прокидываем сигналы в шину для оверлеев
        self.single_gauss_cb.toggled.connect(GlobalBus.instance().draw_single_gauss.emit)
        self.many_gauss_cb.toggled.connect(GlobalBus.instance().draw_many_gauss.emit)

        # Спинбокс
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(50, 2000)
        self.speed_spin.setSuffix(" ms")
        self.speed_spin.setValue(200)
        self.speed_spin.valueChanged.connect(self.speed_changed.emit)

        # Компонуем
        layout.addWidget(QLabel("<b>МАТЕМАТИКА</b>"))
        layout.addWidget(self.enable_cb)
        layout.addWidget(self.enable_cb_many)
        layout.addWidget(QLabel("<b>ВИЗУАЛИЗАЦИЯ</b>"))
        layout.addWidget(self.single_gauss_cb)
        layout.addWidget(self.many_gauss_cb)
        layout.addWidget(QLabel("<b>ТАЙМИНГ</b>"))
        layout.addWidget(self.speed_spin)
        layout.addStretch()

    def _on_single_toggled(self, checked):
        if checked:
            # Если включаем сингл - выключаем режим "много"
            self.enable_cb_many.setChecked(False)
            self.mode_changed.emit(1)
        elif not self.enable_cb_many.isChecked():
            # Если оба выключены
            self.mode_changed.emit(0)

    def _on_many_toggled(self, checked):
        if checked:
            # Если включаем много - выключаем сингл
            self.enable_cb.setChecked(False)
            self.mode_changed.emit(2)
        elif not self.enable_cb.isChecked():
            self.mode_changed.emit(0)
