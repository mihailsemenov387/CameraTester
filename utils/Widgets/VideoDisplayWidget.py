from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import (
    QSizePolicy,
    QWidget,
)


class VideoDisplayWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.current_image = None
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(320, 240)

    def update_image(self, image: QImage):
        self.current_image = image
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.rect()

        # 1. Сначала ВСЕГДА заливаем весь виджет черным
        painter.fillRect(rect, Qt.GlobalColor.black)

        # 2. И только если картинка есть и она не пустая — рисуем её поверх
        if self.current_image and not self.current_image.isNull():
            scaled_img = self.current_image.scaled(
                rect.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )

            x = (rect.width() - scaled_img.width()) // 2
            y = (rect.height() - scaled_img.height()) // 2

            painter.drawImage(x, y, scaled_img)
