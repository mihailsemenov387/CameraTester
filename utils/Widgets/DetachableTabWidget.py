from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget


class DetachableTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(True)
        self.tabBarDoubleClicked.connect(self.detach_tab)
        self.detached_windows = {}

    def detach_tab(self, index):
        if index < 0 or self.count() <= 1:
            return

        widget = self.widget(index)
        title = self.tabText(index)

        # Создаем окно-контейнер
        pop_window = QWidget()
        pop_window.setWindowTitle(title)
        pop_window.setWindowFlags(Qt.Window)

        layout = QVBoxLayout(pop_window)
        layout.setContentsMargins(0, 0, 0, 0)

        self.removeTab(index)
        layout.addWidget(widget)
        widget.show()  # Показываем вложенный QMainWindow воркспейса

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
