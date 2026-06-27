import numpy as np
from PySide6.QtCharts import QChart, QChartView, QLineSeries
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import QVBoxLayout, QWidget


class Plotter(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.fit_series_x = []
        self.fit_series_y = []
        # График X
        self.series_x_raw = QLineSeries()
        self.series_x_raw.setName("Сырые данные X")

        self.series_x_fit = QLineSeries()
        self.series_x_fit.setName("Гаусс X")
        self.series_x_fit.setPen(QPen(QColor(Qt.GlobalColor.red), 2))

        self.chart_x = QChart()
        self.chart_x.addSeries(self.series_x_raw)
        self.chart_x.addSeries(self.series_x_fit)
        self.chart_x.createDefaultAxes()
        self.chart_x.setTitle("Профиль по X")

        # График Y
        self.series_y_raw = QLineSeries()
        self.series_y_raw.setName("Сырые данные Y")

        self.series_y_fit = QLineSeries()
        self.series_y_fit.setName("Гаусс Y")
        # Зеленый цвет для Y
        self.series_y_fit.setPen(QPen(QColor(Qt.GlobalColor.green), 2))

        self.chart_y = QChart()
        self.chart_y.addSeries(self.series_y_raw)
        self.chart_y.addSeries(self.series_y_fit)
        self.chart_y.createDefaultAxes()
        self.chart_y.setTitle("Профиль по Y")

        layout.addWidget(QChartView(self.chart_x))
        layout.addWidget(QChartView(self.chart_y))

    def update_data(self, data):
        if not data or "x_raw" not in data or "y_raw" not in data:
            return

        try:
            # 1. Рисуем синие линии (Сырые данные)
            points_x = [
                QPointF(float(x), float(y)) for x, y in zip(data["x"], data["x_raw"])
            ]
            self.series_x_raw.replace(points_x)

            points_y = [
                QPointF(float(x), float(y)) for x, y in zip(data["y"], data["y_raw"])
            ]
            self.series_y_raw.replace(points_y)

            # 2. Рисуем красную/зеленую линии (Фиттинг)
            if "total_fit_x" in data:
                fx_pts = [
                    QPointF(float(xi), float(yi))
                    for xi, yi in enumerate(data["total_fit_x"])
                ]
                self.series_x_fit.replace(fx_pts)

            if "total_fit_y" in data:
                fy_pts = [
                    QPointF(float(xi), float(yi))
                    for xi, yi in enumerate(data["total_fit_y"])
                ]
                self.series_y_fit.replace(fy_pts)

            # 3. Обновляем границы осей
            self.chart_x.axes(Qt.Horizontal)[0].setRange(0, float(data["x"][-1]))
            self.chart_x.axes(Qt.Vertical)[0].setRange(
                0, float(np.max(data["x_raw"]) * 1.1 + 1)
            )

            self.chart_y.axes(Qt.Horizontal)[0].setRange(0, float(data["y"][-1]))
            self.chart_y.axes(Qt.Vertical)[0].setRange(
                0, float(np.max(data["y_raw"]) * 1.1 + 1)
            )

        except Exception as e:
            # Теперь мы увидим реальную ошибку, если она случится внутри отрисовки
            print(f"Plotter Render Error: {e}")
