import sys

from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QAction, QImage
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from utils.Classes.AbstractCamera import CameraFactory, CameraThread
from utils.SpecialFunctions.AnalysysFun import process
from utils.Widgets.AnalysisToolWidget import AnalysisToolWidget  # <--- Наш новый виджет
from utils.Widgets.SettingsWidget import CameraSettingsWidget
from utils.Widgets.TopBarMenu import CameraSelectionDialog
from utils.Widgets.VideoDisplayWidget import VideoDisplayWidget
from utils.Widgets.VideoOverlayWidget import VideoOverlayWidget


class Dashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CAMTest")
        self.resize(1200, 800)

        # 1. ВКЛЮЧАЕМ РЕЖИМ VSCODE (Разрешаем табы и вложенность доков)
        self.setDockOptions(
            QMainWindow.AnimatedDocks
            | QMainWindow.AllowTabbedDocks
            | QMainWindow.AllowNestedDocks
        )

        # 2. УБИРАЕМ ЦЕНТРАЛЬНЫЙ ВИДЖЕТ
        # Мы ставим пустую невидимую заглушку, чтобы наши табы могли занять 100% экрана
        dummy = QWidget()
        self.setCentralWidget(dummy)
        dummy.hide()

        self.camera = None
        self.camera_thread = None
        self.dock_settings = None
        self.last_raw_frame = None

        # Таймер анализа
        self.analysis_timer = QTimer()
        self.analysis_timer.timeout.connect(self.run_analysis)

        # --- 3. СОЗДАЕМ ТАБ 1: LIVE VIDEO ---
        self.video_display = VideoDisplayWidget()
        self.overlay_display = VideoOverlayWidget()

        overlay_layout = QVBoxLayout(self.video_display)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.addWidget(self.overlay_display)

        # Оборачиваем видео в DockWidget, чтобы оно тоже было вкладкой
        self.video_dock = QDockWidget("Live Video", self)
        self.video_dock.setWidget(self.video_display)
        # Разрешаем видео открепляться, но запрещаем закрывать на крестик
        self.video_dock.setFeatures(
            QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable
        )

        # Добавляем в левую часть (по умолчанию она займет весь экран)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.video_dock)

        # --- 4. СОЗДАЕМ ТАБ 2: УТИЛИТА АНАЛИЗА ---
        self.analysis_dock = AnalysisToolWidget(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.analysis_dock)

        # МАГИЯ QT: Склеиваем видео и анализ в единые Вкладки (Tabs)
        self.tabifyDockWidget(self.video_dock, self.analysis_dock)

        # Подключаем сигналы таймера
        self.analysis_dock.speed_changed.connect(self.analysis_timer.setInterval)
        self.analysis_dock.enabled_changed.connect(self.toggle_analysis)

        # Делаем активной вкладку с Видео
        self.video_dock.raise_()

        self.create_menu()

    def create_menu(self):
        menu_bar = self.menuBar()

        # Меню "Камера"
        cam_menu = menu_bar.addMenu("Камера")
        connect_action = QAction("Подключиться...", self)
        connect_action.triggered.connect(self.open_connect_dialog)
        cam_menu.addAction(connect_action)

        disconnect_action = QAction("Отключиться", self)
        disconnect_action.triggered.connect(self.disconnect_camera)
        cam_menu.addAction(disconnect_action)

        # Меню "Вид"
        self.view_menu = menu_bar.addMenu("Вид")
        self.update_view_menu()

        # Меню "Утилиты"
        # tools_menu = menu_bar.addMenu("Утилиты")
        # analysis_action = QAction("Анализ профиля пучка", self)
        # # Открывает или переводит фокус на панель аналитики
        # analysis_action.triggered.connect(lambda: self.analysis_dock.setVisible(True))
        # tools_menu.addAction(analysis_action)

        tools_menu = menu_bar.addMenu("Утилиты")
        analysis_action = QAction("Анализ профиля пучка", self)

        def show_analysis_tab():
            self.analysis_dock.setVisible(True)
            self.analysis_dock.raise_()  # Выводит вкладку на передний план!

        analysis_action.triggered.connect(show_analysis_tab)
        tools_menu.addAction(analysis_action)

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

        self.statusBar().showMessage("Подключение к камере, ожидайте...")
        self.camera_thread = CameraThread(self.camera)

        self.camera_thread.camera_opened.connect(lambda: self.on_camera_opened(config))
        self.camera_thread.camera_error.connect(self.on_camera_error)
        self.camera_thread.frame_ready.connect(self.video_display.update_image)
        self.camera_thread.raw_frame_ready.connect(self.store_raw_frame)

        self.camera_thread.start()

    @Slot(object)
    def store_raw_frame(self, frame):
        self.last_raw_frame = frame

    @Slot(bool)
    def toggle_analysis(self, is_enabled: bool):
        """Включает/выключает тяжелую математику"""
        if is_enabled:
            # Запускаем таймер с интервалом из спинбокса
            self.analysis_timer.start(self.analysis_dock.speed_spin.value())
        else:
            self.analysis_timer.stop()
            self.overlay_display.clear()  # Стираем графики с экрана видео
            self.statusBar().clearMessage()

    @Slot()
    def run_analysis(self):
        """Вызывается по таймеру, только если галочка 'Включить расчет' нажата"""
        if self.last_raw_frame is not None:
            results = process(self.last_raw_frame)
            if results and results.get("amp_x", 0) > 0:
                # 1. Отправляем в оверлей (поверх видео)
                h, w = self.last_raw_frame.shape[:2]
                self.overlay_display.update_data(results, orig_width=w, orig_height=h)

                # 2. Отправляем в Утилиту анализа (там нарисуются графики)
                self.analysis_dock.update_plots(results)

                # 3. Пишем статус
                self.statusBar().showMessage(
                    f"Центр X: {results['mu_x']:.1f}, Y: {results['mu_y']:.1f} | Sigma X: {results['sigma_x']:.2f}"
                )

    @Slot()
    def on_camera_opened(self, config: dict):
        self.statusBar().showMessage(
            f"Успешно подключено к: {config.get('name')}", 5000
        )

        # Настройки камеры создаются только при подключении
        self.dock_settings = CameraSettingsWidget(self.camera)
        self.dock_settings.setWindowTitle(f"Настройки: {config.get('name')}")
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_settings)
        self.update_view_menu()

    @Slot(str)
    def on_camera_error(self, error_msg: str):
        self.statusBar().clearMessage()
        QMessageBox.critical(self, "Ошибка подключения", error_msg)
        self.disconnect_camera()

    def disconnect_camera(self):
        # Останавливаем анализ, чтобы не считать по мертвым кадрам
        self.analysis_dock.enable_cb.setChecked(False)

        if self.camera_thread:
            try:
                self.camera_thread.frame_ready.disconnect(
                    self.video_display.update_image
                )
            except:
                pass

        if self.camera_thread and self.camera_thread.isRunning():
            self.camera_thread.stop()
            self.camera_thread = None

        if self.camera:
            self.camera.close()
            self.camera = None

        if self.dock_settings:
            self.removeDockWidget(self.dock_settings)
            self.dock_settings.deleteLater()
            self.dock_settings = None
            self.update_view_menu()

        self.last_raw_frame = None
        self.overlay_display.clear()
        self.video_display.update_image(QImage())

    def update_view_menu(self):
        self.view_menu.clear()
        if self.dock_settings:
            self.view_menu.addAction(self.dock_settings.toggleViewAction())
        # Добавляем в Вид галочку для Утилиты анализа
        self.view_menu.addAction(self.analysis_dock.toggleViewAction())

    def closeEvent(self, event):
        self.disconnect_camera()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = Dashboard()
    window.show()
    sys.exit(app.exec())
