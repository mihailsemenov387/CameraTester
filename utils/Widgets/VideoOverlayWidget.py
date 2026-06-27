import numpy as np
from PySide6.QtCore import QPointF, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class VideoOverlayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Делаем фон полностью прозрачным
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # Пропускаем клики мыши сквозь этот виджет (чтобы он не блокировал интерфейс)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.results = None
        self.image_size = None  # Нужно знать размер оригинального кадра для математики

    def update_data(self, results: dict, orig_width: int, orig_height: int):
        self.results = results
        self.image_size = (orig_width, orig_height)
        self.update()

    def clear(self):
        self.results = None
        self.update()

    def paintEvent(self, event):
        # Если нет данных, ничего не рисуем (виджет останется невидимым)
        if not self.results or not self.image_size:
            return

        painter = QPainter(self)
        rect = self.rect()

        orig_w, orig_h = self.image_size

        # Мы должны повторить логику масштабирования VideoDisplayWidget,
        # чтобы знать, ГДЕ ИМЕННО на экране сейчас находится картинка с камеры.
        orig_size = QSize(orig_w, orig_h)
        scaled_size = orig_size.scaled(rect.size(), Qt.AspectRatioMode.KeepAspectRatio)

        x_off = (rect.width() - scaled_size.width()) // 2
        y_off = (rect.height() - scaled_size.height()) // 2
        scale = scaled_size.width() / orig_w

        res = self.results
        cx = x_off + res.get("mu_x", 0) * scale
        cy = y_off + res.get("mu_y", 0) * scale

        # --- Рисуем перекрестие ---
        painter.setPen(QPen(QColor(255, 0, 0, 200), 2, Qt.PenStyle.DashLine))
        painter.drawLine(x_off, cy, x_off + scaled_size.width(), cy)
        painter.drawLine(cx, y_off, cx, y_off + scaled_size.height())

        # --- Гауссиана по X ---
        if "X_gauss" in res and "x_w" in res:
            painter.setPen(
                QPen(Qt.GlobalColor.yellow, 3)
            )  # Толщина 3 для лучшей видимости
            plot_h = 80

            # Нижняя граница кадра с отступом 10 пикселей внутрь картинки
            y_baseline = y_off + scaled_size.height() - 10

            max_val = np.max(res["x_w"]) if np.max(res["x_w"]) > 0 else 1
            points = [
                # Вычитаем из y_baseline, чтобы график рос ВВЕРХ
                QPointF(x_off + (i * scale), y_baseline - (val / max_val * plot_h))
                for i, val in enumerate(res["X_gauss"])
            ]
            painter.drawPolyline(points)

        # --- Гауссиана по Y ---
        if "Y_gauss" in res and "y_w" in res:
            painter.setPen(QPen(Qt.GlobalColor.cyan, 3))
            plot_w = 80

            # Правая граница кадра с отступом 10 пикселей внутрь
            x_baseline = x_off + scaled_size.width() - 10

            max_val = np.max(res["y_w"]) if np.max(res["y_w"]) > 0 else 1
            points = [
                # Вычитаем из x_baseline, чтобы график рос ВЛЕВО внутрь кадра
                QPointF(x_baseline - (val / max_val * plot_w), y_off + (i * scale))
                for i, val in enumerate(res["Y_gauss"])
            ]
            painter.drawPolyline(points)
