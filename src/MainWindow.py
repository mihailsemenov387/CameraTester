import importlib
import pkgutil

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QMessageBox

import workspaces
from utils.Classes.AbstractCamera import CameraFactory, CameraThread
from utils.Menus.TopBarMenu import CameraSelectionDialog
from utils.Widgets.DetachableTabWidget import DetachableTabWidget

from .CameraWorkspace import CameraWorkspace


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
        sys_menu = menu_bar.addMenu("Система")
        sys_menu.addAction("Подключить камеру", self.on_connect_clicked)
        sys_menu.addSeparator()
        sys_menu.addAction("Выход", self.close)

        self.modules_menu = menu_bar.addMenu("Модули")

    def load_workspaces(self):
        """Динамическая загрузка модулей-потребителей"""
        self.modules_menu.clear()

        for loader, module_name, is_pkg in pkgutil.iter_modules(workspaces.__path__):
            if is_pkg:
                try:
                    module = importlib.import_module(f"workspaces.{module_name}")

                    if hasattr(module, "WORKSPACE_CLASS"):
                        cls = getattr(module, "WORKSPACE_CLASS")

                        title = getattr(module, "WORKSPACE_TITLE", module_name)
                        action = QAction(title, self)
                        # Захватываем текущий класс через partial или дефолтный аргумент
                        action.triggered.connect(
                            lambda chk=False, c=cls, t=title: self.add_workspace_tab(
                                c, t
                            )
                        )
                        self.modules_menu.addAction(action)

                except Exception as e:
                    print(f"Ошибка загрузки модуля {module_name}: {e}")

    def add_workspace_tab(self, cls, title):
        """Создает вкладку модуля"""
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

        # Создаем CameraWorkspace (Core), передавая камеру
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

        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if hasattr(w, "shutdown"):
                w.shutdown()

        for title in list(self.tabs.detached_windows.keys()):
            win = self.tabs.detached_windows[title]
            ws = win.findChild(AbstractWorkspace)
            if ws:
                ws.shutdown()
            win.close()

        event.accept()
