import cv2
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QDockWidget, QMainWindow, QVBoxLayout

from utils.Classes.AbstractCamera import CameraThread
from utils.Signals import GlobalBus
from utils.Widgets.ROIWidget import ROIWidget
from utils.Widgets.VideoOverlayWidget import VideoOverlayWidget
from workspaces.AbstractWorkspace import AbstractWorkspace

from .CameraSettingsWidget import CameraSettingsWidget


class CameraWorkspace(AbstractWorkspace):
    def __init__(self, camera_obj, name=None):
        super().__init__()

        self.cam_name = name or "Cam name doesnt set in camera config!"

        print(f"[DEBUG] connected to {self.cam_name}")
        self.thread = CameraThread(camera_obj, self.cam_name)

        self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowTabbedDocks)

        ws_menu = self.menuBar()
        self.view_menu = ws_menu.addMenu("Настройки")

        self.video_container = ROIWidget()
        self.overlay = VideoOverlayWidget()
        self.overlay.set_base(self.video_container)
        ov_layout = QVBoxLayout(self.video_container)
        ov_layout.setContentsMargins(0, 0, 0, 0)
        ov_layout.addWidget(self.overlay)
        self.setCentralWidget(self.video_container)

        self.is_draw_fit = False

        # ------------ new settings init ---------
        self.dock_hw = QDockWidget("Настройки камеры", self)
        self.settings_ui = CameraSettingsWidget(camera_obj)
        self.dock_hw.setWidget(self.settings_ui)
        self.thread.camera_opened.connect(self.settings_ui.setup_ui)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_hw)
        self.view_menu.addAction(self.dock_hw.toggleViewAction())
        # ------------ new settings init ---------

        bus = GlobalBus.instance()
        bus.raw_frame_sent.connect(self._on_frame_received) #TODO: сделать отправку части (сегмента кадра) {через выделение в виджете?  или  сделать через зум и drag}
        bus.analysis_results_sent.connect(self._on_results_received)
        bus.analysis_many_results_sent.connect(self._on_results_received)

        bus.is_draw_fit.connect(self.toggle_draw)
        bus.analysis_cleared.connect(self.overlay.clear)

    def toggle_draw(self, val):
        self.is_draw_fit = val
        if not val:
            self.overlay.clear()

    def _on_frame_received(self, name, frame):
        if name == self.cam_name:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            self.video_container.update_image(pixmap)

            # публикуем кадр для анализа: обрезка по ROI (копия) или весь кадр
            roi = self.video_container.roi
            use_frame = frame
            if not roi.isNull():
                x = max(0, int(roi.x()))
                y = max(0, int(roi.y()))
                w = min(frame.shape[1] - x, int(roi.width()))
                h = min(frame.shape[0] - y, int(roi.height()))
                if w > 0 and h > 0:
                    use_frame = frame[y : y + h, x : x + w].copy()
            GlobalBus.instance().frame_to_use.emit(self.cam_name, use_frame)

    def _on_results_received(self, name, data):
        if name == self.cam_name and self.is_draw_fit:
            img = self.video_container.current_image
            if img:
                self.overlay.update_data(
                    self._translate_results(data), img.width(), img.height()
                )

    def _translate_results(self, data):
        """Сдвигаем координаты результата анализа (он в системе ROI)
        обратно в систему полного кадра для оверлея."""
        roi = self.video_container.roi
        if roi.isNull():
            return data
        rx, ry = roi.x(), roi.y()
        out = dict(data)
        out["mu_x"] = data.get("mu_x", 0) + rx
        out["mu_y"] = data.get("mu_y", 0) + ry
        out["fits_x"] = [
            (np.asarray(xr) + rx, yf) for xr, yf in data.get("fits_x", [])
        ]
        out["fits_y"] = [
            (np.asarray(xr) + ry, yf) for xr, yf in data.get("fits_y", [])
        ]
        return out

    def shutdown(self):
        if self.thread and self.thread.isRunning():
            self.thread.stop()
            self.thread = None
