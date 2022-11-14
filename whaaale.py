# This is a demo to test packaging
from sys import argv

import numpy as np
from PyQt6.QtCharts import QChart, QChartView, QLineSeries
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QApplication, QMainWindow

a = QApplication(argv)
series = QLineSeries()

series.append(0, 6)
series.append(2, 4)
l = np.array([[3, 8], [7, 4], [10, 5], [11, 1], [13, 3], [17, 6], [18, 3], [20, 2]])
for p in l:
    series.append(p[0], p[1])


chart = QChart()
chart.legend().hide()
chart.addSeries(series)
chart.createDefaultAxes()
chart.setTitle("Simple line chart example")

chartView = QChartView(chart)
chartView.setRenderHint(QPainter.RenderHint.Antialiasing)

window = QMainWindow()
window.setCentralWidget(chartView)
window.resize(400, 300)
window.show()

a.exec()
