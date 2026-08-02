from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QSizePolicy, QWidget

import sys

# Отображает кадр с возможностью выделить зону интереса (ROI):
# - LMB: создать/передвинуть рамку, углы — ресайз
# - колесо: зум по центру курсора
# - средняя кнопка: пан при зуме
# - двойной клик: сбросить ROI
# Всё вне рамки затемняется. ROI хранится в координатах исходного кадра.

MIN_ROI = 10
MAX_ZOOM = 10.0
HANDLE_PX = 10

# Windows VK-код клавиши R (запасной вариант для нелатинских раскладок)
_VK_R = 0x52


class ROIWidget(QWidget):
    roi_changed = Signal(float, float, float, float)  # x, y, w, h в пикселях кадра
    view_changed = Signal()  # зум/пан изменились — просим оверлей перерисоваться

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_image = None  # QPixmap
        self.zoom = 1.0
        self.pan = QPointF(0.0, 0.0)
        self.roi = QRectF()

        self._mode = None  # "create" | "move" | "resize" | "pan"
        self._corner = None
        self._drag_start_widget = None
        self._drag_start_img = None
        self._roi_orig = None

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(320, 240)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    # ---------- Публичный API ----------
    def update_image(self, image: QPixmap):
        self.current_image = image
        self.update()

    def has_roi(self) -> bool:
        return self.current_image is not None and not self.roi.isNull()

    def get_transform(self):
        """Возвращает (x0, y0, scale): перевод из координат кадра в координаты виджета."""
        rect = self.rect()
        if self.current_image is None or self.current_image.isNull():
            return 0.0, 0.0, 1.0
        cam_w = self.current_image.width()
        cam_h = self.current_image.height()
        base = min(rect.width() / cam_w, rect.height() / cam_h)
        scale = base * self.zoom
        x0 = (rect.width() - cam_w * scale) / 2 + self.pan.x()
        y0 = (rect.height() - cam_h * scale) / 2 + self.pan.y()
        return x0, y0, scale

    def widget_to_image(self, px, py) -> QPointF:
        x0, y0, s = self.get_transform()
        return QPointF((px - x0) / s, (py - y0) / s)

    def image_to_widget(self, ix, iy) -> QPointF:
        x0, y0, s = self.get_transform()
        return QPointF(x0 + ix * s, y0 + iy * s)

    def _image_rect(self) -> QRectF:
        if self.current_image is None or self.current_image.isNull():
            return QRectF()
        return QRectF(0, 0, self.current_image.width(), self.current_image.height())

    # ---------- Хелперы ----------
    def _hit_handle(self, img) -> str:
        _, _, s = self.get_transform()
        thresh = HANDLE_PX / s
        corners = {
            "tl": self.roi.topLeft(),
            "tr": self.roi.topRight(),
            "bl": self.roi.bottomLeft(),
            "br": self.roi.bottomRight(),
        }
        for name, c in corners.items():
            if (c - img).manhattanLength() <= thresh:
                return name
        return None

    def _apply_resize(self, corner, pt):
        r = QRectF(self._roi_orig)
        if corner == "tl":
            r.setTopLeft(pt)
        elif corner == "tr":
            r.setTopRight(pt)
        elif corner == "bl":
            r.setBottomLeft(pt)
        elif corner == "br":
            r.setBottomRight(pt)
        r = r.normalized().intersected(self._image_rect())
        if r.width() < MIN_ROI or r.height() < MIN_ROI:
            r = QRectF(self._roi_orig)
        self.roi = r

    def _clamp_move(self, r):
        ir = self._image_rect()
        if ir.isNull():
            return r
        if r.left() < 0:
            r.moveLeft(0)
        if r.top() < 0:
            r.moveTop(0)
        if r.right() > ir.right():
            r.moveRight(ir.right())
        if r.bottom() > ir.bottom():
            r.moveBottom(ir.bottom())
        return r

    # ---------- События мыши ----------
    def mousePressEvent(self, event):
        if self.current_image is None:
            return

        if event.button() == Qt.MouseButton.MiddleButton:
            self._mode = "pan"
            self._drag_start_widget = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return

        if event.button() != Qt.MouseButton.LeftButton:
            return

        img = self.widget_to_image(event.position().x(), event.position().y())

        if self.has_roi():
            corner = self._hit_handle(img)
            if corner:
                self._mode = "resize"
                self._corner = corner
            elif self.roi.contains(img):
                self._mode = "move"
                self._drag_start_img = img
            else:
                self._mode = "create"
                self.roi = QRectF(img, img)
        else:
            self._mode = "create"
            self.roi = QRectF(img, img)

        self._roi_orig = QRectF(self.roi)
        self.update()
        event.accept()

    def mouseMoveEvent(self, event):
        img = self.widget_to_image(event.position().x(), event.position().y())

        if self._mode is None:
            if self.has_roi():
                if self._hit_handle(img):
                    self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                elif self.roi.contains(img):
                    self.setCursor(Qt.CursorShape.SizeAllCursor)
                else:
                    self.setCursor(Qt.CursorShape.CrossCursor)
            else:
                self.setCursor(Qt.CursorShape.CrossCursor)
            return

        if self._mode == "pan":
            delta = event.position() - self._drag_start_widget
            self._drag_start_widget = event.position()
            self.pan += delta
            self.view_changed.emit()
        elif self._mode == "create":
            self.roi = QRectF(self._roi_orig.topLeft(), img).normalized()
            self.roi = self.roi.intersected(self._image_rect())
        elif self._mode == "move":
            delta = img - self._drag_start_img
            self.roi = self._clamp_move(self._roi_orig.translated(delta))
        elif self._mode == "resize":
            self._apply_resize(self._corner, img)

        self.update()
        event.accept()

    def mouseReleaseEvent(self, event):
        if self._mode == "pan":
            self.setCursor(Qt.CursorShape.CrossCursor)
        self._mode = None
        self._corner = None
        self.update()
        self.roi_changed.emit(
            self.roi.x() if self.has_roi() else 0,
            self.roi.y() if self.has_roi() else 0,
            self.roi.width() if self.has_roi() else 0,
            self.roi.height() if self.has_roi() else 0,
        )
        event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.roi = QRectF()
            self._mode = None
            self.update()
            self.roi_changed.emit(0, 0, 0, 0)
            event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_R or self._native_key_is_r(event):
            self.zoom = 1.0
            self.pan = QPointF(0.0, 0.0)
            self.view_changed.emit()
            self.update()
            event.accept()
            return
        super().keyPressEvent(event)

    @staticmethod
    def _native_key_is_r(event):
        """Запасная проверка по сырому VK-коду: Qt::key() для латинских клавиш
        не зависит от раскладки, но на всякий случай дублируем Windows-кодом."""
        try:
            if sys.platform.startswith("win"):
                return event.nativeVirtualKey() == _VK_R
        except Exception:
            pass
        return False

    def wheelEvent(self, event):
        if self.current_image is None:
            return
        factor = 1.2 if event.angleDelta().y() > 0 else 1.0 / 1.2
        new_zoom = max(1.0, min(MAX_ZOOM, self.zoom * factor))
        if abs(new_zoom - self.zoom) < 1e-6:
            return

        rect = self.rect()
        x0, y0, s = self.get_transform()
        p = event.position()
        # сохраняем точку кадра под курсором
        ix = (p.x() - x0) / s
        iy = (p.y() - y0) / s

        self.zoom = new_zoom
        cam_w = self.current_image.width()
        cam_h = self.current_image.height()
        s2 = min(rect.width() / cam_w, rect.height() / cam_h) * new_zoom
        self.pan = QPointF(
            p.x() - ix * s2 - (rect.width() - cam_w * s2) / 2,
            p.y() - iy * s2 - (rect.height() - cam_h * s2) / 2,
        )
        self.view_changed.emit()
        self.update()
        event.accept()

    # ---------- Отрисовка ----------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        rect = self.rect()
        p.fillRect(rect, Qt.GlobalColor.black)

        if self.current_image is None or self.current_image.isNull():
            return

        x0, y0, s = self.get_transform()
        p.save()
        p.translate(x0, y0)
        p.scale(s, s)
        p.drawPixmap(0, 0, self.current_image)
        p.restore()

        if self.has_roi():
            self._draw_roi(p, x0, y0, s)

    def _draw_roi(self, p, x0, y0, s):
        ir = self._image_rect()
        r = self.roi

        def to_rect(ir_rect):
            return QRectF(
                x0 + ir_rect.x() * s,
                y0 + ir_rect.y() * s,
                ir_rect.width() * s,
                ir_rect.height() * s,
            )

        # Затемнение всего, что вне рамки
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 150))
        for q in (
            QRectF(ir.x(), ir.y(), ir.width(), r.top() - ir.y()),
            QRectF(ir.x(), r.bottom(), ir.width(), ir.bottom() - r.bottom()),
            QRectF(ir.x(), r.top(), r.left() - ir.x(), r.height()),
            QRectF(r.right(), r.top(), ir.right() - r.right(), r.height()),
        ):
            if q.width() > 0 and q.height() > 0:
                p.drawRect(to_rect(q))

        # Рамка
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(255, 200, 0), 1.5))
        p.drawRect(to_rect(r))

        # Угловые ручки (постоянный размер в пикселях экрана)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 200, 0))
        half = HANDLE_PX / 2
        for c in (r.topLeft(), r.topRight(), r.bottomLeft(), r.bottomRight()):
            p.drawRect(
                QRectF(
                    x0 + c.x() * s - half,
                    y0 + c.y() * s - half,
                    HANDLE_PX,
                    HANDLE_PX,
                )
            )
