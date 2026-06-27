import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox

from utils.Classes.AbstractCamera import CameraFactory, CameraThread
from utils.Widgets.DetachableTabWidget import DetachableTabWidget
from utils.Widgets.TopBarMenu import CameraSelectionDialog
from utils.Widgets.Workspaces import AnalysisWorkspace, CameraWorkspace


class Dashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VEPP-2000 Platform")
        self.resize(1200, 850)

        # Центральный хаб вкладок
        self.tabs = DetachableTabWidget(self)
        self.setCentralWidget(self.tabs)

        # Создаем Аналитику (она сразу подписывается на GlobalBus)
        self.analysis_ws = AnalysisWorkspace()
        self.tabs.addTab(self.analysis_ws, "Аналитика профиля")

        self.create_menu()

    def create_menu(self):
        menu = self.menuBar().addMenu("Система")
        menu.addAction("Подключить камеру", self.on_connect_clicked)
        menu.addAction("Отключить всё", self.close)

    def on_connect_clicked(self):
        dialog = CameraSelectionDialog(self)
        if dialog.exec():
            config = dialog.get_camera_config()
            self.add_camera(config)

    def add_camera(self, config):
        name = config.get("name")
        camera = CameraFactory.create(config)
        if not camera:
            return

        # 1. Показываем надпись сразу (инициализация началась)
        self.statusBar().showMessage(f"Подключение к камере {name}...")

        # 2. Создаем воркспейс
        ws = CameraWorkspace(camera, name)
        self.tabs.addTab(ws, f"Live: {name}")
        self.tabs.setCurrentWidget(ws)

        # 3. Создаем поток
        ws.thread = CameraThread(camera, name)

        # Слот: когда камера реально открылась в фоне
        ws.thread.camera_opened.connect(
            lambda: self.statusBar().showMessage(
                f"Камера {name} успешно подключена", 5000
            )
        )

        # Слот: если произошла ошибка
        ws.thread.camera_error.connect(
            lambda msg: self.statusBar().showMessage(f"Ошибка: {msg}", 10000)
        )

        # Запускаем
        ws.thread.start()

    def closeEvent(self, event):
        # 1. Сначала останавливаем все потоки во всех вкладках
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if hasattr(widget, "shutdown"):
                widget.shutdown()

        # 2. Закрываем оторванные окна (они тоже должны остановиться)
        for title, window in list(self.tabs.detached_windows.items()):
            # Ищем воркспейс внутри оторванного окна
            # (так как наше оторванное окно - это QWidget с layout-ом)
            internal_ws = window.findChild(CameraWorkspace)
            if internal_ws:
                internal_ws.shutdown()
            window.close()

        event.accept()
