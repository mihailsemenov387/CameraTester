import sys

from PySide6.QtWidgets import QApplication

from src.MainWindow import Dashboard

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Fusion выглядит одинаково на всех ОС

    window = Dashboard()
    window.show()

    sys.exit(app.exec())
