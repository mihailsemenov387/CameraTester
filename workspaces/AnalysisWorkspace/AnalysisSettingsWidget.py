# from PySide6.QtCore import Qt, Signal
# from PySide6.QtWidgets import (
#     QCheckBox,
#     QComboBox,
#     QLabel,
#     QSpinBox,
#     QVBoxLayout,
#     QWidget,
# )

# from utils.Signals import GlobalBus


# class AnalysisSettingsWidget(QWidget):
#     speed_changed = Signal(int)
#     mode_changed = Signal(int)

#     def __init__(self, parent=None):
#         super().__init__(parent)
#         layout = QVBoxLayout(self)
#         layout.setContentsMargins(10, 10, 10, 10)

#         self.mode_combo = QComboBox()
#         self.mode_combo.addItem("Выключено", 0)
#         self.mode_combo.addItem("Одиночный Гаусс", 1)
#         self.mode_combo.addItem("Много гауссов)", 2)

#         self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)

#         self.is_draw_fit = QCheckBox("Отоброзить фит на главном выходе")
#         self.is_draw_fit.toggled.connect(GlobalBus.instance().is_draw_fit.emit)

#         #TODO: add ceckbox for line draw
#         self.is_draw_lines_on_plot= QCheckBox("Отоброзить Линии на графике")



#         self.speed_spin = QSpinBox()
#         self.speed_spin.setRange(50, 2000)
#         self.speed_spin.setSuffix(" ms")
#         self.speed_spin.setValue(200)
#         self.speed_spin.valueChanged.connect(self.speed_changed.emit)

#         layout.addWidget(QLabel("<b>Обработка:</b>"))
#         layout.addWidget(self.mode_combo)
#         layout.addWidget(self.is_draw_fit)
#         layout.addWidget(QLabel("<b>Скорость обновления рассчетов</b>"))
#         layout.addWidget(self.speed_spin)
#         layout.addStretch()

#         self._on_mode_changed()

#     def _on_mode_changed(self):
#         current_mode = self.mode_combo.currentData()

#         self.mode_changed.emit(current_mode)

#         need_draw_cross = current_mode == 1
#         GlobalBus.instance().is_draw_cross.emit(need_draw_cross)

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QPushButton
)

from utils.Signals import GlobalBus



class AnalysisSettingsWidget(QWidget):
    speed_changed = Signal(int)
    mode_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Переменные для хранения наилучшего (максимального) фокуса за всё время
        self._best_x = 0.0
        self._best_y = 0.0

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Выключено", 0)
        self.mode_combo.addItem("Одиночный Гаусс", 1)
        self.mode_combo.addItem("Много гауссов)", 2)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)

        self.is_draw_fit = QCheckBox("Отобразить фит на главном выходе")
        self.is_draw_fit.toggled.connect(GlobalBus.instance().is_draw_fit.emit)

        self.is_draw_lines_on_plot = QCheckBox("Отобразить линии на графике")

        # --- БЛОК ФОКУСИРОВКИ ---
        layout.addWidget(QLabel("<b>Настройка фокуса (Интенсивность):</b>"))

        # Метки для текущих значений
        self.current_focus_label = QLabel("Текущая X: — | Y: —")
        layout.addWidget(self.current_focus_label)

        # Метки для рекордов (лучшего фокуса)
        self.best_focus_label = QLabel("Лучшая  X: — | Y: —")
        self.best_focus_label.setStyleSheet("color: green; font-weight: bold;")
        layout.addWidget(self.best_focus_label)

        # Кнопка сброса рекордов (чтобы начать настройку заново)
        self.reset_focus_btn = QPushButton("Сбросить рекорд фокуса")
        self.reset_focus_btn.clicked.connect(self._reset_focus_records)
        layout.addWidget(self.reset_focus_btn)

        # Подключаем сигнал из шины
        # GlobalBus.instance().max_intensity_found.connect(self._update_focus_indicators)
        # ------------------------

        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(50, 2000)
        self.speed_spin.setSuffix(" ms")
        self.speed_spin.setValue(200)
        self.speed_spin.valueChanged.connect(self.speed_changed.emit)

        layout.addWidget(QLabel("<b>Обработка:</b>"))
        layout.addWidget(self.mode_combo)
        layout.addWidget(self.is_draw_fit)
        layout.addWidget(self.is_draw_lines_on_plot)
        layout.addWidget(QLabel("<b>Скорость обновления расчетов</b>"))
        layout.addWidget(self.speed_spin)
        layout.addStretch()

        self._on_mode_changed()

    def _on_mode_changed(self):
        current_mode = self.mode_combo.currentData()
        self.mode_changed.emit(current_mode)

        need_draw_cross = current_mode == 1
        GlobalBus.instance().is_draw_cross.emit(need_draw_cross)

        is_processing_active = current_mode != 0
        self.is_draw_lines_on_plot.setEnabled(is_processing_active)
        self.reset_focus_btn.setEnabled(is_processing_active)

        if not is_processing_active:
            if self.is_draw_lines_on_plot.isChecked():
                self.is_draw_lines_on_plot.setChecked(False)
            self._reset_focus_records()

    def _reset_focus_records(self):
        """Сбрасывает накопленные рекорды интенсивности"""
        self._best_x = 0.0
        self._best_y = 0.0
        self.current_focus_label.setText("Текущая X: — | Y: —")
        self.best_focus_label.setText("Лучшая  X: — | Y: —")

    def _update_focus_indicators(self, intensity_x: float, intensity_y: float):
        """Слот принимает чистые значения максимальной интенсивности для фокуса"""
        if not self.is_draw_lines_on_plot.isChecked():
            return

        # Обновляем рекорды интенсивности (высоты пика)
        if intensity_x > self._best_x:
            self._best_x = intensity_x
        if intensity_y > self._best_y:
            self._best_y = intensity_y

        # Выводим «попугаи» интенсивности на экран
        self.current_focus_label.setText(f"Текущая Интенс. X: {intensity_x:.1f} | Y: {intensity_y:.1f}")
        self.best_focus_label.setText(f"Лучшая Интенс.  X: {self._best_x:.1f} | Y: {self._best_y:.1f}")
