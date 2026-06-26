from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QMainWindow, QVBoxLayout, QWidget

from utils.Widgets.SettingsWidget import CameraSettingsWidget
from utils.Widgets.VideoDisplayWidget import VideoDisplayWidget
from utils.Widgets.VideoOverlayWidget import VideoOverlayWidget


class CameraWorkspace(QMainWindow):  # <--- Наследуемся от QMainWindow!
    def __init__(self, camera_obj, name="Camera"):
        super().__init__()
        # Разрешаем вложенность и табы ВНУТРИ воркспейса
        self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowTabbedDocks)

        # --- ЦЕНТРАЛЬНАЯ ЗОНА (Видео) ---
        self.video_container = VideoDisplayWidget()
        self.overlay = VideoOverlayWidget()

        # Склеиваем видео и оверлей
        ov_layout = QVBoxLayout(self.video_container)
        ov_layout.setContentsMargins(0, 0, 0, 0)
        ov_layout.addWidget(self.overlay)

        self.setCentralWidget(self.video_container)

        # --- ЛОКАЛЬНЫЕ НАСТРОЙКИ (Док-панель внутри вкладки) ---
        self.dock_cam_settings = QDockWidget("Настройки HW", self)
        self.cam_settings_ui = CameraSettingsWidget(camera_obj)
        self.dock_cam_settings.setWidget(self.cam_settings_ui)

        # Добавляем док в это мини-окно
        self.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea, self.dock_cam_settings
        )
