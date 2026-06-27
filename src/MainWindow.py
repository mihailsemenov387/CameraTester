import importlib
import pkgutil
import sys

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox

import workspaces  # Импортируем папку как пакет
from utils.Classes.AbstractCamera import CameraFactory, CameraThread
from utils.Widgets.DetachableTabWidget import DetachableTabWidget
from utils.Widgets.TopBarMenu import CameraSelectionDialog
from utils.Widgets.Workspaces import CameraWorkspace


class Dashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VEPP-2000 Platform")
        self.resize(1200, 850)

        # Центральный хаб вкладок
        self.tabs = DetachableTabWidget(self)
        self.setCentralWidget(self.tabs)

        self.create_menu()

        # Автоматически загружаем модули в меню при старте
        self.load_workspaces()

    def create_menu(self):
        menu_bar = self.menuBar()

        # 1. Меню Система
        sys_menu = menu_bar.addMenu("Система")
        sys_menu.addAction("Подключить камеру", self.on_connect_clicked)
        sys_menu.addSeparator()
        sys_menu.addAction("Выход", self.close)

        # 2. Меню Модули (сюда будут добавляться воркспейсы)
        self.modules_menu = menu_bar.addMenu("Модули")

    def load_workspaces(self):
        """Сканирует папку workspaces и добавляет плагины в меню"""
        self.modules_menu.clear()

        # Итерируемся по подпапкам внутри workspaces/
        for loader, module_name, is_pkg in pkgutil.iter_modules(workspaces.__path__):
            if is_pkg:
                try:
                    # Динамический импорт модуля
                    full_module_name = f"workspaces.{module_name}"
                    module = importlib.import_module(full_module_name)

                    # Проверяем наличие контракта (WORKSPACE_CLASS)
                    if hasattr(module, "WORKSPACE_CLASS"):
                        title = getattr(
                            module, "WORKSPACE_TITLE", module_name.capitalize()
                        )

                        # Создаем действие в меню для открытия этого воркспейса
                        action = QAction(title, self)
                        # Используем лямбду с захватом текущего модуля
                        action.triggered.connect(
                            lambda checked=False, m=module: self.add_workspace_tab(m)
                        )
                        self.modules_menu.addAction(action)

                except Exception as e:
                    print(f"Ошибка загрузки модуля {module_name}: {e}")

    def add_workspace_tab(self, module):
        """Создает экземпляр воркспейса и добавляет его как вкладку"""
        cls = getattr(module, "WORKSPACE_CLASS")
        title = getattr(module, "WORKSPACE_TITLE", "Новый модуль")

        # Создаем объект воркспейса (AnalysisWorkspace или любой другой)
        instance = cls()
        self.tabs.addTab(instance, title)
        self.tabs.setCurrentWidget(instance)

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

        self.statusBar().showMessage(f"Подключение к камере {name}...")

        ws = CameraWorkspace(camera, name)
        self.tabs.addTab(ws, f"Live: {name}")
        self.tabs.setCurrentWidget(ws)

        ws.thread = CameraThread(camera, name)
        ws.thread.camera_opened.connect(
            lambda: self.statusBar().showMessage(
                f"Камера {name} успешно подключена", 5000
            )
        )
        ws.thread.camera_error.connect(
            lambda msg: self.statusBar().showMessage(f"Ошибка: {msg}", 10000)
        )
        ws.thread.start()

    def closeEvent(self, event):
        # Остановка всех потоков перед выходом
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if hasattr(widget, "shutdown"):
                widget.shutdown()

        for title, window in list(self.tabs.detached_windows.items()):
            # Ищем воркспейсы в оторванных окнах
            internal_ws = window.findChild(CameraWorkspace)
            if internal_ws:
                internal_ws.shutdown()
            window.close()

        event.accept()
