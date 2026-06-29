import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter, QPixmap
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

    # TODO: remove legacy code
    # def update_image(self, image: QImage):
    #     self.current_image = image
    #     self.update()

    # def paintEvent(self, event):
    #     painter = QPainter(self)
    #     rect = self.rect()

    #     painter.fillRect(rect, Qt.GlobalColor.black)

    #     if self.current_image and not self.current_image.isNull():
    #         scaled_img = self.current_image.scaled(
    #             rect.size(),
    #             Qt.AspectRatioMode.KeepAspectRatio,
    #             Qt.TransformationMode.FastTransformation,
    #         )

    #         x = (rect.width() - scaled_img.width()) // 2
    #         y = (rect.height() - scaled_img.height()) // 2

    #         painter.drawImage(x, y, scaled_img)

    def update_image(self, image: QPixmap):
        self.current_image = image
        self.update()

    # def paintEvent(self, event):
    #     painter = QPainter(self)
    #     rect = self.rect()

    #     painter.fillRect(rect, Qt.GlobalColor.black)

    #     if self.current_image and not self.current_image.isNull():
    #         scaled_pixmap = self.current_image.scaled(
    #             rect.size(),
    #             Qt.AspectRatioMode.KeepAspectRatio,
    #             Qt.TransformationMode.SmoothTransformation, # или fast но там шакал
    #         )

    #         x = (rect.width() - scaled_pixmap.width()) // 2
    #         y = (rect.height() - scaled_pixmap.height()) // 2

    #         painter.drawPixmap(x, y, scaled_pixmap)

    # другой скейл
    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        rect = self.rect()
        painter.fillRect(rect, Qt.GlobalColor.black)

        if self.current_image and not self.current_image.isNull():
            cam_w = self.current_image.width()
            cam_h = self.current_image.height()

            scale_x = rect.width() / cam_w
            scale_y = rect.height() / cam_h
            scale = min(scale_x, scale_y)

            target_w = cam_w * scale
            target_h = cam_h * scale
            x = (rect.width() - target_w) / 2 / scale
            y = (rect.height() - target_h) / 2 / scale

            painter.scale(scale, scale)

            painter.drawPixmap(int(x), int(y), self.current_image)
