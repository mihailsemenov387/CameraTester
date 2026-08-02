import numpy as np
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from utils.Signals import GlobalBus


class VideoOverlayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.results = None
        self.image_size = None
        self.is_draw_cross = False
        self.base = None  # ROIWidget, у которого берём трансформацию кадра

        GlobalBus.instance().is_draw_cross.connect(self._cross_logic)

    def set_base(self, widget):
        self.base = widget
        widget.view_changed.connect(self.update)

    def _cross_logic(self, data):
        self.is_draw_cross = data

    def update_data(self, results, w, h):
        self.results = results
        self.image_size = (w, h)
        self.update()

    def clear(self):
        self.results = None
        self.update()

    def paintEvent(self, event):
        if not self.results or not self.image_size or self.base is None:
            return
        painter = QPainter(self)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        orig_w, orig_h = self.image_size

        x_off, y_off, scale = self.base.get_transform()

        painter.translate(x_off, y_off)
        painter.scale(scale, scale)

        res = self.results

        if self.is_draw_cross:
            # Получаем координаты и сразу добавляем 0.5 для выравнивания по центру пикселя
            cx = res.get("mu_x", 0.0)
            cy = res.get("mu_y", 0.0)
            # Включаем сглаживание, чтобы толщина 1.5 отрисовалась идеально мягко и точно
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setPen(QPen(QColor(255, 0, 0, 200), 1.5 / scale, Qt.PenStyle.SolidLine))

            size = 2.0
            gap = 1.0

            # Отрисовка по QPointF теперь будет идеально центрированной
            painter.drawLine(QPointF(cx - size, cy), QPointF(cx - gap, cy))
            painter.drawLine(QPointF(cx + gap, cy), QPointF(cx + size, cy))
            painter.drawLine(QPointF(cx, cy - size), QPointF(cx, cy - gap))
            painter.drawLine(QPointF(cx, cy + gap), QPointF(cx, cy + size))

        self._draw_projections(painter, res, orig_w, orig_h)

    def _draw_projections(self, painter, res, orig_w, orig_h):
        plot_h = 70

        # X
        if "fits_x" in res and "x_raw" in res:
            max_val = np.max(res["x_raw"]) if np.max(res["x_raw"]) > 0 else 1
            painter.setPen(QPen(Qt.GlobalColor.red, 1.5))
            base_y = orig_h - 5

            for fit_x, fit_y in res["fits_x"]:
                pts = [
                    QPointF(xi, base_y - (yi / max_val * plot_h))
                    for xi, yi in zip(fit_x, fit_y)
                ]
                painter.drawPolyline(pts)

        # Y
        if "fits_y" in res and "y_raw" in res:
            max_val = np.max(res["y_raw"]) if np.max(res["y_raw"]) > 0 else 1
            painter.setPen(QPen(Qt.GlobalColor.blue, 1.5))
            base_x = orig_w - 5

            for fit_x, fit_y in res["fits_y"]:
                pts = [
                    QPointF(base_x - (yi / max_val * plot_h), xi)
                    for xi, yi in zip(fit_x, fit_y)
                ]
                painter.drawPolyline(pts)
