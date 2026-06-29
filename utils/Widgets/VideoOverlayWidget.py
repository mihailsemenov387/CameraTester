import numpy as np
from PySide6.QtCore import QPointF, QSize, Qt
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

        GlobalBus.instance().is_draw_cross.connect(self._cross_logic)

    def _cross_logic(self, data):
        self.is_draw_cross = data

    def update_data(self, results, w, h):
        self.results = results
        self.image_size = (w, h)
        self.update()

    def clear(self):
        self.results = None
        self.update()

    # def paintEvent(self, event):
    #     if not self.results or not self.image_size:
    #         return
    #     painter = QPainter(self)
    #     painter.setRenderHint(QPainter.Antialiasing)

    #     rect = self.rect()
    #     orig_w, orig_h = self.image_size
    #     scaled_size = QSize(orig_w, orig_h).scaled(
    #         rect.size(), Qt.AspectRatioMode.KeepAspectRatio
    #     )
    #     x_off = (rect.width() - scaled_size.width()) // 2
    #     y_off = (rect.height() - scaled_size.height()) // 2
    #     scale = scaled_size.width() / orig_w

    #     res = self.results

    #     if self.is_draw_cross:
    #         painter.setPen(QPen(QColor(255, 0, 0, 150), 1, Qt.PenStyle.DashLine))
    #         cx = x_off + res.get("mu_x", 0) * scale
    #         cy = y_off + res.get("mu_y", 0) * scale
    #         painter.drawLine(x_off, cy, x_off + scaled_size.width(), cy)
    #         painter.drawLine(cx, y_off, cx, y_off + scaled_size.height())

    #     self._draw_projections(painter, res, x_off, y_off, scaled_size, scale)

    # def _draw_projections(self, painter, res, x_off, y_off, scaled_size, scale):
    #     plot_h = 70

    #     # X
    #     if "fits_x" in res and "x_raw" in res:
    #         max_val = np.max(res["x_raw"]) if np.max(res["x_raw"]) > 0 else 1
    #         painter.setPen(QPen(Qt.GlobalColor.blue, 2))
    #         base_y = y_off + scaled_size.height() - 5

    #         for fit_x, fit_y in res["fits_x"]:
    #             pts = [
    #                 QPointF(x_off + (xi * scale), base_y - (yi / max_val * plot_h))
    #                 for xi, yi in zip(fit_x, fit_y)
    #             ]
    #             painter.drawPolyline(pts)

    #     # Y
    #     if "fits_y" in res and "y_raw" in res:
    #         max_val = np.max(res["y_raw"]) if np.max(res["y_raw"]) > 0 else 1
    #         painter.setPen(QPen(Qt.GlobalColor.red, 2))
    #         base_x = x_off + scaled_size.width() - 5

    #         for fit_x, fit_y in res["fits_y"]:
    #             pts = [
    #                 QPointF(base_x - (yi / max_val * plot_h), y_off + (xi * scale))
    #                 for xi, yi in zip(fit_x, fit_y)
    #             ]
    #             painter.drawPolyline(pts)

    def paintEvent(self, event):
        if not self.results or not self.image_size:
            return
        painter = QPainter(self)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        rect = self.rect()
        orig_w, orig_h = self.image_size

        scale_x = rect.width() / orig_w
        scale_y = rect.height() / orig_h
        scale = min(scale_x, scale_y)

        target_w = orig_w * scale
        target_h = orig_h * scale
        x_off = (rect.width() - target_w) / 2
        y_off = (rect.height() - target_h) / 2

        painter.translate(x_off, y_off)
        painter.scale(scale, scale)

        res = self.results

        if self.is_draw_cross:
            cx = res.get("mu_x", 0)
            cy = res.get("mu_y", 0)

            painter.setPen(QPen(QColor(255, 0, 0, 200), 1.5, Qt.PenStyle.SolidLine))

            size = 6  # cross size
            gap = 1  # gap size

            painter.drawLine(int(cx - size), int(cy), int(cx - gap), int(cy))
            painter.drawLine(int(cx + gap), int(cy), int(cx + size), int(cy))

            painter.drawLine(int(cx), int(cy - size), int(cx), int(cy - gap))
            painter.drawLine(int(cx), int(cy + gap), int(cx), int(cy + size))

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
