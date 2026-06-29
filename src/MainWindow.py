import importlib
import pkgutil
import sys
from pathlib import Path

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

    # def load_workspaces(self):
    #     self.modules_menu.clear()

    #     prefix = workspaces.__name__ + "."
    #     for loader, module_name, is_pkg in pkgutil.walk_packages(
    #         workspaces.__path__, prefix
    #     ):
    #         try:
    #             importlib.import_module(module_name)
    #         except Exception as e:
    #             print(f"Ошибка загрузки модуля {module_name}: {e}")

    #     for title, cls in WORKSPACE_REGISTRY.items():
    #         action = QAction(title, self)

    #         action.triggered.connect(
    #             lambda chk=False, c=cls, t=title: self.add_workspace_tab(c, t)
    #         )
    #         self.modules_menu.addAction(action)

    def load_workspaces(self):

        self.modules_menu.clear()

        # 1. Определяем, откуда запущен код (из папки проекта или из .exe)
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            base_path = Path(sys._MEIPASS)
        else:
            # Если запускаем через интерпретатор, берем корень проекта
            base_path = (
                Path(__file__).resolve().parent.parent
            )  # Подкрутите вложенность ( parent ), чтобы выйти в корень проекта

        # 2. Задаем папки для сканирования плагинов
        plugin_dirs = [base_path / "src" / "CameraWorkspace", base_path / "workspaces"]

        print(f"[DEBUG] Сканируем папки на наличие воркспейсов: {plugin_dirs}")

        # 3. Ищем все файлы workspace.py в этих папках
        for p_dir in plugin_dirs:
            if not p_dir.exists():
                continue

            # Ищем рекурсивно файлы с именем workspace.py
            for path in p_dir.rglob("workspace.py"):
                # Превращаем путь к файлу в относительный путь импорта Python
                # Например: workspaces/AnalysisWorkspace/workspace.py -> workspaces.AnalysisWorkspace.workspace
                try:
                    rel_path = path.relative_to(base_path)
                    module_path = ".".join(rel_path.with_suffix("").parts)

                    # Будим файл, чтобы сработал ваш декоратор!
                    importlib.import_module(module_path)
                    print(f"[DEBUG] Авто-импорт успешной: {module_path}")
                except Exception as e:
                    print(f"[DEBUG] Не удалось загрузить {path.name}: {e}")

        print(
            f"[DEBUG] Реестр WORKSPACE_REGISTRY после автоскана: {WORKSPACE_REGISTRY}"
        )

        # 4. Строим меню из декоратора
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
