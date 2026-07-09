from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QDockWidget, QMainWindow

from utils.Classes.Plotter import Plotter
from utils.Signals import GlobalBus
from utils.SpecialFunctions.AnalysysFun import process, process_many
from workspaces.AbstractWorkspace import AbstractWorkspace, register_workspace

from .AnalysisSettingsWidget import AnalysisSettingsWidget


@register_workspace(title="Аналитика профиля")
class AnalysisWorkspace(AbstractWorkspace):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Аналитика")
        self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowTabbedDocks)

        self.current_mode = 0
        self.latest_frame = None
        self.latest_cam_name = None

        self.analysis_timer = QTimer()
        self.analysis_timer.timeout.connect(self._do_analysis_step)
        self.plotter = Plotter()
        self.setCentralWidget(self.plotter)

        self.dock_math = QDockWidget("Параметры анализа", self)
        self.settings_ui = AnalysisSettingsWidget()
        self.dock_math.setWidget(self.settings_ui)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_math)

        self.settings_ui.speed_changed.connect(self.analysis_timer.setInterval)
        self.settings_ui.mode_changed.connect(self._update_mode)

        # ceckbox for inner plotter logic
        # self.settings_ui.is_draw_lines_on_plot.toggled.connect(self.plotter.update_line_vis)
        # self.plotter.intensity_calculated.connect(GlobalBus.instance().max_intensity_found.emit)

        self.settings_ui.is_draw_lines_on_plot.toggled.connect(self.plotter.update_line_vis)
        self.plotter.intensity_calculated.connect(self.settings_ui._update_focus_indicators)

        GlobalBus.instance().raw_frame_sent.connect(self._buffer_frame)

    # do case switch
    def _update_mode(self, mode):
        self.current_mode = mode
        self.plotter.update_is_draw(mode != 0 )
        if mode == 0:
            self.analysis_timer.stop()
        else:
            self.analysis_timer.start(self.settings_ui.speed_spin.value())

    def _buffer_frame(self, cam_name, frame):
        self.latest_frame = frame
        self.latest_cam_name = cam_name

    def _toggle_timer(self, enabled):
        if enabled:
            interval = self.settings_ui.speed_spin.value()
            self.analysis_timer.start(interval)
        else:
            self.analysis_timer.stop()

    # TODO: add unified interface for send/recive analysis results
    def _do_analysis_step(self):
        if self.latest_frame is None:
            return

        if self.current_mode == 1:
            res = process(self.latest_frame)
            if res:
                self.plotter.update_data(res)
                GlobalBus.instance().analysis_results_sent.emit(
                    self.latest_cam_name, res
                )

        elif self.current_mode == 2:
            res = process_many(self.latest_frame)
            if res:
                self.plotter.update_data(res)
                GlobalBus.instance().analysis_many_results_sent.emit(
                    self.latest_cam_name, res
                )

    def shutdown(self):
        self.analysis_timer.stop()
