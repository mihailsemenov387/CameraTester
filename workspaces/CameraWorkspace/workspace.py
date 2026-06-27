import cv2
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QDockWidget, QMainWindow, QVBoxLayout

from utils.Classes.Plotter import Plotter
from utils.Signals import GlobalBus
from utils.SpecialFunctions.AnalysysFun import process
from utils.Widgets.AnalysisSettingsWidget import AnalysisSettingsWidget
from utils.Widgets.SettingsWidget import CameraSettingsWidget
from utils.Widgets.VideoDisplayWidget import VideoDisplayWidget
from utils.Widgets.VideoOverlayWidget import VideoOverlayWidget


class CameraWorkspace(QMainWindow):
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
        self.overlay = VideoOverlayWidget()
        ov_layout = QVBoxLayout(self.video_container)
        ov_layout.setContentsMargins(0, 0, 0, 0)
        ov_layout.addWidget(self.overlay)
        self.setCentralWidget(self.video_container)

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
        if name == self.cam_name:
            img = self.video_container.current_image
            if img:
                self.overlay.update_data(data, img.width(), img.height())

    def closeEvent(self, event):
        """Вызывается автоматически при закрытии вкладки или окна"""
        self.shutdown()
        event.accept()

    def shutdown(self):
        """Безопасная остановка потока"""
        if self.thread and self.thread.isRunning():
            self.thread.stop()
            self.thread = None
