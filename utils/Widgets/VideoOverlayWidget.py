import numpy as np
from PySide6.QtCore import QPointF, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from utils.Signals import GlobalBus


class UnifiedBeamOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.results = None
        self.image_size = None
        self.is_draw_cross = False

        GlobalBus.instance().is_draw_cross.connect(self.cross_logic)

    def cross_logic(self, data):
        self.is_draw_cross = data

    def update_data(self, results, w, h):
        self.results = results
        self.image_size = (w, h)
        self.update()

    def clear(self):
        self.results = None
        self.update()

    def paintEvent(self, event):
        if not self.results or not self.image_size:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Расчет масштаба
        rect = self.rect()
        orig_w, orig_h = self.image_size
        scaled_size = QSize(orig_w, orig_h).scaled(
            rect.size(), Qt.AspectRatioMode.KeepAspectRatio
        )
        x_off = (rect.width() - scaled_size.width()) // 2
        y_off = (rect.height() - scaled_size.height()) // 2
        scale = scaled_size.width() / orig_w

        res = self.results

        # 1. Перекрестие (по mu_x, mu_y)
        if self.is_draw_cross:
            painter.setPen(QPen(QColor(255, 0, 0, 150), 1, Qt.PenStyle.DashLine))
            cx = x_off + res.get("mu_x", 0) * scale
            cy = y_off + res.get("mu_y", 0) * scale
            painter.drawLine(x_off, cy, x_off + scaled_size.width(), cy)
            painter.drawLine(cx, y_off, cx, y_off + scaled_size.height())

        # 2. Рисуем Гауссианы (fits_x и fits_y)
        self._draw_projections(painter, res, x_off, y_off, scaled_size, scale)

    def _draw_projections(self, painter, res, x_off, y_off, scaled_size, scale):
        plot_h = 70  # Высота графиков

        # Отрисовка X (снизу вверх)
        if "fits_x" in res and "x_raw" in res:
            max_val = np.max(res["x_raw"]) if np.max(res["x_raw"]) > 0 else 1
            painter.setPen(QPen(Qt.GlobalColor.yellow, 2))
            # Базовая линия — низ картинки
            base_y = y_off + scaled_size.height() - 5

            for fit_x, fit_y in res["fits_x"]:
                pts = [
                    QPointF(x_off + (xi * scale), base_y - (yi / max_val * plot_h))
                    for xi, yi in zip(fit_x, fit_y)
                ]
                painter.drawPolyline(pts)

        # Отрисовка Y (справа налево)
        if "fits_y" in res and "y_raw" in res:
            max_val = np.max(res["y_raw"]) if np.max(res["y_raw"]) > 0 else 1
            painter.setPen(QPen(Qt.GlobalColor.cyan, 2))
            base_x = x_off + scaled_size.width() - 5

            for fit_x, fit_y in res["fits_y"]:
                # Здесь fit_x — это координаты по вертикали (y), а fit_y — значения
                pts = [
                    QPointF(base_x - (yi / max_val * plot_h), y_off + (xi * scale))
                    for xi, yi in zip(fit_x, fit_y)
                ]
                painter.drawPolyline(pts)
