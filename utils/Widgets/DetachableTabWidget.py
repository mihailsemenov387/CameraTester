from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget


class DetachableTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(True)

        self.setTabsClosable(True)  # Включаем крестики на вкладках
        self.tabCloseRequested.connect(self.close_tab)  #

        self.tabBarDoubleClicked.connect(self.detach_tab)
        self.detached_windows = {}

    def detach_tab(self, index):
        if index < 0 or self.count() <= 1:
            return

        widget = self.widget(index)
        title = self.tabText(index)

        pop_window = QWidget(self.window())
        pop_window.setWindowTitle(title)
        pop_window.setWindowFlags(Qt.Window)

        layout = QVBoxLayout(pop_window)
        layout.setContentsMargins(0, 0, 0, 0)

        self.removeTab(index)
        layout.addWidget(widget)

        # ВАЖНО: Qt прячет виджет при удалении из таба, нужно показать его обратно
        widget.show()

        def reattach(event):
            self.addTab(widget, title)
            pop_window.deleteLater()
            if title in self.detached_windows:
                del self.detached_windows[title]
            event.accept()

        pop_window.closeEvent = reattach
        pop_window.resize(1000, 700)
        pop_window.show()
        self.detached_windows[title] = pop_window

    def close_tab(self, index):
        widget = self.widget(index)
        if widget:
            if hasattr(widget, "shutdown"):
                widget.shutdown()
            widget.hide()
            self.removeTab(index)
            widget.deleteLater()

    def close_all_detached(self):
        # Создаем копию списка окон, чтобы избежать ошибок при удалении во время цикла
        windows = list(self.detached_windows.values())
        for win in windows:
            # Отключаем reattach перед закрытием, чтобы вкладки не пытались
            # вернуться в уже закрывающееся главное окно
            win.closeEvent = lambda event: event.accept()
            win.close()
            win.deleteLater()
        self.detached_windows.clear()
