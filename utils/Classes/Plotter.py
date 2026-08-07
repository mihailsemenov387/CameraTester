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
        self.series_y_raw.clear()
        self.series_y_fit.clear()
        self.series_y_max_line.clear()
        self.series_y_max_line_best.clear()
        self.series_y_contrast.clear()
        self._best_x = self._best_y = 0

    def reset_best(self):
        self._best_x = self._best_y = 0

    def update_data(self, data: dict = {}):
        if not data:
            return

        try:
            # Нормированный контраст (Майкельсон) — точки со своей осью 0..1.
            # Рисуем независимо от профиля/контраста.
            if "x_contrast_pts" in data and "y_contrast_pts" in data:
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
                self.series_x_contrast.clear()
                self.series_y_contrast.clear()
                self.axis_x_contrast.setVisible(False)
                self.axis_y_contrast.setVisible(False)

            if "x_raw" not in data or "y_raw" not in data:
                return

            # 1. Рисуем сырые данные
            points_x = [
                QPointF(float(x), float(y)) for x, y in zip(data["x"], data["x_raw"])
            ]
            self.series_x_raw.replace(points_x)

            points_y = [
                QPointF(float(x), float(y)) for x, y in zip(data["y"], data["y_raw"])
            ]
            self.series_y_raw.replace(points_y)

            # 2. Рисуем фиттинг (Гаусс). В режиме контраста фит не рисуем:
            #    его амплитуда (200-250) задирает ось, и производная (~10)
            #    визуально уходит в ноль.
            has_fit_x = "total_fit_x" in data
            has_fit_y = "total_fit_y" in data

            if self._is_contrast:
                self.series_x_fit.clear()
                self.series_y_fit.clear()
            else:
                if has_fit_x:
                    fx_pts = [
                        QPointF(float(xi), float(yi))
                        for xi, yi in enumerate(data["total_fit_x"])
                    ]
                    self.series_x_fit.replace(fx_pts)

                if has_fit_y:
                    fy_pts = [
                        QPointF(float(xi), float(yi))
                        for xi, yi in enumerate(data["total_fit_y"])
                    ]
                    self.series_y_fit.replace(fy_pts)

            # 3. Считаем максимумы интенсивности и шлём в фокус-индикаторы
            if self._is_contrast:
                # Рекорды интенсивности в режиме контраста не накапливаем
                max_y_val_x = float(np.max(data["x_raw"]))
                max_y_val_y = float(np.max(data["y_raw"]))
            else:
                y_data_x = data["total_fit_x"] if has_fit_x else data["x_raw"]
                y_data_y = data["total_fit_y"] if has_fit_y else data["y_raw"]
                max_y_val_x = np.max(y_data_x)
                max_y_val_y = np.max(y_data_y)
                self._best_x = max(self._best_x, max_y_val_x)
                self._best_y = max(self._best_y, max_y_val_y)
                self.intensity_calculated.emit(float(max_y_val_x), float(max_y_val_y))

            # 4. Линии уровня максимума (только если чекбокс включён)
            if self._is_draw_line:
                axis_x_max_limit = float(data["x"][-1])
                axis_y_max_limit = float(data["y"][-1])

                self.series_x_max_line.replace(
                    [QPointF(0, max_y_val_x), QPointF(axis_x_max_limit, max_y_val_x)]
                )
                self.series_y_max_line.replace(
                    [QPointF(0, max_y_val_y), QPointF(axis_y_max_limit, max_y_val_y)]
                )

                if self._is_contrast:
                    # «Рекордный» максимум в режиме контраста не показываем
                    self.series_x_max_line_best.clear()
                    self.series_y_max_line_best.clear()
                else:
                    self.series_x_max_line_best.replace(
                        [QPointF(0, self._best_x), QPointF(axis_x_max_limit, self._best_x)]
                    )
                    self.series_y_max_line_best.replace(
                        [QPointF(0, self._best_y), QPointF(axis_y_max_limit, self._best_y)]
                    )
            else:
                # Если чекбокс выключен, скрываем линии
                self.series_x_max_line.clear()
                self.series_x_max_line_best.clear()
                self.series_y_max_line.clear()
                self.series_y_max_line_best.clear()

            # 5. Обновляем границы осей под новые данные
            if self._is_contrast:
                # Динамические лимиты строго по текущему максимуму контраста
                lo_x = float(np.min(data["x_raw"])) * 1.1 - 1
                hi_x = float(np.max(data["x_raw"])) * 1.1 + 1
                lo_y = float(np.min(data["y_raw"])) * 1.1 - 1
                hi_y = float(np.max(data["y_raw"])) * 1.1 + 1
            else:
                max_val_x = float(np.max(data["x_raw"]))
                max_val = max(self._best_x, max_val_x)
                lo_x, hi_x = 0, max_val * 1.1 + 1

                max_val_y = float(np.max(data["y_raw"]))
                max_val = max(self._best_y, max_val_y)
                lo_y, hi_y = 0, max_val * 1.1 + 1

            self.chart_x.axes(Qt.Orientation.Horizontal)[0].setRange(
                0, float(data["x"][-1])
            )
            self.chart_x.axes(Qt.Orientation.Vertical)[0].setRange(lo_x, hi_x)

            self.chart_y.axes(Qt.Orientation.Horizontal)[0].setRange(
                0, float(data["y"][-1])
            )
            self.chart_y.axes(Qt.Orientation.Vertical)[0].setRange(lo_y, hi_y)

        except Exception as e:
            print(f"Plotter Render Error: {e}")
