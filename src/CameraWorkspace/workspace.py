import cv2
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QDockWidget, QMainWindow, QVBoxLayout

from utils.Classes.AbstractCamera import CameraThread
from utils.Signals import GlobalBus
from utils.Widgets.VideoDisplayWidget import VideoDisplayWidget
from utils.Widgets.VideoOverlayWidget import VideoOverlayWidget
from workspaces.AbstractWorkspace import AbstractWorkspace

from .CameraSettingsWidget import CameraSettingsWidget


class CameraWorkspace(AbstractWorkspace):
    def __init__(self, camera_obj, name="Camera"):
        super().__init__()
        self.cam_name = name
        self.thread = CameraThread(camera_obj, name)

        self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowTabbedDocks)

        ws_menu = self.menuBar()
        self.view_menu = ws_menu.addMenu("Настройки")

        self.video_container = VideoDisplayWidget()
        self.overlay = VideoOverlayWidget()
        ov_layout = QVBoxLayout(self.video_container)
        ov_layout.setContentsMargins(0, 0, 0, 0)
        ov_layout.addWidget(self.overlay)
        self.setCentralWidget(self.video_container)

        self.is_draw_fit = False

        # self.dock_hw = QDockWidget("Настройки камеры", self)
        # self.settings_ui = CameraSettingsWidget(camera_obj)
        # self.dock_hw.setWidget(self.settings_ui)
        # self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_hw)
        # self.view_menu.addAction(self.dock_hw.toggleViewAction())

        # ------------ new settings init ---------
        self.dock_hw = QDockWidget("Настройки камеры", self)
        self.settings_ui = CameraSettingsWidget(camera_obj)
        self.dock_hw.setWidget(self.settings_ui)
        self.thread.camera_opened.connect(self.settings_ui.setup_ui)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_hw)
        self.view_menu.addAction(self.dock_hw.toggleViewAction())
        # ------------ new settings init ---------

        bus = GlobalBus.instance()
        bus.raw_frame_sent.connect(self._on_frame_received)
        bus.analysis_results_sent.connect(self._on_results_received)
        bus.analysis_many_results_sent.connect(self._on_results_received)

        bus.is_draw_fit.connect(self.toggle_draw)

    def toggle_draw(self, val):
        self.is_draw_fit = val
        if not val:
            self.overlay.clear()

    # def _on_frame_received(self, name, frame):
    #     if name == self.cam_name:
    #         rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    #         h, w, ch = rgb.shape
    #         qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
    #         pixmap = QPixmap.fromImage(qimg)
    #         self.video_container.update_image(pixmap)

    def _on_frame_received(self, name, frame):
        if name != self.cam_name:
            return

        try:
            # Конвертация цветов в OpenCV (работает на чистом C++ под капотом, GIL отдыхает)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape

            # Создаем QImage и жестко изолируем память через .copy()
            qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()

            # Отдаем в виджет. Никаких тяжелых QPixmap.fromImage здесь больше нет!
            self.video_container.update_image(qimg)

        except Exception as e:
            print(f"Ошибка подготовки кадра: {e}")

    def _on_results_received(self, name, data):
        if name == self.cam_name and self.is_draw_fit:
            img = self.video_container.current_image
            if img:
                self.overlay.update_data(data, img.width(), img.height())

    def shutdown(self):
        if self.thread and self.thread.isRunning():
            self.thread.stop()
            self.thread = None
