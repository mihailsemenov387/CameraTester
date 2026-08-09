import numpy as np
from PySide6.QtCharts import (
    QChart,
    QChartView,
    QLineSeries,
    QScatterSeries,
    QValueAxis,
)
from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import QVBoxLayout, QWidget


class Plotter(QWidget):
    intensity_calculated = Signal(float, float)

    def __init__(self):
        super().__init__()
        self._is_draw = False
        self._is_draw_line = False
        self._is_contrast = False
        self._best_x = 0.0
        self._best_y = 0.0

        layout = QVBoxLayout(self)

        # ==========================================
        # НАСТРОЙКА ГРАФИКА X
        # ==========================================
        self.chart_x = QChart()
        self.chart_x.setTitle("Профиль по X")

        # 1. ЯВНОЕ СОЗДАНИЕ ОСЕЙ (Никаких createDefaultAxes!)
        self.axis_x_horiz = QValueAxis()
        self.axis_x_vert = QValueAxis()
        self.chart_x.addAxis(self.axis_x_horiz, Qt.AlignmentFlag.AlignBottom)
        self.chart_x.addAxis(self.axis_x_vert, Qt.AlignmentFlag.AlignLeft)

        # 2. Инициализация серий
        self.series_x_raw = QLineSeries()
        self.series_x_raw.setName("Сырые данные X")

        self.series_x_fit = QLineSeries()
        self.series_x_fit.setName("Гаусс X")
        self.series_x_fit.setPen(QPen(QColor(Qt.GlobalColor.red), 2))

        self.series_x_max_line = QLineSeries()
        self.series_x_max_line.setName("Максимум X")
        self.series_x_max_line.setPen(QPen(QColor(Qt.GlobalColor.darkGray), 1.5, Qt.PenStyle.DashLine))

        self.series_x_max_line_best = QLineSeries()
        self.series_x_max_line_best.setName("Максимум X (лучший)")
        self.series_x_max_line_best.setPen(QPen(QColor(Qt.GlobalColor.darkRed), 1.5, Qt.PenStyle.DashLine))

        # Добавляем базовые серии на график и привязываем к осям
        for s in [self.series_x_raw, self.series_x_fit, self.series_x_max_line, self.series_x_max_line_best]:
            self.chart_x.addSeries(s)
            s.attachAxis(self.axis_x_horiz)
            s.attachAxis(self.axis_x_vert)

        # Ось и серия для нормированного контраста
        self.axis_x_contrast = QValueAxis()
        self.axis_x_contrast.setRange(0, 1)
        self.axis_x_contrast.setTitleText("Норм. контраст")
        self.axis_x_contrast.setLabelFormat("%.2f")
        self.axis_x_contrast.setVisible(False)
        self.chart_x.addAxis(self.axis_x_contrast, Qt.AlignmentFlag.AlignRight)

        self.series_x_contrast = QScatterSeries()
        self.series_x_contrast.setName("Норм. контраст X")
        self.series_x_contrast.setColor(QColor(Qt.GlobalColor.magenta))
        self.series_x_contrast.setMarkerSize(6)
        self.chart_x.addSeries(self.series_x_contrast)
        self.series_x_contrast.attachAxis(self.axis_x_horiz)
        self.series_x_contrast.attachAxis(self.axis_x_contrast)

        # Производная X
        self.series_x_deriv = QLineSeries()
        self.series_x_deriv.setName("Производная X")
        self.series_x_deriv.setPen(QPen(QColor(Qt.GlobalColor.darkYellow), 1))
        self.chart_x.addSeries(self.series_x_deriv)
        self.series_x_deriv.attachAxis(self.axis_x_horiz)
        self.series_x_deriv.attachAxis(self.axis_x_vert)

        # Вторая производная X
        self.series_x_2deriv = QLineSeries()
        self.series_x_2deriv.setName("2-я производная X")
        self.series_x_2deriv.setPen(QPen(QColor(Qt.GlobalColor.darkMagenta), 1))
        self.chart_x.addSeries(self.series_x_2deriv)
        self.series_x_2deriv.attachAxis(self.axis_x_horiz)
        self.series_x_2deriv.attachAxis(self.axis_x_vert)

        # ==========================================
        # НАСТРОЙКА ГРАФИКА Y
        # ==========================================
        self.chart_y = QChart()
        self.chart_y.setTitle("Профиль по Y")

        # 1. ЯВНОЕ СОЗДАНИЕ ОСЕЙ
        self.axis_y_horiz = QValueAxis()
        self.axis_y_vert = QValueAxis()
        self.chart_y.addAxis(self.axis_y_horiz, Qt.AlignmentFlag.AlignBottom)
        self.chart_y.addAxis(self.axis_y_vert, Qt.AlignmentFlag.AlignLeft)

        self.series_y_raw = QLineSeries()
        self.series_y_raw.setName("Сырые данные Y")

        self.series_y_fit = QLineSeries()
        self.series_y_fit.setName("Гаусс Y")
        self.series_y_fit.setPen(QPen(QColor(Qt.GlobalColor.blue), 2))

        self.series_y_max_line = QLineSeries()
        self.series_y_max_line.setName("Максимум Y")
        self.series_y_max_line.setPen(QPen(QColor(Qt.GlobalColor.darkGray), 1.5, Qt.PenStyle.DashLine))

        self.series_y_max_line_best = QLineSeries()
        self.series_y_max_line_best.setName("Максимум Y (лучший)")
        self.series_y_max_line_best.setPen(QPen(QColor(Qt.GlobalColor.darkBlue), 1.5, Qt.PenStyle.DashLine))

        # Привязываем серии к осям
        for s in [self.series_y_raw, self.series_y_fit, self.series_y_max_line, self.series_y_max_line_best]:
            self.chart_y.addSeries(s)
            s.attachAxis(self.axis_y_horiz)
            s.attachAxis(self.axis_y_vert)

        # Ось и серия для нормированного контраста Y
        self.axis_y_contrast = QValueAxis()
        self.axis_y_contrast.setRange(0, 1)
        self.axis_y_contrast.setTitleText("Норм. контраст")
        self.axis_y_contrast.setLabelFormat("%.2f")
        self.axis_y_contrast.setVisible(False)
        self.chart_y.addAxis(self.axis_y_contrast, Qt.AlignmentFlag.AlignRight)

        self.series_y_contrast = QScatterSeries()
        self.series_y_contrast.setName("Норм. контраст Y")
        self.series_y_contrast.setColor(QColor(Qt.GlobalColor.darkCyan))
        self.series_y_contrast.setMarkerSize(6)
        self.chart_y.addSeries(self.series_y_contrast)
        self.series_y_contrast.attachAxis(self.axis_y_horiz)
        self.series_y_contrast.attachAxis(self.axis_y_contrast)

        # Производная Y
        self.series_y_deriv = QLineSeries()
        self.series_y_deriv.setName("Производная Y")
        self.series_y_deriv.setPen(QPen(QColor(Qt.GlobalColor.darkYellow), 1))
        self.chart_y.addSeries(self.series_y_deriv)
        self.series_y_deriv.attachAxis(self.axis_y_horiz)
        self.series_y_deriv.attachAxis(self.axis_y_vert)

        # Вторая производная Y
        self.series_y_2deriv = QLineSeries()
        self.series_y_2deriv.setName("2-я производная Y")
        self.series_y_2deriv.setPen(QPen(QColor(Qt.GlobalColor.darkMagenta), 1))
        self.chart_y.addSeries(self.series_y_2deriv)
        self.series_y_2deriv.attachAxis(self.axis_y_horiz)
        self.series_y_2deriv.attachAxis(self.axis_y_vert)

        layout.addWidget(QChartView(self.chart_x))
        layout.addWidget(QChartView(self.chart_y))


    def update_line_vis(self, val):
        self._is_draw_line = val

    def update_is_draw(self, val):
        self._is_draw = val

    def set_contrast_mode(self, enabled):
        self._is_contrast = enabled
        self.reset_best()

    def clear_canvas(self):
        self.series_x_raw.clear()
        self.series_x_fit.clear()
        self.series_x_max_line.clear()
        self.series_x_max_line_best.clear()
        self.series_x_contrast.clear()
        self.series_x_deriv.clear()
        self.series_x_2deriv.clear()

        self.series_y_raw.clear()
        self.series_y_fit.clear()
        self.series_y_max_line.clear()
        self.series_y_max_line_best.clear()
        self.series_y_contrast.clear()
        self.series_y_deriv.clear()
        self.series_y_2deriv.clear()
        self.reset_best()

    def reset_best(self):
        self._best_x = 0.0
        self._best_y = 0.0

    def update_data(self, data: dict = {}):
        if not data:
            return

        try:
            # 1. Нормированный контраст
            has_norm = "x_contrast_pts" in data and "y_contrast_pts" in data
            if has_norm:
                self.series_x_contrast.replace([QPointF(float(px), float(pv)) for px, pv in zip(data["x_contrast_pts"], data["x_contrast_vals"])])
                self.series_y_contrast.replace([QPointF(float(py), float(pv)) for py, pv in zip(data["y_contrast_pts"], data["y_contrast_vals"])])
                self.axis_x_contrast.setVisible(True)
                self.axis_y_contrast.setVisible(True)
            else:
                self.series_x_contrast.clear()
                self.series_y_contrast.clear()
                self.axis_x_contrast.setVisible(False)
                self.axis_y_contrast.setVisible(False)

            has_coords = "x" in data and "y" in data and len(data["x"]) > 0 and len(data["y"]) > 0
            if not has_coords:
                return

            # Защита от нулевого Range осей по X (если ROI шириной 1 пиксель)
            x_max = max(1.0, float(data["x"][-1]))
            y_max = max(1.0, float(data["y"][-1]))

            # 2. Сырые профили
            has_raw = "x_raw" in data and "y_raw" in data
            if has_raw:
                self.series_x_raw.replace([QPointF(float(a), float(b)) for a, b in zip(data["x"], data["x_raw"])])
                self.series_y_raw.replace([QPointF(float(a), float(b)) for a, b in zip(data["y"], data["y_raw"])])
            else:
                self.series_x_raw.clear()
                self.series_y_raw.clear()

            # 3. Фит (Гаусс)
            has_fit_x = "total_fit_x" in data
            has_fit_y = "total_fit_y" in data
            if has_fit_x:
                self.series_x_fit.replace([QPointF(float(xi), float(yi)) for xi, yi in enumerate(data["total_fit_x"])])
            else:
                self.series_x_fit.clear()

            if has_fit_y:
                self.series_y_fit.replace([QPointF(float(xi), float(yi)) for xi, yi in enumerate(data["total_fit_y"])])
            else:
                self.series_y_fit.clear()

            # 4. Обновление пиков интенсивности
            has_display = has_raw
            if has_fit_x:
                curr_max_x = float(np.max(data["total_fit_x"]))
                self._best_x = max(self._best_x, curr_max_x)
            elif has_raw:
                curr_max_x = float(np.max(data["x_raw"]))
            else:
                curr_max_x = 0.0

            if has_fit_y:
                curr_max_y = float(np.max(data["total_fit_y"]))
                self._best_y = max(self._best_y, curr_max_y)
            elif has_raw:
                curr_max_y = float(np.max(data["y_raw"]))
            else:
                curr_max_y = 0.0

            # 5. Границы главных осей (ВАЖНО: передаем best_val, чтобы график не сжимался)
            best_x_to_pass = self._best_x if self._is_draw_line else None
            best_y_to_pass = self._best_y if self._is_draw_line else None
            lo_x, hi_x = self._main_bounds(data, "x_raw", "total_fit_x", best_x_to_pass)
            lo_y, hi_y = self._main_bounds(data, "y_raw", "total_fit_y", best_y_to_pass)

            # 6. Производная (нормализованная под текущие границы осей)
            self._draw_overlay_norm(data, "x_deriv", data["x"], self.series_x_deriv, lo_x, hi_x)
            self._draw_overlay_norm(data, "y_deriv", data["y"], self.series_y_deriv, lo_y, hi_y)

            # 6b. Вторая производная (тот же оверлей)
            self._draw_overlay_norm(data, "x_2deriv", data["x"], self.series_x_2deriv, lo_x, hi_x)
            self._draw_overlay_norm(data, "y_2deriv", data["y"], self.series_y_2deriv, lo_y, hi_y)

            # 7. Линии уровня максимума
            if self._is_draw_line and has_display:
                self.series_x_max_line.replace([QPointF(0, curr_max_x), QPointF(x_max, curr_max_x)])
                self.series_y_max_line.replace([QPointF(0, curr_max_y), QPointF(y_max, curr_max_y)])

                if has_fit_x:
                    self.series_x_max_line_best.replace([QPointF(0, self._best_x), QPointF(x_max, self._best_x)])
                else:
                    self.series_x_max_line_best.clear()

                if has_fit_y:
                    self.series_y_max_line_best.replace([QPointF(0, self._best_y), QPointF(y_max, self._best_y)])
                else:
                    self.series_y_max_line_best.clear()
            else:
                self.series_x_max_line.clear()
                self.series_x_max_line_best.clear()
                self.series_y_max_line.clear()
                self.series_y_max_line_best.clear()

            # Отправляем сигналы UI
            if has_display:
                self.intensity_calculated.emit(float(curr_max_x), float(curr_max_y))

            # 8. Финальное обновление границ через явные оси!
            self.axis_x_horiz.setRange(0, x_max)
            self.axis_x_vert.setRange(lo_x, hi_x)
            self.axis_y_horiz.setRange(0, y_max)
            self.axis_y_vert.setRange(lo_y, hi_y)

        except Exception as e:
            print(f"Plotter Render Error: {e}")

    @staticmethod
    def _main_bounds(data, raw_key, fit_key, best_val=None):
        """Вертикальные границы главной оси с учетом сохраненного максимума."""
        parts = []
        if raw_key in data and len(data[raw_key]):
            parts.append(data[raw_key])
        if fit_key in data and len(data[fit_key]):
            parts.append(data[fit_key])

        if not parts:
            if best_val is not None and best_val > 0:
                return 0.0, float(best_val) * 1.1
            return 0.0, 1.0

        vmin = float(min(np.min(p) for p in parts))
        vmax = float(max(np.max(p) for p in parts))

        # Если включена отрисовка "лучшей линии", то ось не должна падать ниже нее
        if best_val is not None and best_val > vmax:
            vmax = float(best_val)

        if vmax <= vmin:
            return vmin, vmin + 1.0

        pad = (vmax - vmin) * 0.08
        return vmin - pad, vmax + pad

    def _draw_overlay_norm(self, data, key, coords, series, lo, hi):
        if key not in data:
            series.clear()
            return
        v = data[key]
        vmin = float(np.min(v))
        vmax = float(np.max(v))
        if vmax > vmin:
            scale = (hi - lo) / (vmax - vmin)
            pts = [QPointF(float(c), float(lo + (val - vmin) * scale)) for c, val in zip(coords, v)]
        else:
            mid = (lo + hi) / 2.0
            pts = [QPointF(float(c), mid) for c in coords]
        series.replace(pts)
