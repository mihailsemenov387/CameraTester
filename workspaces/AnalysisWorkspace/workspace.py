from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QDockWidget, QMainWindow

from utils.Classes.Plotter import Plotter
from utils.Signals import GlobalBus
from utils.SpecialFunctions.AnalysysFun import (
    _get_base_profiles,
    estimate_contrast_params,
    process,
    process_contrast,
    process_contrast_normalized,
    process_many,
)
from workspaces.AbstractWorkspace import AbstractWorkspace, register_workspace

from .AnalysisSettingsWidget import AnalysisSettingsWidget


@register_workspace(title="Анализ профиля")
class AnalysisWorkspace(AbstractWorkspace):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Анализ")
        self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowTabbedDocks)

        self.current_mode = 0
        self.analysis_enabled = True
        self.contrast_enabled = False
        self.norm_contrast_enabled = False
        self.norm_window = 3
        self.norm_step = 200
        self.latest_frame = None
        self.latest_cam_name = None
        self._is_new_frame = False

        self.analysis_timer = QTimer()
        self.analysis_timer.timeout.connect(self._do_analysis_step)
        self.plotter = Plotter()
        self.setCentralWidget(self.plotter)

        self.dock_math = QDockWidget("Параметры анализа", self)
        self.settings_ui = AnalysisSettingsWidget()
        self.dock_math.setWidget(self.settings_ui)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_math)

        self.settings_ui.speed_changed.connect(self.analysis_timer.setInterval)
        self.analysis_timer.start(self.settings_ui.speed_spin.value())
        self.settings_ui.mode_changed.connect(self._update_mode)
        self.settings_ui.analysis_enabled.connect(self._on_analysis_enabled)
        self.settings_ui.contrast_enabled.connect(self._on_contrast_enabled)
        self.settings_ui.norm_contrast_enabled.connect(self._on_norm_contrast_enabled)
        self.settings_ui.norm_contrast_window.connect(self._set_norm_window)
        self.settings_ui.norm_contrast_step.connect(self._set_norm_step)
        self.settings_ui.auto_params_requested.connect(self._auto_contrast_params)

        # ceckbox for inner plotter logic
        # self.settings_ui.is_draw_lines_on_plot.toggled.connect(self.plotter.update_line_vis)
        # self.plotter.intensity_calculated.connect(GlobalBus.instance().max_intensity_found.emit)

        self.settings_ui.is_draw_lines_on_plot.toggled.connect(
            self.plotter.update_line_vis
        )
        self.settings_ui.reset_focus_btn.clicked.connect(
            self.plotter.reset_best
        )  # reset plotter limits
        self.plotter.intensity_calculated.connect(
            self.settings_ui._update_focus_indicators
        )

        GlobalBus.instance().frame_to_use.connect(self._buffer_frame)

    # do case switch
    def _update_mode(self, mode):
        self.current_mode = mode
        self.plotter.update_is_draw(mode != 0)
        if mode == 0:
            self.plotter.clear_canvas()
            # Чтобы фит не оставался висеть на видео при переключении
            GlobalBus.instance().analysis_cleared.emit()

    def _on_analysis_enabled(self, enabled):
        self.analysis_enabled = enabled
        if enabled:
            self.analysis_timer.start(self.settings_ui.speed_spin.value())
        else:
            self.analysis_timer.stop()
            self.latest_frame = None
            self._is_new_frame = False
            self.plotter.clear_canvas()
            GlobalBus.instance().analysis_cleared.emit()

    def _on_contrast_enabled(self, enabled):
        self.contrast_enabled = enabled
        self.plotter.set_contrast_mode(enabled)

    def _on_norm_contrast_enabled(self, enabled):
        self.norm_contrast_enabled = enabled

    def _set_norm_window(self, value):
        self.norm_window = value

    def _set_norm_step(self, value):
        self.norm_step = value

    def _auto_contrast_params(self):
        """Кнопка «Авто»: подбирает окно/шаг норм. контраста по текущему кадру."""
        if self.latest_frame is None:
            return
        base = _get_base_profiles(self.latest_frame)
        if not base:
            return
        _, _, _, x_w, y_w = base
        window, step = estimate_contrast_params(x_w, y_w)
        self.norm_window = window
        self.norm_step = step
        self.settings_ui.set_norm_params(window, step)
        print(f"[DEBUG] авто параметры контраста: окно={window}, шаг={step}")

    def _buffer_frame(self, cam_name, frame):
        if not self.analysis_enabled:
            return
        if cam_name != self.latest_cam_name:
            self.latest_cam_name = cam_name
            self.settings_ui.set_camera(cam_name)
        self.latest_frame = frame
        self._is_new_frame = True

    def _do_analysis_step(self):
        if self.latest_frame is None or not self._is_new_frame:
            return
        self._is_new_frame = False

        frame = self.latest_frame
        mode = self.current_mode
        want_deriv = self.contrast_enabled
        want_norm = self.norm_contrast_enabled

        # Базовые профили нужны режиму «только профили» и контрасту —
        # считаем один раз и переиспользуем во всех функциях.
        need_base = want_deriv or want_norm or mode == 0
        base = _get_base_profiles(frame) if need_base else None
        if need_base and base is None:
            return

        # Фит считаем в режимах 1/2: он нужен и для оверлея («фит на главном
        # выходе»), и как источник производной/нормированного контраста.
        fit_res = None
        if mode == 1:
            fit_res = process(frame, base=base)
            if fit_res:
                GlobalBus.instance().analysis_results_sent.emit(
                    self.latest_cam_name, fit_res
                )
        elif mode == 2:
            fit_res = process_many(frame, base=base)
            if fit_res:
                GlobalBus.instance().analysis_many_results_sent.emit(
                    self.latest_cam_name, fit_res
                )

        # Собираем то, что показываем на графиках.
        data = {}
        if want_deriv:
            c = process_contrast(frame, base=base, fit_result=fit_res)
            if c:
                data.update(c)
        if want_norm:
            n = process_contrast_normalized(
                frame,
                base=base,
                fit_result=fit_res,
                window=self.norm_window,
                step=self.norm_step,
            )
            if n:
                data.update(n)

        # Если контраст не включён — показываем результат фита,
        # а без фита («только профили») — сырые профили.
        if not data:
            if fit_res:
                data.update(fit_res)
            elif base:
                _, x, y, x_w, y_w = base
                data.update({"x": x, "y": y, "x_raw": x_w, "y_raw": y_w})

        if data:
            self.plotter.update_data(data)

    def shutdown(self):
        self.analysis_timer.stop()
