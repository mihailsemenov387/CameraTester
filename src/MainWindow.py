import importlib
import inspect  # Добавим для проверки аргументов __init__
import pkgutil
import sys

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox

import workspaces
from utils.Classes.AbstractCamera import CameraFactory, CameraThread
from utils.Widgets.DetachableTabWidget import DetachableTabWidget
from utils.Widgets.TopBarMenu import CameraSelectionDialog
from utils.Widgets.Workspaces import CameraWorkspace  # Импорт ядра


class Dashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VEPP-2000 Platform")
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

                        # ПРОВЕРКА: может ли этот класс создаться без аргументов?
                        # (Это отсечет CameraWorkspace, если он случайно попал в загрузку)
                        sig = inspect.signature(cls.__init__)
                        # Если в __init__ больше 1 аргумента (self) и они не имеют дефолтных значений
                        params = [
                            p
                            for p in sig.parameters.values()
                            if p.name != "self" and p.default is p.empty
                        ]

                        if len(params) == 0:
                            title = getattr(module, "WORKSPACE_TITLE", module_name)
                            action = QAction(title, self)
                            # Захватываем текущий класс через partial или дефолтный аргумент
                            action.triggered.connect(
                                lambda chk=False, c=cls, t=title: (
                                    self.add_workspace_tab(c, t)
                                )
                            )
                            self.modules_menu.addAction(action)
                        else:
                            print(
                                f"Модуль {module_name} пропущен: требует аргументы в __init__"
                            )

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
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if hasattr(widget, "shutdown"):
                widget.shutdown()
        event.accept()
