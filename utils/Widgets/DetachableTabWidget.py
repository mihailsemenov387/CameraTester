from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget


class DetachableTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(True)  # Разрешаем менять вкладки местами
        self.tabBarDoubleClicked.connect(self.detach_tab)
        self.detached_windows = {}

    def detach_tab(self, index):
        # Не разрешаем отрывать последнюю вкладку, чтобы главное окно не пустовало
        if index < 0 or self.count() <= 1:
            return

        widget = self.widget(index)
        title = self.tabText(index)

        # Создаем полноценное независимое окно ОС
        pop_window = QWidget()
        pop_window.setWindowTitle(title)
        pop_window.setWindowFlags(Qt.Window)  # <--- Появится в Alt-Tab!

        layout = QVBoxLayout(pop_window)
        layout.setContentsMargins(5, 5, 5, 5)

        # Забираем виджет из вкладок и кладем в новое окно
        self.removeTab(index)
        layout.addWidget(widget)

        # Логика возвращения вкладки при закрытии выносного окна
        def reattach(event):
            self.addTab(widget, title)
            pop_window.deleteLater()
            if title in self.detached_windows:
                del self.detached_windows[title]
            event.accept()

        pop_window.closeEvent = reattach
        pop_window.resize(800, 600)
        pop_window.show()

        self.detached_windows[title] = pop_window
