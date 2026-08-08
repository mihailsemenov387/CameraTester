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
        # Исправили флаги под ваши методы
        self._is_draw = False  # Отвечает за отрисовку графиков вообще
        self._is_draw_line = False  #   Отвечает за линии максимума
        self._is_contrast = False  #   Режим контраста (производная профиля)
        self._best_x = 0.0
        self._best_y = 0.0

        layout = QVBoxLayout(self)

        # --- НАСТРОЙКА ГРАФИКА X ---
        self.series_x_raw = QLineSeries()
        self.series_x_raw.setName("Сырые данные X")

        self.series_x_fit = QLineSeries()
        self.series_x_fit.setName("Гаусс X")
        self.series_x_fit.setPen(QPen(QColor(Qt.GlobalColor.red), 2))

        # Новая серия для вертикальной линии максимума X
        self.series_x_max_line = QLineSeries()
        self.series_x_max_line.setName("Максимум X")
        # Делаем линию пунктирной (DashLine) серого цвета
        pen_max_x = QPen(QColor(Qt.GlobalColor.darkGray), 1.5, Qt.PenStyle.DashLine)
        self.series_x_max_line.setPen(pen_max_x)

        self.series_x_max_line_best = QLineSeries()
        self.series_x_max_line_best.setName("Максимум X (наилучший)")
        # Делаем линию пунктирной (DashLine) серого цвета
        pen_max_x = QPen(QColor(Qt.GlobalColor.darkRed), 1.5, Qt.PenStyle.DashLine)
        self.series_x_max_line_best.setPen(pen_max_x)

        self.chart_x = QChart()
        self.chart_x.addSeries(self.series_x_raw)
        self.chart_x.addSeries(self.series_x_fit)
        self.chart_x.addSeries(self.series_x_max_line)  # Добавили на график
        self.chart_x.addSeries(self.series_x_max_line_best)  # Добавили на график
        self.chart_x.createDefaultAxes()
        self.chart_x.setTitle("Профиль по X")

        # Нормированный контраст (Майкельсон) — точки со своей осью 0..1
        self.series_x_contrast = QScatterSeries()
        self.series_x_contrast.setName("Норм. контраст X")
        self.series_x_contrast.setColor(QColor(Qt.GlobalColor.magenta))
        self.series_x_contrast.setMarkerSize(6)

        self.axis_x_contrast = QValueAxis()
        self.axis_x_contrast.setRange(0, 1)
        self.axis_x_contrast.setTitleText("Норм. контраст")
        self.axis_x_contrast.setLabelFormat("%.2f")
        self.axis_x_contrast.setVisible(False)

        self.chart_x.addSeries(self.series_x_contrast)
        self.chart_x.addAxis(self.axis_x_contrast, Qt.AlignmentFlag.AlignRight)
        self.series_x_contrast.attachAxis(
            self.chart_x.axes(Qt.Orientation.Horizontal)[0]
        )
        self.series_x_contrast.attachAxis(self.axis_x_contrast)

        # Производная профиля (контраст) — оверлей поверх профиля,
        # рисуется на главных осях, нормализованная под размах профиля.
        self.series_x_deriv = QLineSeries()
        self.series_x_deriv.setName("Производная X")
        self.series_x_deriv.setPen(QPen(QColor(Qt.GlobalColor.darkYellow), 1))
        self.chart_x.addSeries(self.series_x_deriv)
        self.series_x_deriv.attachAxis(
            self.chart_x.axes(Qt.Orientation.Horizontal)[0]
        )
        self.series_x_deriv.attachAxis(self.chart_x.axes(Qt.Orientation.Vertical)[0])

        # --- НАСТРОЙКА ГРАФИКА Y ---
        self.series_y_raw = QLineSeries()
        self.series_y_raw.setName("Сырые данные Y")

        self.series_y_fit = QLineSeries()
        self.series_y_fit.setName("Гаусс Y")
        self.series_y_fit.setPen(QPen(QColor(Qt.GlobalColor.blue), 2))

        # Новая серия для вертикальной линии максимума Y
        self.series_y_max_line = QLineSeries()
        self.series_y_max_line.setName("Максимум Y")
        pen_max_y = QPen(QColor(Qt.GlobalColor.darkGray), 1.5, Qt.PenStyle.DashLine)
        self.series_y_max_line.setPen(pen_max_y)

        self.series_y_max_line_best = QLineSeries()
        self.series_y_max_line_best.setName("Максимум Y (наилучший)")
        pen_max_y = QPen(QColor(Qt.GlobalColor.darkBlue), 1.5, Qt.PenStyle.DashLine)
        self.series_y_max_line_best.setPen(pen_max_y)

        self.chart_y = QChart()
        self.chart_y.addSeries(self.series_y_raw)
        self.chart_y.addSeries(self.series_y_fit)
        self.chart_y.addSeries(self.series_y_max_line)  # Добавили на график
        self.chart_y.addSeries(self.series_y_max_line_best)  # Добавили на график
        self.chart_y.createDefaultAxes()
        self.chart_y.setTitle("Профиль по Y")

        # Нормированный контраст по Y — точки со своей осью 0..1
        self.series_y_contrast = QScatterSeries()
        self.series_y_contrast.setName("Норм. контраст Y")
        self.series_y_contrast.setColor(QColor(Qt.GlobalColor.darkCyan))
        self.series_y_contrast.setMarkerSize(6)

        self.axis_y_contrast = QValueAxis()
        self.axis_y_contrast.setRange(0, 1)
        self.axis_y_contrast.setTitleText("Норм. контраст")
        self.axis_y_contrast.setLabelFormat("%.2f")
        self.axis_y_contrast.setVisible(False)

        self.chart_y.addSeries(self.series_y_contrast)
        self.chart_y.addAxis(self.axis_y_contrast, Qt.AlignmentFlag.AlignRight)
        self.series_y_contrast.attachAxis(
            self.chart_y.axes(Qt.Orientation.Horizontal)[0]
        )
        self.series_y_contrast.attachAxis(self.axis_y_contrast)

        # Производная профиля по Y (аналог серии по X).
        self.series_y_deriv = QLineSeries()
        self.series_y_deriv.setName("Производная Y")
        self.series_y_deriv.setPen(QPen(QColor(Qt.GlobalColor.darkYellow), 1))
        self.chart_y.addSeries(self.series_y_deriv)
        self.series_y_deriv.attachAxis(
            self.chart_y.axes(Qt.Orientation.Horizontal)[0]
        )
        self.series_y_deriv.attachAxis(self.chart_y.axes(Qt.Orientation.Vertical)[0])

        layout.addWidget(QChartView(self.chart_x))
        layout.addWidget(QChartView(self.chart_y))

    def update_line_vis(self, val):
        self._is_draw_line = val

    def update_is_draw(self, val):
        self._is_draw = val

    def set_contrast_mode(self, enabled):
        """Включает/выключает режим контраста. Сбрасывает накопленный
        «лучший максимум», чтобы ось пересчиталась под текущие данные."""
        self._is_contrast = enabled
        self._best_x = self._best_y = 0

    def clear_canvas(self):
        # Если рисовать запрещено, очищаем всё и выходим
        print("[DEBUG]: clear canvas")
        self.series_x_raw.clear()
        self.series_x_fit.clear()
        self.series_x_max_line.clear()
        self.series_x_max_line_best.clear()
        self.series_x_contrast.clear()
        self.series_x_deriv.clear()
        self.series_y_raw.clear()
        self.series_y_fit.clear()
        self.series_y_max_line.clear()
        self.series_y_max_line_best.clear()
        self.series_y_contrast.clear()
        self.series_y_deriv.clear()
        self._best_x = self._best_y = 0

    def reset_best(self):
        self._best_x = self._best_y = 0

    def update_data(self, data: dict = {}):
        if not data:
            return

        try:
            # --- Нормированный контраст (Майкельсон) — точки + правая ось 0..1 ---
            has_norm = "x_contrast_pts" in data and "y_contrast_pts" in data
            if has_norm:
                self.series_x_contrast.replace(
                    [
                        QPointF(float(px), float(pv))
                        for px, pv in zip(
                            data["x_contrast_pts"], data["x_contrast_vals"]
                        )
                    ]
                )
                self.series_y_contrast.replace(
                    [
                        QPointF(float(py), float(pv))
                        for py, pv in zip(
                            data["y_contrast_pts"], data["y_contrast_vals"]
                        )
                    ]
                )
                self.axis_x_contrast.setVisible(True)
                self.axis_y_contrast.setVisible(True)
            else:
                # Выключили норм. контраст — прячем точки и ось
                self.series_x_contrast.clear()
                self.series_y_contrast.clear()
                self.axis_x_contrast.setVisible(False)
                self.axis_y_contrast.setVisible(False)

            # Координаты нужны для любых построений (профиль/фит/точки).
            has_coords = (
                "x" in data and "y" in data and len(data["x"]) > 0 and len(data["y"]) > 0
            )
            if not has_coords:
                return
            x_max = float(data["x"][-1])
            y_max = float(data["y"][-1])

