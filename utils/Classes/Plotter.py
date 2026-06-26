from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import QVBoxLayout, QWidget


class Plotter(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # График X
        self.series_x_raw = QLineSeries()
        self.series_x_raw.setName("Сырые данные X")

        self.series_x_fit = QLineSeries()
        self.series_x_fit.setName("Гаусс X")
        # Устанавливаем красный цвет через QPen, чтобы можно было задать толщину (2)
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
        """Принимает словарь результатов из функции process"""

        # Обновляем серию X
        points_x_raw = [QPointF(x, y) for x, y in zip(data["x"], data["x_w"])]
        points_x_fit = [QPointF(x, y) for x, y in zip(data["x"], data["X_gauss"])]
        self.series_x_raw.replace(points_x_raw)
        self.series_x_fit.replace(points_x_fit)

        # Обновляем серию Y
        points_y_raw = [QPointF(x, y) for x, y in zip(data["y"], data["y_w"])]
        points_y_fit = [QPointF(x, y) for x, y in zip(data["y"], data["Y_gauss"])]
        self.series_y_raw.replace(points_y_raw)
        self.series_y_fit.replace(points_y_fit)

        # Пересчитываем оси (чтобы график не улетал)
        self.chart_x.axes(Qt.Orientation.Horizontal)[0].setRange(0, data["x"][-1])
        self.chart_x.axes(Qt.Orientation.Vertical)[0].setRange(
            0, max(data["x_w"]) * 1.1
        )

        self.chart_y.axes(Qt.Orientation.Horizontal)[0].setRange(0, data["y"][-1])
        self.chart_y.axes(Qt.Orientation.Vertical)[0].setRange(
            0, max(data["y_w"]) * 1.1
        )
