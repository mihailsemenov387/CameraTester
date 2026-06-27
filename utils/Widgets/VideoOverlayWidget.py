import numpy as np
from PySide6.QtCore import QPointF, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class SingleGaussOverlayWidget(QWidget):
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


class MultiGaussOverlayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.results = None
        self.image_size = None

    def update_data(self, results: dict, orig_width: int, orig_height: int):
        """
        results должен содержать:
        - 'x_raw', 'y_raw': сырые данные профилей
        - 'fits_x', 'fits_y': списки кортежей (x_coords, y_values) для каждого Гаусса
        - 'peaks_x', 'peaks_y': координаты центров пиков
        """
        self.results = results
        self.image_size = (orig_width, orig_height)
        self.update()

    def clear(self):
        self.results = None
        self.update()

    def paintEvent(self, event):
        if not self.results or not self.image_size:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()

        orig_w, orig_h = self.image_size
        orig_size = QSize(orig_w, orig_h)
        scaled_size = orig_size.scaled(rect.size(), Qt.AspectRatioMode.KeepAspectRatio)

        x_off = (rect.width() - scaled_size.width()) // 2
        y_off = (rect.height() - scaled_size.height()) // 2
        scale = scaled_size.width() / orig_w

        res = self.results

        # --- РИСУЕМ ПО ОСИ X (Сверху кадра) ---
        if "x_raw" in res:
            self._draw_multi_peaks(
                painter,
                raw_data=res["x_raw"],
                fits=res.get("fits_x", []),
                peaks=res.get("peaks_x", []),
                offset_x=x_off,
                offset_y=y_off,
                scale=scale,
                is_x_axis=True,
                color=Qt.GlobalColor.yellow,
                baseline_shift=10,  # отступ от края внутрь
            )

        # --- РИСУЕМ ПО ОСИ Y (Слева кадра) ---
        if "y_raw" in res:
            self._draw_multi_peaks(
                painter,
                raw_data=res["y_raw"],
                fits=res.get("fits_y", []),
                peaks=res.get("peaks_y", []),
                offset_x=x_off,
                offset_y=y_off,
                scale=scale,
                is_x_axis=False,
                color=Qt.GlobalColor.cyan,
                baseline_shift=10,
            )

    def _draw_multi_peaks(
        self,
        painter,
        raw_data,
        fits,
        peaks,
        offset_x,
        offset_y,
        scale,
        is_x_axis,
        color,
        baseline_shift,
    ):
        plot_depth = 80  # Высота/ширина зоны графиков
        max_val = np.max(raw_data) if np.max(raw_data) > 0 else 1

        # 1. Рисуем сырой профиль (тонкая белая линия для контекста)
        painter.setPen(QPen(QColor(200, 200, 200, 100), 1))

        raw_points = []
        for i, val in enumerate(raw_data):
            norm_val = val / max_val * plot_depth
            if is_x_axis:
                px = offset_x + (i * scale)
                py = offset_y + baseline_shift + plot_depth - norm_val
            else:
                px = offset_x + baseline_shift + plot_depth - norm_val
                py = offset_y + (i * scale)
            raw_points.append(QPointF(px, py))

        if len(raw_points) > 1:
            painter.drawPolyline(raw_points)

        # 2. Рисуем каждый фит Гаусса (толстая цветная линия)
        painter.setPen(QPen(color, 2))
        for fit_x, fit_y in fits:
            fit_points = []
            for fx, fy in zip(fit_x, fit_y):
                norm_fy = fy / max_val * plot_depth
                if is_x_axis:
                    px = offset_x + (fx * scale)
                    py = offset_y + baseline_shift + plot_depth - norm_fy
                else:
                    px = offset_x + baseline_shift + plot_depth - norm_fy
                    py = offset_y + (fx * scale)
                fit_points.append(QPointF(px, py))

            if len(fit_points) > 1:
                painter.drawPolyline(fit_points)

        # 3. Рисуем маркеры пиков (крестики)
        painter.setPen(QPen(Qt.GlobalColor.red, 2))
        marker_size = 4
        for p_idx in peaks:
            if is_x_axis:
                # Центр пика на базовой линии
                cx = offset_x + (p_idx * scale)
                cy = offset_y + baseline_shift + plot_depth
            else:
                cx = offset_x + baseline_shift + plot_depth
                cy = offset_y + (p_idx * scale)

            painter.drawLine(
                cx - marker_size, cy - marker_size, cx + marker_size, cy + marker_size
            )
            painter.drawLine(
                cx + marker_size, cy - marker_size, cx - marker_size, cy + marker_size
            )


class UnifiedBeamOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.results = None
        self.image_size = None

    def update_data(self, results, w, h):
        self.results = results
        self.image_size = (w, h)
        self.update()

    def clear(self):
        self.results = None
        self.update()

    def paintEvent(self, event):
        if not self.results or not self.image_size: return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Расчет масштаба
        rect = self.rect()
        orig_w, orig_h = self.image_size
        scaled_size = QSize(orig_w, orig_h).scaled(rect.size(), Qt.AspectRatioMode.KeepAspectRatio)
        x_off = (rect.width() - scaled_size.width()) // 2
        y_off = (rect.height() - scaled_size.height()) // 2
        scale = scaled_size.width() / orig_w

        res = self.results

        # 1. Перекрестие (по mu_x, mu_y)
        painter.setPen(QPen(QColor(255, 0, 0, 150), 1, Qt.PenStyle.DashLine))
        cx = x_off + res.get('mu_x', 0) * scale
        cy = y_off + res.get('mu_y', 0) * scale
        painter.drawLine(x_off, cy, x_off + scaled_size.width(), cy)
        painter.drawLine(cx, y_off, cx, y_off + scaled_size.height())

        # 2. Рисуем Гауссианы (fits_x и fits_y)
        self._draw_projections(painter, res, x_off, y_off, scaled_size, scale)

    def _draw_projections(self, painter, res, x_off, y_off, scaled_size, scale):
        plot_h = 70 # Высота графиков

        # Отрисовка X (снизу вверх)
        if "fits_x" in res and "x_raw" in res:
            max_val = np.max(res["x_raw"]) if np.max(res["x_raw"]) > 0 else 1
            painter.setPen(QPen(Qt.GlobalColor.yellow, 2))
            # Базовая линия — низ картинки
            base_y = y_off + scaled_size.height() - 5

            for fit_x, fit_y in res["fits_x"]:
                pts = [QPointF(x_off + (xi * scale), base_y - (yi / max_val * plot_h))
                       for xi, yi in zip(fit_x, fit_y)]
                painter.drawPolyline(pts)

        # Отрисовка Y (справа налево)
        if "fits_y" in res and "y_raw" in res:
            max_val = np.max(res["y_raw"]) if np.max(res["y_raw"]) > 0 else 1
            painter.setPen(QPen(Qt.GlobalColor.cyan, 2))
            base_x = x_off + scaled_size.width() - 5

            for fit_x, fit_y in res["fits_y"]:
                # Здесь fit_x — это координаты по вертикали (y), а fit_y — значения
                pts = [QPointF(base_x - (yi / max_val * plot_h), y_off + (xi * scale))
                       for xi, yi in zip(fit_x, fit_y)]
                painter.drawPolyline(pts)