# 1. Профиль (сырые данные либо производная, если выбран контраст).
            #    Presence-driven: нет профиля в данных — старый профиль не оставляем.
            has_raw = "x_raw" in data and "y_raw" in data
            if has_raw:
                self.series_x_raw.replace(
                    [
                        QPointF(float(a), float(b))
                        for a, b in zip(data["x"], data["x_raw"])
                    ]
                )
                self.series_y_raw.replace(
                    [
                        QPointF(float(a), float(b))
                        for a, b in zip(data["y"], data["y_raw"])
                    ]
                )
            else:
                self.series_x_raw.clear()
                self.series_y_raw.clear()

            # 2. Фит (Гаусс). Нет фита в новых данных — не оставляем устаревший.
            has_fit_x = "total_fit_x" in data
            has_fit_y = "total_fit_y" in data
            if has_fit_x:
                self.series_x_fit.replace(
                    [
                        QPointF(float(xi), float(yi))
                        for xi, yi in enumerate(data["total_fit_x"])
                    ]
                )
            else:
                self.series_x_fit.clear()
            if has_fit_y:
                self.series_y_fit.replace(
                    [
                        QPointF(float(xi), float(yi))
                        for xi, yi in enumerate(data["total_fit_y"])
                    ]
                )
            else:
                self.series_y_fit.clear()

            # 5. Границы главных осей — ТОЛЬКО по профилю и фиту.
            #    Контрастные серии (производная, норм. Майкельсон) рисуются
            #    поверх и на границы оси НЕ влияют.
            lo_x, hi_x = self._main_bounds(data, "x_raw", "total_fit_x")
            lo_y, hi_y = self._main_bounds(data, "y_raw", "total_fit_y")

            # 2b. Производная — нормируем под размах главной оси, чтобы она
            #     была видна поверх профиля, не меняя её границы.
            self._draw_overlay_norm(
                data, "x_deriv", data["x"], self.series_x_deriv, lo_x, hi_x
            )
            self._draw_overlay_norm(
                data, "y_deriv", data["y"], self.series_y_deriv, lo_y, hi_y
            )

            # 3. Максимум высоты для линий уровня и фокус-индикаторов.
            #    Рекорды («best») накапливаем только в режиме фита.
            has_display = has_raw
            if has_fit_x:
                max_x = float(np.max(data["total_fit_x"]))
                self._best_x = max(self._best_x, max_x)
            elif has_raw:
                max_x = float(np.max(data["x_raw"]))
            else:
                max_x = 0.0
            if has_fit_y:
                max_y = float(np.max(data["total_fit_y"]))
                self._best_y = max(self._best_y, max_y)
            elif has_raw:
                max_y = float(np.max(data["y_raw"]))
            else:
                max_y = 0.0

            # 4. Линии уровня максимума (только если чекбокс включён).
            if self._is_draw_line and has_display:
                self.series_x_max_line.replace(
                    [QPointF(0, max_x), QPointF(x_max, max_x)]
                )
                self.series_y_max_line.replace(
                    [QPointF(0, max_y), QPointF(y_max, max_y)]
                )
                if has_fit_x:
                    self.series_x_max_line_best.replace(
                        [QPointF(0, self._best_x), QPointF(x_max, self._best_x)]
                    )
                else:
                    self.series_x_max_line_best.clear()
                if has_fit_y:
                    self.series_y_max_line_best.replace(
                        [QPointF(0, self._best_y), QPointF(y_max, self._best_y)]
                    )
                else:
                    self.series_y_max_line_best.clear()
            else:
                self.series_x_max_line.clear()
                self.series_x_max_line_best.clear()
                self.series_y_max_line.clear()
                self.series_y_max_line_best.clear()

            # Фокус-индикаторы: текущая высота пика (по фиту, если он есть).
            if has_display:
                self.intensity_calculated.emit(float(max_x), float(max_y))

            self.chart_x.axes(Qt.Orientation.Horizontal)[0].setRange(0, x_max)
            self.chart_x.axes(Qt.Orientation.Vertical)[0].setRange(lo_x, hi_x)

            self.chart_y.axes(Qt.Orientation.Horizontal)[0].setRange(0, y_max)
            self.chart_y.axes(Qt.Orientation.Vertical)[0].setRange(lo_y, hi_y)

        except Exception as e:
            print(f"Plotter Render Error: {e}")

    @staticmethod
    def _main_bounds(data, raw_key, fit_key):
        """Вертикальные границы главной оси: строго по профилю (+ фит).
        Никакие контрастные данные сюда не попадают."""
        parts = []
        if raw_key in data and len(data[raw_key]):
            parts.append(data[raw_key])
        if fit_key in data and len(data[fit_key]):
            parts.append(data[fit_key])
        if not parts:
            return 0.0, 1.0
        vmin = float(min(np.min(p) for p in parts))
        vmax = float(max(np.max(p) for p in parts))
        if vmax <= vmin:
            return vmin, vmin + 1.0
        pad = (vmax - vmin) * 0.08
        return vmin - pad, vmax + pad

    def _draw_overlay_norm(self, data, key, coords, series, lo, hi):
        """Рисует оверлейную серию (например, производную), нормализуя её
        значения к диапазону [lo, hi] главной оси — чтобы она была видна,
        не ломая границы оси. Если данных нет — очищает серию."""
        if key not in data:
            series.clear()
            return
        v = data[key]
        vmin = float(np.min(v))
        vmax = float(np.max(v))
        if vmax > vmin:
            scale = (hi - lo) / (vmax - vmin)
            pts = [
                QPointF(float(c), float(lo + (val - vmin) * scale))
                for c, val in zip(coords, v)
            ]
        else:
            mid = (lo + hi) / 2.0
            pts = [QPointF(float(c), mid) for c in coords]
        series.replace(pts)
