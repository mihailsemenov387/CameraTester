from abc import ABCMeta, abstractmethod

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QMainWindow

WORKSPACE_REGISTRY = {}


def register_workspace(title: str):
    def wrapper(cls):
        WORKSPACE_REGISTRY[title] = cls
        return cls

    return wrapper


class WorkspaceMeta(type(QObject), ABCMeta):
    pass


class AbstractWorkspace(QMainWindow, metaclass=WorkspaceMeta):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.destroyed.connect(self.shutdown)

    def closeEvent(self, event):
        self.shutdown()
        event.accept()

    @abstractmethod
    def shutdown(self):
        pass
