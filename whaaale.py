# This is a demo to test packaging
from sys import argv

import numpy as np
from PyQt6 import QtGui
from PyQt6.QtCharts import QChart, QChartView, QLineSeries
from PyQt6.QtGui import QPainter, QAction, QColor
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QMenuBar, QMenu, QFrame, QGridLayout, QVBoxLayout, QHBoxLayout, QWidget, QSlider, QLabel, QComboBox
from PyQt6.QtCore import Qt 


class MainWindow(QMainWindow):
    def start(self):
        self.resize(640, 360)
        self.setup_ui()
        self.setWindowTitle("Whaaale")
        self.show()

    def setup_ui(self):
        layout =  QGridLayout()
        toolbar1 = QHBoxLayout()
        toolbar2 = QVBoxLayout()
        toolbar3 = QGridLayout()
        toolbar4 = QGridLayout()
        viewer = QHBoxLayout()
        spectrum_graph = QHBoxLayout()
        layout.addLayout(toolbar1, 0, 0, 2, 2) # row, column, rowSpan, columnSpan
        layout.addLayout(toolbar2, 2, 0, 2, 2)
        layout.addLayout(toolbar3, 4, 0, 2, 2)
        layout.addLayout(toolbar4, 6, 0, 2, 2)
        layout.addLayout(viewer, 0, 2, 4, 6)
        layout.addLayout(spectrum_graph, 4, 2, 4, 6)

        # ****** Elements of layout ******

        # ****** Buttons ******

        self.single_band_button = QPushButton(self)
        self.single_band_button.setText('Single')
        self.single_band_button.clicked.connect(self.single_band)

        self.fake_col_button = QPushButton(self)
        self.fake_col_button.setText('Fake color')
        self.fake_col_button.clicked.connect(self.fake_col)

        # ****** Magic Wand ******

        self.label_wand = QLabel("Magic wand", self)
        self.label_wand.setFixedSize(90, 20)

        select_magic_wand = QComboBox()
        select_magic_wand.addItem("Option 1")
        select_magic_wand.addItem("Option 2")
        select_magic_wand.addItem("Option 3")

        slider_magic_wand = QSlider(Qt.Orientation.Horizontal, self)
        slider_magic_wand.setGeometry(50,50, 200, 50)
        slider_magic_wand.setMinimum(0)
        slider_magic_wand.setMaximum(20)
        slider_magic_wand.setTickPosition(QSlider.TickPosition.TicksBelow)
        slider_magic_wand.setTickInterval(2)

        # ****** Spectral curve ******

        self.label_spectral = QLabel("Spectral curve", self)
        self.label_spectral.setFixedSize(60, 20)

        self.select_point = QPushButton(self)
        self.select_point.setText('Select point')
        self.select_point.clicked.connect(self.single_band)

        self.select_area = QPushButton(self)
        self.select_area.setText('Select area')
        self.select_area.clicked.connect(self.fake_col)

        self.export_png = QPushButton(self)
        self.export_png.setText('PNG')
        self.export_png.clicked.connect(self.single_band)
        self.export_png.setFixedSize(35, 35)

        self.export_csv = QPushButton(self)
        self.export_csv.setText('CSV')
        self.export_csv.clicked.connect(self.fake_col)
        self.export_csv.setFixedSize(35, 35)

        # ****** Menu ******

        self.label_band1 = QLabel("Band #1", self)
        self.label_band1.setFixedSize(40, 20)
        frame1 = QFrame(self)
        frame1.setFrameShape(QFrame.Shape.StyledPanel)
        frame1.setLineWidth(3)
        frame1.setFixedSize(30, 30)
        frame1.setStyleSheet("background-color:red")

        self.label_band2 = QLabel("Band #2", self)
        self.label_band2.setFixedSize(40, 20)
        frame2 = QFrame(self)
        frame2.setFrameShape(QFrame.Shape.StyledPanel)
        frame2.setLineWidth(3)
        frame2.setFixedSize(30, 30)
        frame2.setStyleSheet("background-color:green")

        self.label_band3 = QLabel("Band #3", self)
        self.label_band3.setFixedSize(40, 20)
        frame3 = QFrame(self)
        frame3.setFrameShape(QFrame.Shape.StyledPanel)
        frame3.setLineWidth(3)
        frame3.setFixedSize(30, 30)
        frame3.setStyleSheet("background-color:blue")


        # ****** Add elements to layout ******

        # toolbar1.addWidget(frame)
        toolbar1.addWidget(self.single_band_button)
        toolbar1.addWidget(self.fake_col_button)

        toolbar2.addWidget(self.label_wand)
        toolbar2.addWidget(select_magic_wand)
        toolbar2.addWidget(slider_magic_wand)

        toolbar3.addWidget(self.label_spectral, 0, 0)
        toolbar3.addWidget(self.select_point, 1, 0)
        toolbar3.addWidget(self.select_area, 2, 0)
        toolbar3.addWidget(self.export_png, 3, 0)
        toolbar3.addWidget(self.export_csv, 3, 1)

        toolbar4.addWidget(self.label_band1, 0, 0)
        toolbar4.addWidget(frame1, 0, 1)
        toolbar4.addWidget(self.label_band2, 1, 0)
        toolbar4.addWidget(frame2, 1, 1)
        toolbar4.addWidget(self.label_band3, 2, 0)
        toolbar4.addWidget(frame3, 2, 1)

        spectrum_graph.addWidget(self.setup_chart())
        viewer.addWidget(self.setup_chart())

        # ****** Widget placing ******
        widget = QWidget()
        widget.resize(100, 100)
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        
        # ****** Menu bar ******
        self._createMenuBar()

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
        
    def single_band(self):
        # Function for handling clicking on single_band_button
        print('clicked single band')

    def fake_col(self):
        # Function for handling clicking on fake_col_button
        print('clicked fake color')

    def _createMenuBar(self):
        menuBar = QMenuBar(self)
        self.setMenuBar(menuBar)
        fileMenu = menuBar.addMenu("&File")
        editMenu = menuBar.addMenu("&View")
        helpMenu = menuBar.addMenu("&Help")

        # File menu
        action_new = QAction("New", self)
        action_new.triggered.connect(self.fake_col)
        action_open = QAction("Open", self)
        action_open.triggered.connect(self.fake_col)
        action_exit = QAction("Exit", self)
        action_exit.triggered.connect(self.fake_col)
        fileMenu.addAction(action_new)
        fileMenu.addAction(action_open)
        fileMenu.addAction(action_exit)

        # Edit menu
        action_view1 = QAction("Option 1", self)
        action_view1.triggered.connect(self.fake_col)
        action_view2 = QAction("Option 2", self)
        action_view2.triggered.connect(self.fake_col)
        editMenu.addAction(action_view1)
        editMenu.addAction(action_view2)

        # Help menu
        action_help = QAction("Help", self)
        action_help.triggered.connect(self.fake_col)
        helpMenu.addAction(action_help)


def main():
    a = QApplication(argv)
    main_window = MainWindow()
    main_window.start()
    a.exec()


if __name__ == "__main__":
    main()
