import sys

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction, QImage
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from utils.Classes.AbstractCamera import CameraFactory, CameraThread, UVCCamera
from utils.Widgets.SettingsWidget import CameraSettingsWidget
from utils.Widgets.TopBarMenu import CameraSelectionDialog
from utils.Widgets.VideoDisplayWidget import VideoDisplayWidget


class Dashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CAMTest")
        self.resize(1000, 700)

        self.camera = None
        self.camera_thread = None
        self.dock_settings = None

        central_widget = QWidget()
        central_layout = QVBoxLayout()
        self.video_display = VideoDisplayWidget()

        central_layout.addWidget(self.video_display)
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

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

        self.view_menu = menu_bar.addMenu("Вид")
        self.update_view_menu()

    def open_connect_dialog(self):
        dialog = CameraSelectionDialog(self)
        if dialog.exec():
            config = dialog.get_camera_config()
            self.connect_to_camera(config)

    def connect_to_camera(self, config: dict):
        self.disconnect_camera()

        self.camera = CameraFactory.create(config)
        if not self.camera:
            QMessageBox.critical(
                self, "Ошибка", f"Неподдерживаемый тип камеры: {config.get('type')}"
            )
            return

        # Показываем внизу статус, что идет подключение
        self.statusBar().showMessage("Подключение к камере, ожидайте...")

        # Создаем поток
        self.camera_thread = CameraThread(self.camera)

        # Подключаем сигналы от фонового потока
        self.camera_thread.camera_opened.connect(lambda: self.on_camera_opened(config))
        self.camera_thread.camera_error.connect(self.on_camera_error)
        self.camera_thread.frame_ready.connect(self.update_video_screen)

        # Запускаем поток (камера начнет открываться в фоне)
        self.camera_thread.start()

    @Slot()
    def on_camera_opened(self, config: dict):
        """Сработает, когда поток успешно откроет камеру"""
        self.statusBar().showMessage(
            f"Успешно подключено к: {config.get('name')}", 5000
        )

        # Только теперь создаем панель настроек!
        self.dock_settings = CameraSettingsWidget(self.camera)
        self.dock_settings.setWindowTitle(f"Настройки: {config.get('name')}")
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_settings)
        self.update_view_menu()

    @Slot(str)
    def on_camera_error(self, error_msg: str):
        """Сработает, если камера не откроется"""
        self.statusBar().clearMessage()
        QMessageBox.critical(self, "Ошибка подключения", error_msg)
        self.disconnect_camera()

    def disconnect_camera(self):
        """Безопасная остановка потока и закрытие камеры"""
        if self.camera_thread:
            # 1. Сначала ПРЕРЫВАЕМ СВЯЗЬ.
            # Теперь, что бы ни прислал поток, функция update_video_screen не вызовется.
            try:
                self.camera_thread.frame_ready.disconnect(self.update_video_screen)
            except:
                # На случай, если сигнал и так не был подключен
                pass

        if self.camera_thread and self.camera_thread.isRunning():
            self.camera_thread.stop()
            self.camera_thread = None

        if self.camera:
            self.camera.close()
            self.camera = None

        # Удаляем старую панель настроек (чтобы нельзя было крутить настройки отключенной камеры)
        if self.dock_settings:
            self.removeDockWidget(self.dock_settings)
            self.dock_settings.deleteLater()
            self.dock_settings = None
            self.update_view_menu()

        # Очищаем экран
        self.video_display.update_image(QImage())

    def update_view_menu(self):
        """Добавляет в меню Вид галочку для отображения/скрытия панели настроек"""
        self.view_menu.clear()
        if self.dock_settings:
            # toggleViewAction - это встроенная в Qt магия, которая сама создает
            # пункт меню с галочкой для скрытия/показа QDockWidget
            self.view_menu.addAction(self.dock_settings.toggleViewAction())
        else:
            no_settings_action = QAction("Нет активных панелей", self)
            no_settings_action.setDisabled(True)
            self.view_menu.addAction(no_settings_action)

    @Slot(QImage)
    def update_video_screen(self, image: QImage):
        self.video_display.update_image(image)

    def closeEvent(self, event):
        self.disconnect_camera()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = Dashboard()
    window.show()

    sys.exit(app.exec())
