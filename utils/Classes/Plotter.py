import numpy as np
from PySide6.QtCharts import QChart, QChartView, QLineSeries
from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import QVBoxLayout, QWidget

# TODO: cosmetic refactor


class Plotter(QWidget):
    intensity_calculated = Signal(float, float)

    def __init__(self):
        super().__init__()
        # Исправили флаги под ваши методы
        self._is_draw = False       # Отвечает за отрисовку графиков вообще
        self._is_draw_line = False  #   Отвечает за линии максимума


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

        self.chart_x = QChart()
        self.chart_x.addSeries(self.series_x_raw)
        self.chart_x.addSeries(self.series_x_fit)
        self.chart_x.addSeries(self.series_x_max_line) # Добавили на график
        self.chart_x.createDefaultAxes()
        self.chart_x.setTitle("Профиль по X")

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

        self.chart_y = QChart()
        self.chart_y.addSeries(self.series_y_raw)
        self.chart_y.addSeries(self.series_y_fit)
        self.chart_y.addSeries(self.series_y_max_line) # Добавили на график
        self.chart_y.createDefaultAxes()
        self.chart_y.setTitle("Профиль по Y")

        layout.addWidget(QChartView(self.chart_x))
        layout.addWidget(QChartView(self.chart_y))


    def update_line_vis(self,val):
        self._is_draw_line = val

    def update_is_draw(self,val):
        self._is_draw = val

    def update_data(self, data):
        if not data or "x_raw" not in data or "y_raw" not in data:
             return

        try:
            if not self._is_draw:
                # Если рисовать запрещено, очищаем всё и выходим
                self.series_x_raw.clear()
                self.series_x_fit.clear()
                self.series_x_max_line.clear()
                self.series_y_raw.clear()
                self.series_y_fit.clear()
                self.series_y_max_line.clear()
                return

            # 1. Рисуем сырые данные
            points_x = [QPointF(float(x), float(y)) for x, y in zip(data["x"], data["x_raw"])]
            self.series_x_raw.replace(points_x)

            points_y = [QPointF(float(x), float(y)) for x, y in zip(data["y"], data["y_raw"])]
            self.series_y_raw.replace(points_y)

            # 2. Рисуем фиттинг (Гаусс)
            has_fit_x = "total_fit_x" in data
            has_fit_y = "total_fit_y" in data

            if has_fit_x:
                fx_pts = [QPointF(float(xi), float(yi)) for xi, yi in enumerate(data["total_fit_x"])]
                self.series_x_fit.replace(fx_pts)

            if has_fit_y:
                fy_pts = [QPointF(float(xi), float(yi)) for xi, yi in enumerate(data["total_fit_y"])]
                self.series_y_fit.replace(fy_pts)

            # 3. Рисуем линии максимума (по фиту, если он есть, иначе по сырым данным)
            if self._is_draw_line:
                # Берем максимальный Икс на оси для ограничения линии по ширине
                axis_x_max_limit = float(data["x"][-1])
                axis_y_max_limit = float(data["y"][-1])

                # Ищем пик по X (высоту Гаусса X)
                y_data_x = data["total_fit_x"] if has_fit_x else data["x_raw"]
                max_y_val_x = np.max(y_data_x)  # Максимальная интенсивность по X

                # Горизонтальная линия от 0 до конца графика на уровне max_y_val_x
                self.series_x_max_line.replace([
                    QPointF(0, max_y_val_x),
                    QPointF(axis_x_max_limit, max_y_val_x)
                ])

                # Ищем пик по Y (высоту Гаусса Y)
                y_data_y = data["total_fit_y"] if has_fit_y else data["y_raw"]
                max_y_val_y = np.max(y_data_y)  # Максимальная интенсивность по Y

                # Горизонтальная линия от 0 до конца графика на уровне max_y_val_y
                self.series_y_max_line.replace([
                    QPointF(0, max_y_val_y),
                    QPointF(axis_y_max_limit, max_y_val_y)
                ])

                # Отправляем чистые интенсивности напрямую в сигнал
                self.intensity_calculated.emit(float(max_y_val_x), float(max_y_val_y))

            else:
                # Если чекбокс выключен, скрываем линии
                self.series_x_max_line.clear()
                self.series_y_max_line.clear()

            # 4. Обновляем границы осей под новые данные
            max_val_x = float(np.max(data["x_raw"]))
            self.chart_x.axes(Qt.Orientation.Horizontal)[0].setRange(0, float(data["x"][-1]))
            self.chart_x.axes(Qt.Orientation.Vertical)[0].setRange(0, max_val_x * 1.1 + 1)

            max_val_y = float(np.max(data["y_raw"]))
            self.chart_y.axes(Qt.Orientation.Horizontal)[0].setRange(0, float(data["y"][-1]))
            self.chart_y.axes(Qt.Orientation.Vertical)[0].setRange(0, max_val_y * 1.1 + 1)

        except Exception as e:
            print(f"Plotter Render Error: {e}")
