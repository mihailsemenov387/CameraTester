import cv2
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QDockWidget, QMainWindow, QVBoxLayout

from utils.Signals import GlobalBus
from utils.Widgets.VideoDisplayWidget import VideoDisplayWidget
from utils.Widgets.VideoOverlayWidget import UnifiedBeamOverlay


from workspaces.AbstractWorkspace import AbstractWorkspace

from .CameraSettingsWidget import CameraSettingsWidget


class CameraWorkspace(AbstractWorkspace):
    def __init__(self, camera_obj, name="Camera"):
        super().__init__()
        self.cam_name = name
        self.thread = None
        self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowTabbedDocks)

        # 1. Локальное меню
        ws_menu = self.menuBar()
        ws_menu.addMenu("Настройки").addAction("О камере...")
        self.view_menu = ws_menu.addMenu("Вид")

        # 2. Видео и Оверлей
        self.video_container = VideoDisplayWidget()
        self.overlay = UnifiedBeamOverlay() # ОДИН ВМЕСТО ДВУХ
        ov_layout = QVBoxLayout(self.video_container)
        ov_layout.setContentsMargins(0, 0, 0, 0)
        ov_layout.addWidget(self.overlay)
        self.setCentralWidget(self.video_container)


        self.is_draw_single_gauss = False
        self.is_draw_many_gauss = False


        # 3. Настройки HW (в Доке)
        self.dock_hw = QDockWidget("Настройки HW", self)
        self.settings_ui = CameraSettingsWidget(camera_obj)
        self.dock_hw.setWidget(self.settings_ui)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_hw)
        self.view_menu.addAction(self.dock_hw.toggleViewAction())

        # ПОДПИСКА НА ШИНУ
        bus = GlobalBus.instance()
        bus.raw_frame_sent.connect(self._on_frame_received)
        bus.analysis_results_sent.connect(self._on_results_received)
        bus.analysis_many_results_sent.connect(self._on_results_received_many)

        bus.draw_single_gauss.connect(self.toggle_draw)
        bus.draw_many_gauss.connect(self.toggle_draw_many)

    def toggle_draw(self, val):
        self.is_draw_single_gauss = val
        if not val:
            self.overlay.clear()

    def toggle_draw_many(self, val):
        self.is_draw_many_gauss = val
        if not val:
            self.overlay.clear()

    def _on_frame_received(self, name, frame):
        """Ловим кадр из шины. Если наш — рисуем."""
        if name == self.cam_name:
            # Конвертируем numpy в QImage прямо здесь (разгружаем поток захвата)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
            self.video_container.update_image(qimg)

    def _on_results_received(self, name, data):
        """Ловим результаты математики из шины. Если для нас — рисуем прицел."""
        if name == self.cam_name and self.is_draw_single_gauss:
            img = self.video_container.current_image
            if img:
                self.overlay.update_data(data, img.width(), img.height())

    def _on_results_received_many(self, name, data):
        """Ловим результаты математики из шины. Если для нас — рисуем прицел."""
        if name == self.cam_name and self.is_draw_many_gauss:
            img = self.video_container.current_image
            if img:
                self.overlay.update_data(data, img.width(), img.height())

    def shutdown(self):
        """Безопасная остановка потока"""
        if self.thread and self.thread.isRunning():
            self.thread.stop()
            self.thread = None
