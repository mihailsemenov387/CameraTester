import sys

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QImage, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from utils.Classes.AbstractCamera import AbstractCamera, CameraThread, UVCCamera


class VideoDisplayWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.current_image = None
        # Говорим Qt: этот виджет может тянуться как угодно, не ломай интерфейс
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(320, 240)

    def update_image(self, image: QImage):
        self.current_image = image
        self.update()  # Просто просим Qt перерисовать прямоугольник (очень быстро)

    def paintEvent(self, event):
        # Эта функция вызывается видеокартой. Она не трогает соседние окна!
        if self.current_image:
            painter = QPainter(self)
            rect = self.rect()

            # Масштабируем картинку "на лету" с быстрым алгоритмом
            scaled_img = self.current_image.scaled(
                rect.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )

            # Центрируем картинку на черном фоне
            x = (rect.width() - scaled_img.width()) // 2
            y = (rect.height() - scaled_img.height()) // 2

            # Заливаем фон черным
            painter.fillRect(rect, Qt.GlobalColor.black)
            # Отрисовываем кадр
            painter.drawImage(x, y, scaled_img)


class LabDashboard(QMainWindow):
    def __init__(self, camera: AbstractCamera):
        super().__init__()
        self.camera = camera
        self.setWindowTitle("VEPP-2000 Alignment Tool")
        self.resize(1000, 700)

        # -- Центр (Видео) --
        central_widget = QWidget()
        central_layout = QVBoxLayout()
        self.video_display = VideoDisplayWidget()
        central_layout.addWidget(self.video_display)
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

        # -- Док Настройки --
        self.dock_settings = QDockWidget("Настройки камеры", self)
        self.dock_settings.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)

        settings_widget = QWidget()
        settings_layout = QVBoxLayout()
        settings_layout.addWidget(QLabel("Экспозиция:"))

        # Настраиваем слайдер под типичные значения OpenCV (от -10 до 0)
        self.slider_exp = QSlider(Qt.Orientation.Horizontal)
        self.slider_exp.setRange(-10, 0)
        self.slider_exp.setValue(-5)
        # ПОДВЯЗЫВАЕМ СЛАЙДЕР К КАМЕРЕ
        self.slider_exp.valueChanged.connect(self.camera.set_exposure)

        settings_layout.addWidget(self.slider_exp)
        settings_layout.addStretch()
        settings_widget.setLayout(settings_layout)
        self.dock_settings.setWidget(settings_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_settings)

        # -- Запуск потока камеры --
        self.camera_thread = CameraThread(self.camera)
        # Подвязываем сигнал с картинкой из потока к обновлению экрана
        self.camera_thread.frame_ready.connect(self.update_video_screen)
        self.camera_thread.start()

    @Slot(QImage)
    def update_video_screen(self, image: QImage):
        # Масштабируем картинку под размер окна (сохраняя пропорции)
        self.video_display.update_image(image)

    def closeEvent(self, event):
        # Правильное закрытие программы при нажатии на крестик
        self.camera_thread.stop()
        self.camera.close()
        event.accept()


# ==========================================
# 4. ЗАПУСК
# ==========================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Создаем нашу абстрактную UVC-камеру
    my_webcam = UVCCamera(index=0)

    if not my_webcam.open():
        print("Не удалось открыть камеру!")
        sys.exit(1)

    # Передаем камеру в интерфейс
    window = LabDashboard(my_webcam)
    window.show()

    sys.exit(app.exec())
