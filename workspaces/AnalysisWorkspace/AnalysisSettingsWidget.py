from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from utils.Signals import GlobalBus


class AnalysisSettingsWidget(QWidget):
    speed_changed = Signal(int)
    mode_changed = Signal(int)
    analysis_enabled = Signal(bool)
    contrast_enabled = Signal(bool)
    norm_contrast_enabled = Signal(bool)
    norm_contrast_window = Signal(int)
    norm_contrast_step = Signal(int)
    auto_params_requested = Signal()

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
        layout.addWidget(QLabel("<b>Интенсивность:</b>"))

        # Метки для текущих значений
        self.current_focus_label = QLabel("I X: | Y: ")
        layout.addWidget(self.current_focus_label)

        # Метки для рекордов (лучшего фокуса)
        self.best_focus_label = QLabel("max I  X:  | Y: ")
        self.best_focus_label.setStyleSheet("color: green; font-weight: bold;")
        layout.addWidget(self.best_focus_label)

        # Кнопка сброса рекордов (чтобы начать настройку заново)
        self.reset_focus_btn = QPushButton("Сбросить максимум")
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
        self.analysis_cb = QCheckBox("Анализ")
        self.analysis_cb.setChecked(True)
        self.analysis_cb.toggled.connect(self.analysis_enabled.emit)
        layout.addWidget(self.analysis_cb)
        layout.addWidget(self.mode_combo)

        self.contrast_cb = QCheckBox("Контраст (производная)")
        self.contrast_cb.setChecked(False)
        self.contrast_cb.toggled.connect(self.contrast_enabled.emit)
        layout.addWidget(self.contrast_cb)

        self.norm_cb = QCheckBox("Норм. контраст (Майкельсон)")
        self.norm_cb.setChecked(False)
        self.norm_cb.toggled.connect(self.norm_contrast_enabled.emit)
        self.norm_cb.toggled.connect(self._on_norm_toggled)
        layout.addWidget(self.norm_cb)

        self.norm_window_spin = QSpinBox()
        self.norm_window_spin.setRange(1, 200)
        self.norm_window_spin.setValue(3)
        self.norm_window_spin.setSuffix(" px")
        self.norm_window_spin.valueChanged.connect(self.norm_contrast_window.emit)

        self.norm_step_spin = QSpinBox()
        self.norm_step_spin.setRange(1, 100000)
        self.norm_step_spin.setValue(200)
        self.norm_step_spin.setSuffix(" px")
        self.norm_step_spin.valueChanged.connect(self.norm_contrast_step.emit)

        self.auto_params_btn = QPushButton("Авто")
        self.auto_params_btn.setToolTip(
            "Подобрать окно и шаг автоматически по текущему кадру"
        )
        self.auto_params_btn.clicked.connect(self.auto_params_requested.emit)

        norm_row = QHBoxLayout()
        norm_row.addWidget(QLabel("Окно:"))
        norm_row.addWidget(self.norm_window_spin)
        norm_row.addWidget(QLabel("Шаг:"))
        norm_row.addWidget(self.norm_step_spin)
        norm_row.addWidget(self.auto_params_btn)
        layout.addLayout(norm_row)
        self._on_norm_toggled(False)
        layout.addWidget(self.is_draw_fit)
        layout.addWidget(self.is_draw_lines_on_plot)
        layout.addWidget(QLabel("<b>Скорость обновления расчетов</b>"))
        layout.addWidget(self.speed_spin)
        layout.addStretch()

        self._on_mode_changed()

    def _on_norm_toggled(self, enabled):
        self.norm_window_spin.setEnabled(enabled)
        self.norm_step_spin.setEnabled(enabled)

    def set_norm_params(self, window, step):
        """Устанавливает окно/шаг (значения уже подобраны автоматически)."""
        self.norm_window_spin.setValue(window)
        self.norm_step_spin.setValue(step)

    def _on_mode_changed(self):
        current_mode = self.mode_combo.currentData()
        self.mode_changed.emit(current_mode)

        need_draw_cross = current_mode != 0
        GlobalBus.instance().is_draw_cross.emit(need_draw_cross)

        # is_processing_active = current_mode != 0
        # self.is_draw_lines_on_plot.setEnabled(is_processing_active)
        # self.reset_focus_btn.setEnabled(is_processing_active)

        # if not is_processing_active:
        #     if self.is_draw_lines_on_plot.isChecked():
        #         #FIXME: temp
        #         pass
        #         self.is_draw_lines_on_plot.setChecked(False)
        #     self._reset_focus_records()

    def _reset_focus_records(self):
        """Сбрасывает накопленные рекорды интенсивности"""
        self._best_x = 0.0
        self._best_y = 0.0
        self.current_focus_label.setText("I X:   | Y:  ")
        self.best_focus_label.setText("max I  X:  | Y:  ")

    def _update_focus_indicators(self, intensity_x: float, intensity_y: float):
        """Слот принимает чистые значения максимальной интенсивности для фокуса"""
        # Обновляем рекорды интенсивности (высоты пика)
        if intensity_x > self._best_x:
            self._best_x = intensity_x
        if intensity_y > self._best_y:
            self._best_y = intensity_y

        # Выводим «попугаи» интенсивности на экран
        self.current_focus_label.setText(
            f"I. X: {intensity_x:.1f} | Y: {intensity_y:.1f}"
        )
        self.best_focus_label.setText(
            f"max I  X: {self._best_x:.1f} | Y: {self._best_y:.1f}"
        )
