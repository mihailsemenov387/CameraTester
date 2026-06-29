import importlib
import pkgutil

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QMessageBox

import workspaces
from utils.Classes.AbstractCamera import CameraFactory, CameraThread
from utils.Menus.TopBarMenu import CameraSelectionDialog
from utils.Widgets.DetachableTabWidget import DetachableTabWidget
from workspaces.AbstractWorkspace import WORKSPACE_REGISTRY

from .CameraWorkspace.workspace import CameraWorkspace


class Dashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CAMTest")
        self.resize(1200, 850)

        self.tabs = DetachableTabWidget(self)
        self.setCentralWidget(self.tabs)

        self.create_menu()
        self.load_workspaces()

    def create_menu(self):
        menu_bar = self.menuBar()
        sys_menu = menu_bar.addMenu("Подключение")
        sys_menu.addAction("Подключить камеру", self.on_connect_clicked)
        sys_menu.addSeparator()
        sys_menu.addAction("Выход", self.close)

        self.modules_menu = menu_bar.addMenu("Модули")

    def load_workspaces(self):
        self.modules_menu.clear()

        prefix = workspaces.__name__ + "."
        for loader, module_name, is_pkg in pkgutil.walk_packages(
            workspaces.__path__, prefix
        ):
            try:
                importlib.import_module(module_name)
            except Exception as e:
                print(f"Ошибка загрузки модуля {module_name}: {e}")

        for title, cls in WORKSPACE_REGISTRY.items():
            action = QAction(title, self)

            action.triggered.connect(
                lambda chk=False, c=cls, t=title: self.add_workspace_tab(c, t)
            )
            self.modules_menu.addAction(action)

    def add_workspace_tab(self, cls, title):
        try:
            instance = cls()
            self.tabs.addTab(instance, title)
            self.tabs.setCurrentWidget(instance)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось запустить модуль: {e}")

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

        self.statusBar().showMessage(f"Подключение к {name}...")

        ws = CameraWorkspace(camera, name)
        self.tabs.addTab(ws, f"Live: {name}")
        self.tabs.setCurrentWidget(ws)

        ws.thread = CameraThread(camera, name)
        ws.thread.camera_opened.connect(
            lambda: self.statusBar().showMessage(f"OK: {name}", 5000)
        )
        ws.thread.start()

    def closeEvent(self, event):
        print("Завершение работы программы...")

        if hasattr(self.tabs, "close_all_detached"):
            self.tabs.close_all_detached()

        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if hasattr(widget, "shutdown"):
                widget.shutdown()

        self.tabs.clear()

        print("Все модули остановлены. Выход.")

        event.accept()
