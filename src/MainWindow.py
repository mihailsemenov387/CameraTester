import sys

from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QAction, QImage
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from utils.Classes.AbstractCamera import CameraFactory, CameraThread
from utils.Classes.Plotter import Plotter
from utils.SpecialFunctions.AnalysysFun import process
from utils.Widgets.AnalysisSettingsWidget import AnalysisSettingsWidget
from utils.Widgets.DetachableTabWidget import DetachableTabWidget
from utils.Widgets.SettingsWidget import CameraSettingsWidget
from utils.Widgets.TopBarMenu import CameraSelectionDialog
from utils.Widgets.VideoDisplayWidget import VideoDisplayWidget
from utils.Widgets.VideoOverlayWidget import VideoOverlayWidget


class Dashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VEPP-2000 Beam Profiler")

        # Центральный виджет - только менеджер вкладок
        self.tabs = DetachableTabWidget(self)
        self.setCentralWidget(self.tabs)

        # Глобальный таймер анализа (может быть один на всех)
        self.analysis_timer = QTimer()
        self.analysis_timer.timeout.connect(self.global_analysis_loop)
        self.analysis_timer.start(200)

        self.workspaces = []  # Список активных вкладок-воркспейсов

        self.camera = None
        self.camera_thread = None
        self.camera_settings = None  # Настройки камеры (создадутся при подключении)
        self.last_raw_frame = None

        # Таймер анализа
        self.analysis_timer = QTimer()
        self.analysis_timer.timeout.connect(self.global_analysis_loop)

        # --- НАШИ ВКЛАДКИ (Центральный виджет) ---
        self.tabs = DetachableTabWidget(self)
        self.setCentralWidget(self.tabs)

        # 1. ВОРКСПЕЙС КАМЕРЫ (Кадр + Настройки камеры)
        self.camera_workspace = QWidget()
        self.cam_layout = QHBoxLayout(self.camera_workspace)
        self.cam_layout.setContentsMargins(0, 0, 0, 0)
        self.cam_layout.setSpacing(5)

        self.video_display = VideoDisplayWidget()
        self.overlay_display = VideoOverlayWidget()

        # Накладываем оверлей поверх видео
        overlay_layout = QVBoxLayout(self.video_display)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.addWidget(self.overlay_display)

        self.cam_layout.addWidget(self.video_display, stretch=4)
        # Сюда при подключении добавится панель настроек камеры

        self.create_menu()

    def create_menu(self):
        menu_bar = self.menuBar()

        cam_menu = menu_bar.addMenu("Камера")
        connect_action = QAction("Подключиться", self)
        connect_action.triggered.connect(self.open_connect_dialog)
        cam_menu.addAction(connect_action)

        disconnect_action = QAction("Отключиться", self)
        disconnect_action.triggered.connect(self.disconnect_camera)
        cam_menu.addAction(disconnect_action)

    def open_connect_dialog(self):
        dialog = CameraSelectionDialog(self)
        if dialog.exec():
            config = dialog.get_camera_config()
            self.connect_to_camera(config)

    def connect_to_camera(self, config):
        camera = CameraFactory.create(config)
        if not camera or not camera.open():
            return

        # Создаем воркспейс (внутри него уже есть доки настроек)
        ws = CameraWorkspace(camera, name=config.get("name"))
        self.tabs.addTab(ws, config.get("name"))
        self.workspaces.append(ws)

        # Поток камеры
        thread = CameraThread(camera)
        thread.frame_ready.connect(ws.video_container.update_image)
        # Сохраняем последний кадр в воркспейс для анализа
        thread.raw_frame_ready.connect(lambda f: setattr(ws, "last_frame", f))
        thread.start()
        ws.camera_thread = thread

    @Slot(object)
    def store_raw_frame(self, frame):
        self.last_raw_frame = frame

    @Slot(bool)
    def toggle_analysis(self, is_enabled: bool):
        if is_enabled:
            self.analysis_timer.start(self.analysis_settings.speed_spin.value())
        else:
            self.analysis_timer.stop()
            self.overlay_display.clear()
            self.statusBar().clearMessage()

    def global_analysis_loop(self):
        """Проходим по всем воркспейсам и обновляем математику, если они активны"""
        for ws in self.workspaces:
            if hasattr(ws, "last_frame") and ws.last_frame is not None:
                # Если воркспейс не скрыт и не закрыт - считаем
                res = process(ws.last_frame)
                if res:
                    ws.overlay.update_data(
                        res, ws.last_frame.shape[1], ws.last_frame.shape[0]
                    )
                    # Если внутри воркспейса есть док с графиками - обновляем

    @Slot()
    def on_camera_opened(self, config: dict):
        self.statusBar().showMessage(
            f"Успешно подключено к: {config.get('name')}", 5000
        )

        # Создаем настройки и добавляем их прямо в горизонтальный макет вкладки Камеры!
        self.camera_settings = CameraSettingsWidget(self.camera)
        self.cam_layout.addWidget(self.camera_settings, stretch=1)

    @Slot(str)
    def on_camera_error(self, error_msg: str):
        self.statusBar().clearMessage()
        QMessageBox.critical(self, "Ошибка подключения", error_msg)
        self.disconnect_camera()

    def disconnect_camera(self):
        self.analysis_settings.enable_cb.setChecked(False)

        if self.camera_thread:
            try:
                self.camera_thread.frame_ready.disconnect(
                    self.video_display.update_image
                )
                self.camera_thread.raw_frame_ready.disconnect(self.store_raw_frame)
            except:
                pass

        if self.camera_thread and self.camera_thread.isRunning():
            self.camera_thread.stop()
            self.camera_thread = None

        if self.camera:
            self.camera.close()
            self.camera = None

        # Удаляем настройки камеры из вкладки при отключении
        if self.camera_settings:
            self.cam_layout.removeWidget(self.camera_settings)
            self.camera_settings.deleteLater()
            self.camera_settings = None

        self.last_raw_frame = None
        self.overlay_display.clear()
        self.video_display.update_image(QImage())

    def closeEvent(self, event):
        self.disconnect_camera()
        # Закрываем все оторванные вкладки
        for window in list(self.tabs.detached_windows.values()):
            window.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = Dashboard()
    window.show()
    sys.exit(app.exec())
