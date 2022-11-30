# This is a demo to test packaging
from sys import argv

import numpy as np
from PyQt6 import QtGui
from PyQt6.QtCharts import QChart, QChartView, QLineSeries
from PyQt6.QtGui import QPainter, QAction, QColor
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QMenuBar, QMenu, QFrame, QGridLayout, QVBoxLayout, QHBoxLayout, QWidget


#   ***************************************************************************
#   * This is the first version with fixed button sizes.                      *
#   * Whaaale will be using layouts to adjust sizes to the window size.       *
#   ***************************************************************************

class MainWindow(QMainWindow):
    def start(self):
        # Setup variables
        self.height = 0
        self.width = 0
        self.size1 = 20

        # Setup funcs
        # self.setup_chart()
        self.resize(640, 360)
        self.setup_ui()
        self.setWindowTitle("Whaaale")
        self.show()

    def setup_chart(self):
        series = QLineSeries()

        series.append(0, 6)
        series.append(2, 4)
        l = np.array(
            [[3, 8], [7, 4], [10, 5], [11, 1], [13, 3], [17, 6], [18, 3], [20, 2]]
        )
        for p in l:
            series.append(p[0], p[1])

        chart = QChart()
        chart.legend().hide()
        chart.addSeries(series)
        chart.createDefaultAxes()
        chart.setTitle("Simple line chart example")

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        return chart_view
        # self.chart_view = chart_view
        # self.setCentralWidget(self.chart_view)

    # Overridden function so we can adjust gui to the size of the window
    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        self.width = self.geometry().width()
        self.height = self.geometry().height()
        # self.size1 = int(0.15 * self.width)
        print("Height: ", self.height)
        print("Width: ", self.width) 
        return super().resizeEvent(a0)

    def setup_ui(self):
        layout =  QGridLayout()
        toolbar1 = QVBoxLayout()
        toolbar2 = QVBoxLayout()
        viewer = QHBoxLayout()
        spectrum_graph = QHBoxLayout()
        layout.addLayout(toolbar1, 0, 0) # row, column, rowSpan, columnSpan
        layout.addLayout(toolbar2, 1, 0)
        layout.addLayout(viewer, 0, 1)
        layout.addLayout(spectrum_graph, 1, 1)

        # Elements of layout

        # Buttons
        # Create a QVBoxLayout instance

        self.single_band_button = QPushButton(self)
        self.single_band_button.setText('Single')
        # self.single_band_button.setSize
        self.single_band_button.move(5, 30)
        # self.single_band_button.setGeometry(100, 100, self.size1, self.size1)
        self.single_band_button.clicked.connect(self.single_band)

        self.fake_col_button = QPushButton(self)
        self.fake_col_button.setText('Fake color')
        self.fake_col_button.move(110, 30)
        self.fake_col_button.clicked.connect(self.fake_col)

        frame = QFrame(self)
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setLineWidth(3)
        frame.resize(100, 100)
        frame.move(self.size1, 200)

        # add elements to layout

        toolbar1.addWidget(self.single_band_button)
        toolbar1.addWidget(self.fake_col_button)
        viewer.addWidget(self.setup_chart())

        widget = QWidget()
        widget.resize(100, 100)
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        
        # # Menu bar
        self._createMenuBar()

        
        
    def single_band(self):
        # Function for handling clicking on single_band_button
        print('clicked single band')

    def fake_col(self):
        # Function for handling clicking on fake_col_button
        print('clicked fake color')

    def _createMenuBar(self):
        menuBar = QMenuBar(self)
        self.setMenuBar(menuBar)
        # fileMenu = QMenu("&File", self)
        # menuBar.addMenu(fileMenu)
        fileMenu = menuBar.addMenu("&File")
        editMenu = menuBar.addMenu("&View")
        helpMenu = menuBar.addMenu("&Help")
        action_new = QAction("New", self)
        action_new.triggered.connect(self.fake_col)
        action_open = QAction("Open", self)
        action_open.triggered.connect(self.fake_col)
        action_exit = QAction("Exit", self)
        action_exit.triggered.connect(self.fake_col)
        fileMenu.addAction(action_new)
        fileMenu.addAction(action_open)
        fileMenu.addAction(action_exit)


def main():
    a = QApplication(argv)
    main_window = MainWindow()
    main_window.start()
    a.exec()


if __name__ == "__main__":
    main()
