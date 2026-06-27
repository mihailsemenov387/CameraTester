from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QDockWidget, QMainWindow

from utils.Classes.Plotter import Plotter
from utils.Signals import GlobalBus
from utils.SpecialFunctions.AnalysysFun import process
from workspaces.AbstractWorkspace import AbstractWorkspace

from .AnalysisSettingsWidget import AnalysisSettingsWidget


class AnalysisWorkspace(AbstractWorkspace):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Аналитика")
        self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowTabbedDocks)

        # Буфер для хранения последнего пришедшего кадра
        self.latest_frame = None
        self.latest_cam_name = None

        # --- 1. ТАЙМЕР (Вот он будет реально юзать время из настроек) ---
        self.analysis_timer = QTimer()
        self.analysis_timer.timeout.connect(self._perform_analysis)

        # --- 2. ЦЕНТР И ДОКИ ---
        self.plotter = Plotter()
        self.setCentralWidget(self.plotter)

        self.dock_math = QDockWidget("Параметры анализа", self)
        self.settings_ui = AnalysisSettingsWidget()
        self.dock_math.setWidget(self.settings_ui)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_math)

        # --- 3. СВЯЗИ ---
        # Подписываемся на настройки (интервал и вкл/выкл)
        self.settings_ui.speed_changed.connect(self.analysis_timer.setInterval)
        self.settings_ui.enabled_changed.connect(self._toggle_timer)

        # Подписываемся на шину (просто сохраняем кадр в буфер, НЕ считаем сразу!)
        GlobalBus.instance().raw_frame_sent.connect(self._buffer_frame)

    def _buffer_frame(self, cam_name, frame):
        """Просто запоминаем последний кадр. Это происходит мгновенно."""
        self.latest_frame = frame
        self.latest_cam_name = cam_name

    def _toggle_timer(self, enabled):
        if enabled:
            # Берем значение из спинбокса и запускаем
            interval = self.settings_ui.speed_spin.value()
            self.analysis_timer.start(interval)
        else:
            self.analysis_timer.stop()

    def _perform_analysis(self):
        """Эта функция вызывается ТАЙМЕРОМ (например, раз в 200мс)"""
        if self.latest_frame is None:
            return

        # Тяжелый расчет Гаусса запускается только здесь!
        res = process(self.latest_frame)

        if res:
            # 1. Обновляем графики
            self.plotter.update_data(res)
            # 2. Кидаем результаты обратно в шину для отрисовки оверлея на камере
            GlobalBus.instance().analysis_results_sent.emit(self.latest_cam_name, res)

        # Очищаем буфер, чтобы не считать одно и то же, если камера тормозит
        # self.latest_frame = None

    def shutdown(self):
        """Реализация интерфейса: гасим таймер анализа"""
        if hasattr(self, "analysis_timer"):
            self.analysis_timer.stop()
        print("Таймер анализа остановлен.")
