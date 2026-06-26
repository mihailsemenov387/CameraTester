import sys

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QSlider,
    QSpinBox,
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


class CameraSettingsWidget(QDockWidget):
    def __init__(self, camera: AbstractCamera):
        super().__init__("Настройки камеры")
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)

        settings_widget = QWidget()
        self.layout = QVBoxLayout()

        # Теперь мы можем передавать функцию для "Авто", если она есть!
        self.add_slider(
            "Экспозиция:", -10, 0, -5, camera.set_exposure, camera.set_auto_exposure
        )
        self.add_slider("Gamma:", 90, 150, 100, camera.set_gamma)
        self.add_slider("Gain:", 4, 8, 1, camera.set_gain)
        self.add_slider("Contrast:", 0, 255, 127, camera.set_contrast)
        self.add_slider("Brightness:", -127, 127, 0, camera.set_brightness)

        self.layout.addStretch()
        settings_widget.setLayout(self.layout)
        self.setWidget(settings_widget)

    def add_slider(
        self, label_text, min_val, max_val, start_val, connect_func, auto_func=None
    ):
        row_layout = QHBoxLayout()

        label = QLabel(label_text)
        label.setMinimumWidth(80)
        row_layout.addWidget(label)

        # 2. Ползунок
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(start_val)

        # 3. SpinBox (Цифры со стрелочками)
        spinbox = QSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(start_val)
        spinbox.setFixedWidth(50)  # Чтобы окошко не растягивалось слишком сильно

        # СИНХРОНИЗАЦИЯ: Ползунок двигает цифры, а цифры двигают ползунок!
        slider.valueChanged.connect(spinbox.setValue)
        spinbox.valueChanged.connect(slider.setValue)

        # Отправляем значение в камеру (подключаем только ползунок, так как они связаны)
        slider.valueChanged.connect(connect_func)

        row_layout.addWidget(slider)
        row_layout.addWidget(spinbox)

        # 4. Кнопка Авто (Чекбокс)
        if auto_func:
            auto_cb = QCheckBox("Авто")
            # Если поставили галочку -> блокируем ручной ввод (чтобы пользователь не дергал ползунок)
            auto_cb.toggled.connect(slider.setDisabled)
            auto_cb.toggled.connect(spinbox.setDisabled)
            # Отправляем команду в камеру
            auto_cb.toggled.connect(auto_func)

            row_layout.addWidget(auto_cb)
        else:
            # Если функции Авто нет, добавляем пустое место для выравнивания
            spacer = QWidget()
            spacer.setFixedWidth(55)
            row_layout.addWidget(spacer)

        # Добавляем готовую строку в главный вертикальный макет
        self.layout.addLayout(row_layout)


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
        self.dock_settings = CameraSettingsWidget(self.camera)

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
