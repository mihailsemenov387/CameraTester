from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from utils.Classes.Plotter import Plotter


class AnalysisToolWidget(QDockWidget):
    # Сигналы для общения с Главным окном
    speed_changed = Signal(int)
    enabled_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__("Утилита: Анализ пучка", parent)
        # Позволяем отрывать окно и таскать куда угодно
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )

        container = QWidget()
        layout = QVBoxLayout(container)

        # --- ПАНЕЛЬ УПРАВЛЕНИЯ АНАЛИЗОМ ---
        controls_layout = QHBoxLayout()

        self.enable_cb = QCheckBox("Включить расчет")
        self.enable_cb.setChecked(False)  # По умолчанию выключено, чтобы не грузить ПК
        self.enable_cb.toggled.connect(self.enabled_changed.emit)

        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(50, 2000)
        self.speed_spin.setSuffix(" ms")
        self.speed_spin.setValue(200)
        self.speed_spin.valueChanged.connect(self.speed_changed.emit)

        controls_layout.addWidget(self.enable_cb)
        controls_layout.addSpacing(20)
        controls_layout.addWidget(QLabel("Интервал обновления:"))
        controls_layout.addWidget(self.speed_spin)
        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # --- ПЛОТТЕР (ГРАФИКИ) ---
        self.plotter = Plotter()
        layout.addWidget(self.plotter)

        self.setWidget(container)

    def update_plots(self, results):
        """Обновляет графики, только если панель активна"""
        if self.enable_cb.isChecked():
            self.plotter.update_data(results)

    def clear_plots(self):
        """Здесь можно добавить очистку графиков при выключении"""
        pass
