# import numpy as np
# from PySide6.QtCore import Qt
# from PySide6.QtGui import QImage, QPainter, QPixmap
# from PySide6.QtWidgets import (
#     QSizePolicy,
#     QWidget,
# )


# class VideoDisplayWidget(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.current_image = None
#         self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
#         self.setMinimumSize(320, 240)

#     # TODO: remove legacy code
#     # def update_image(self, image: QImage):
#     #     self.current_image = image
#     #     self.update()

#     # def paintEvent(self, event):
#     #     painter = QPainter(self)
#     #     rect = self.rect()

#     #     painter.fillRect(rect, Qt.GlobalColor.black)

#     #     if self.current_image and not self.current_image.isNull():
#     #         scaled_img = self.current_image.scaled(
#     #             rect.size(),
#     #             Qt.AspectRatioMode.KeepAspectRatio,
#     #             Qt.TransformationMode.FastTransformation,
#     #         )

#     #         x = (rect.width() - scaled_img.width()) // 2
#     #         y = (rect.height() - scaled_img.height()) // 2

#     #         painter.drawImage(x, y, scaled_img)

#     def update_image(self, image: QPixmap):
#         self.current_image = image
#         self.update()

#     # def paintEvent(self, event):
#     #     painter = QPainter(self)
#     #     rect = self.rect()

#     #     painter.fillRect(rect, Qt.GlobalColor.black)

#     #     if self.current_image and not self.current_image.isNull():
#     #         scaled_pixmap = self.current_image.scaled(
#     #             rect.size(),
#     #             Qt.AspectRatioMode.KeepAspectRatio,
#     #             Qt.TransformationMode.SmoothTransformation, # или fast но там шакал
#     #         )

#     #         x = (rect.width() - scaled_pixmap.width()) // 2
#     #         y = (rect.height() - scaled_pixmap.height()) // 2

#     #         painter.drawPixmap(x, y, scaled_pixmap)

#     # другой скейл
#     def paintEvent(self, event):
#         painter = QPainter(self)

#         painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

#         rect = self.rect()
#         painter.fillRect(rect, Qt.GlobalColor.black)

#         if self.current_image and not self.current_image.isNull():
#             cam_w = self.current_image.width()
#             cam_h = self.current_image.height()

#             scale_x = rect.width() / cam_w
#             scale_y = rect.height() / cam_h
#             scale = min(scale_x, scale_y)

#             target_w = cam_w * scale
#             target_h = cam_h * scale
#             x = (rect.width() - target_w) / 2 / scale
#             y = (rect.height() - target_h) / 2 / scale

#             painter.scale(scale, scale)

#             painter.drawPixmap(int(x), int(y), self.current_image)

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter, QPixmap
from PySide6.QtWidgets import QSizePolicy, QWidget


class VideoDisplayWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.current_image = None  # Тут храним строго QImage
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(320, 240)

    def update_image(self, image: QImage):
        """Принимает QImage. Метод отрабатывает мгновенно, не перегружая UI-поток"""
        self.current_image = image
        self.update()  # Просто просим Qt перерисовать виджет при первой возможности

    def paintEvent(self, event):
        painter = QPainter(self)
        # SmoothPixmapTransform работает быстро, если масштаб считает сама видеокарта
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        rect = self.rect()
        painter.fillRect(rect, Qt.GlobalColor.black)

        if self.current_image and not self.current_image.isNull():
            # 1. Конвертируем QImage в Pixmap строго В МОМЕНТ ОТРИСОВКИ
            # Qt делает это на уровне оптимизированного C++ кода под капотом, обходя GIL
            pixmap = QPixmap.fromImage(self.current_image)
            cam_w = pixmap.width()
            cam_h = pixmap.height()

            # 2. Ваша точная математика пропорций
            scale_x = rect.width() / cam_w
            scale_y = rect.height() / cam_h
            scale = min(scale_x, scale_y)

            target_w = cam_w * scale
            target_h = cam_h * scale

            x = (rect.width() - target_w) / 2 / scale
            y = (rect.height() - target_h) / 2 / scale

            # 3. Отрисовка через матрицу трансформации
            painter.scale(scale, scale)
            painter.drawPixmap(int(x), int(y), pixmap)

# from PySide6.QtCore import Qt
# from PySide6.QtGui import QImage, QPainter, QPixmap
# from PySide6.QtWidgets import QSizePolicy, QWidget


# class VideoDisplayWidget(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.current_pixmap = None  # Храним уже готовый для GPU Pixmap
#         self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
#         self.setMinimumSize(320, 240)

#     def update_image(self, image: QImage):
#         """Принимает QImage, сразу переводит в QPixmap и запрашивает перерисовку."""
#         if image and not image.isNull():
#             # Конвертируем в потокe получения кадра, освобождая paintEvent от лишней работы
#             self.current_pixmap = QPixmap.fromImage(image)
#         else:
#             self.current_pixmap = None
#         self.update()

#     def paintEvent(self, event):
#         painter = QPainter(self)
#         # Включаем сглаживание для качественного масштабирования видеокартой
#         painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

#         rect = self.rect()
#         # Заливаем фон черным
#         painter.fillRect(rect, Qt.GlobalColor.black)

#         if self.current_pixmap and not self.current_pixmap.isNull():
#             cam_w = self.current_pixmap.width()
#             cam_h = self.current_pixmap.height()

#             # Вычисляем коэффициент масштабирования с сохранением пропорций
#             scale_x = rect.width() / cam_w
#             scale_y = rect.height() / cam_h
#             scale = min(scale_x, scale_y)

#             # Вычисляем размеры финальной картинки на экране
#             target_w = cam_w * scale
#             target_h = cam_h * scale

#             # Центрируем картинку в окне (БЕЗ деления на масштаб!)
#             x = (rect.width() - target_w) / 2
#             y = (rect.height() - target_h) / 2

#             # Применяем трансформацию масштаба к художнику
#             painter.scale(scale, scale)

#             # Пересчитываем координаты X и Y под измененную матрицу координат
#             # Рисуем pixmap, и он встанет ровно по центру
#             painter.drawPixmap(int(x / scale), int(y / scale), self.current_pixmap)
