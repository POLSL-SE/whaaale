from dataclasses import dataclass
from typing import Literal, Optional

import numpy as np
from numpy.typing import NDArray
from PyQt6.QtCharts import QCategoryAxis, QChart, QChartView, QLineSeries
from PyQt6.QtCore import Qt, QMargins
from PyQt6.QtGui import QFont, QPainter
from PyQt6.QtWidgets import QGridLayout, QLabel, QSizePolicy, QWidget

from lib import ScalarType


@dataclass
class PixelValues:
    values: NDArray


@dataclass
class AreaValues:
    avg: NDArray[np.float64]
    min: NDArray[np.float64]
    max: NDArray[np.float64]
    quartile_low: NDArray[np.float64]
    quartile_high: NDArray[np.float64]


class SpectralViewer(QWidget):
    data: Optional[PixelValues | AreaValues] = None
    chart_view: Optional[QChartView] = None

    def __init__(
        self,
        parent: Optional["QWidget"] = None,
        flags: Qt.WindowType = Qt.WindowType.Widget,
    ) -> None:
        super().__init__(parent, flags)

        status_label = QLabel(
            "Open an image and select a pixel or an area to show the spectral curve.",
            self,
        )
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        status_label.setWordWrap(True)
        self.status_label = status_label

        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        status_label.setFont(font)

        grid_layout = QGridLayout()
        grid_layout.addWidget(status_label)
        self.setLayout(grid_layout)
        self.grid_layout = grid_layout

    def update_labels(self, labels: list[str]):
        self.labels = labels

    def from_pixel(self, pixel: NDArray):
        self.data = PixelValues(pixel)
        self.render_pixel()

    def from_area(self, area: NDArray[ScalarType]):
        h, w, b = area.shape
        a_lin = area.reshape((h * w, b))
        q: np.ndarray[tuple[Literal[5], int], np.dtype[np.float64]] = np.quantile(
            a_lin, [0, 0.25, 0.5, 0.75, 1], axis=0
        )
        v_min, q_low, avg, q_high, v_max = q
        values = AreaValues(
            avg=avg, min=v_min, max=v_max, quartile_low=q_low, quartile_high=q_high
        )
        self.data = values
        self.render_area()

    def clear(self):
        self.data = None

        if self.chart_view is not None:
            self.grid_layout.removeWidget(self.chart_view)
            self.chart_view = None

        self.status_label.setText(
            "Select a pixel or an area to show the spectral curve."
        )
        self.status_label.setVisible(True)
        self.grid_layout.addWidget(self.status_label)

    def render_pixel(self):
        if not isinstance(self.data, PixelValues):
            raise RuntimeError(
                "Pixel spectral curve render requested, but data is not a pixel value (either area or None)."
            )

        series = QLineSeries()
        series.setName("Value")

        for i, val in enumerate(self.data.values):
            series.append(float(i), float(val))

        chart = QChart()
        chart.addSeries(series)
        chart.createDefaultAxes()
        chart.setTitle("Spectral curve")

        margins = QMargins(2, 2, 2, -7)
        chart.setMargins(margins)

        legend = chart.legend()
        legend.setVisible(False)
        legend.setAlignment(Qt.AlignmentFlag.AlignBottom)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        try:
            self.grid_layout.removeWidget(self.status_label)
        except Exception as err:
            print(err)

        if self.chart_view is not None:
            self.grid_layout.removeWidget(self.chart_view)

        self.grid_layout.addWidget(chart_view)
        self.chart_view = chart_view

    def render_area(self):
        if not isinstance(self.data, AreaValues):
            raise RuntimeError(
                "Area spectral curve render requested, but data is not an `AreaValues` object, but a pixel or None."
            )

        series_min = QLineSeries()
        series_min.setName("min")
        series_qlow = QLineSeries()
        series_qlow.setName("25%")
        series_avg = QLineSeries()
        series_avg.setName("avg")
        series_qhigh = QLineSeries()
        series_qhigh.setName("75%")
        series_max = QLineSeries()
        series_max.setName("max")

        for i in range(len(self.labels)):
            x = float(i)
            series_min.append(x, self.data.min[i])
            series_qlow.append(x, self.data.quartile_low[i])
            series_avg.append(x, self.data.avg[i])
            series_qhigh.append(x, self.data.quartile_high[i])
            series_max.append(x, self.data.max[i])

        chart = QChart()
        chart.addSeries(series_min)
        chart.addSeries(series_qlow)
        chart.addSeries(series_avg)
        chart.addSeries(series_qhigh)
        chart.addSeries(series_max)
        chart.setTitle("Spectral curve")

        margins = QMargins(2, 2, 2, -7)
        chart.setMargins(margins)

        chart.createDefaultAxes()
        default_x_axis = chart.axes(Qt.Orientation.Horizontal)[0]
        chart.removeAxis(default_x_axis)
        axis = self.label_x_axis()
        chart.addAxis(axis, Qt.AlignmentFlag.AlignBottom)

        legend = chart.legend()
        legend.setVisible(True)
        legend.setAlignment(Qt.AlignmentFlag.AlignBottom)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        try:
            self.status_label.hide()
            self.grid_layout.removeWidget(self.status_label)
        except Exception as err:
            print(err)

        if self.chart_view is not None:
            self.grid_layout.removeWidget(self.chart_view)

        self.grid_layout.addWidget(chart_view)
        self.chart_view = chart_view

    def label_x_axis(self) -> QCategoryAxis:
        n_labels = len(self.labels)
        axis = QCategoryAxis()
        axis.setMin(0)
        axis.setMax(n_labels - 1)
        axis.setStartValue(0)
        axis.setLabelsPosition(
            QCategoryAxis.AxisLabelsPosition.AxisLabelsPositionOnValue
        )
        for i, label in enumerate(self.labels):
            axis.append(label, i)

        return axis
