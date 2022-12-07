import csv
from dataclasses import dataclass
from math import ceil
from pathlib import Path
from typing import Literal, Optional

import matplotlib.backend_tools
import matplotlib.colors
import matplotlib.style
import numpy as np
from matplotlib.axes import Axes
from matplotlib.backend_managers import ToolManager
from matplotlib.backend_tools import ToolBase
from matplotlib.backends.backend_qt import ToolbarQt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from numpy.typing import NDArray
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QFileDialog, QGridLayout, QLabel, QSizePolicy, QWidget

from lib import LabelType, ScalarType


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
    canvas: Optional[FigureCanvas] = None

    def __init__(
        self,
        parent: Optional["QWidget"] = None,
        flags: Qt.WindowType = Qt.WindowType.Widget,
    ) -> None:
        super().__init__(parent, flags)

        # Force Qt backend, new toolbar and set style
        matplotlib.use("qtagg")
        matplotlib.rcParams["toolbar"] = "toolmanager"
        matplotlib.style.use("style/dark_plot.mplstyle")

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

    def update_labels(self, labels: list[str], labels_type: LabelType):
        self.labels = labels
        self.labels_type = labels_type

    def from_pixel(self, pixel: NDArray):
        self.data = PixelValues(pixel)
        self.render()

    def from_area(self, area: NDArray[ScalarType]):
        h, w, b = area.shape
        a_lin = area.reshape((h * w, b))
        avg = np.mean(a_lin, axis=0)
        q: np.ndarray[tuple[Literal[4], int], np.dtype[np.float64]] = np.quantile(
            a_lin, [0, 0.25, 0.75, 1], axis=0
        )
        v_min, q_low, q_high, v_max = q
        values = AreaValues(
            avg=avg, min=v_min, max=v_max, quartile_low=q_low, quartile_high=q_high
        )
        self.data = values
        self.render()

    def clear(self):
        self.data = None

        if self.canvas is not None:
            self.grid_layout.removeWidget(self.canvas)
            self.grid_layout.removeWidget(self.toolbar)
            self.canvas.deleteLater()
            self.toolbar.deleteLater()
            self.canvas = None
            self.toolbar = None

        self.status_label.setText(
            "Select a pixel or an area to show the spectral curve."
        )
        self.status_label.setVisible(True)
        self.grid_layout.addWidget(self.status_label)

    def render(self):
        if self.data is None:
            raise RuntimeError("Spectral curve render requested, but data is None")
        if self.labels is None:
            raise RuntimeError("Labels have not been provided")

        bands = len(self.labels)
        fig = Figure(tight_layout=True)
        canvas = FigureCanvas(fig)
        # set focus to enable keyboard shortcuts
        canvas.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        ax: Axes = fig.subplots()

        match self.labels_type:
            case LabelType.CUSTOM_STR:
                ax.set_xticks(
                    np.arange(bands),
                    labels=self.labels,
                    rotation=90,
                    fontsize="x-small",
                )
                size = fig.get_size_inches() * fig.dpi
                w = size[0]
                step = ceil(bands / w * 12)
                for i, label in enumerate(ax.xaxis.get_ticklabels()):
                    if (i % step) != 0:
                        label.set_visible(False)

                x_values = np.arange(bands)
                ax.set_xlabel("Band")

            case LabelType.WAVELENGTH:
                x_values = np.array(self.labels, dtype=np.float64)
                self.show_spectrum_bg(ax, self.data, x_values)
                ax.set_xlabel("Wavelength [nm]")

            case LabelType.AUTO:
                x_values = np.arange(bands)
                ax.set_xlabel("Band")

        match self.data:
            case AreaValues(avg, min, max, quartile_low, quartile_high):
                ax.plot(x_values, avg, label="avg")
                ax.plot(x_values, min, label="min")
                ax.plot(x_values, max, label="max")
                ax.plot(x_values, quartile_low, label="25%")
                ax.plot(x_values, quartile_high, label="75%")

            case PixelValues(values):
                ax.plot(x_values, values, label="Value")

            case None:
                raise RuntimeError("No value")

        ax.margins(0, 0)
        ax.legend()

        self.status_label.setVisible(False)
        self.grid_layout.removeWidget(self.status_label)
        toolmanager = ToolManager(fig)
        self.toolmanager = toolmanager
        toolbar = ToolbarQt(toolmanager, self)
        matplotlib.backend_tools.add_tools_to_manager(self.toolmanager)
        matplotlib.backend_tools.add_tools_to_container(toolbar)
        toolmanager.remove_tool("fullscreen")
        toolmanager.remove_tool("quit")
        toolmanager.remove_tool("quit_all")
        toolmanager.add_tool(
            "CSV",
            ExportData,
            parent=self,
            plot_values=self.data,
            labels_type=self.labels_type,
            bands=self.labels if self.labels_type == LabelType.CUSTOM_STR else x_values,
        )
        toolbar.add_tool("CSV", "io", 1)
        if self.canvas:
            self.grid_layout.replaceWidget(self.canvas, canvas)
            self.grid_layout.replaceWidget(self.toolbar, toolbar)
        else:
            self.grid_layout.addWidget(canvas)
            self.grid_layout.addWidget(toolbar)
        self.canvas = canvas
        self.toolbar = toolbar

    def show_spectrum_bg(
        self, ax: Axes, values: AreaValues | PixelValues, x_values: NDArray[np.float64]
    ):
        # Visible spectrum limits for the image
        clim = (350, 780)
        # Prepare normalizer scaling [350, 780] to [0, 1]
        norm = matplotlib.colors.Normalize(*clim)
        # List of wavelengths from the visible light spectrum every 2 nm
        wl = np.arange(clim[0], clim[1] + 1, 2)
        # Prepare a `(wavelength, RGBA colour)` list
        colorlist = list(zip(norm(wl), [wavelength_to_rgb(w) for w in wl]))
        # Prepare a colormap for `imshow`
        spectralmap = matplotlib.colors.LinearSegmentedColormap.from_list(
            "spectrum", colorlist
        )

        if isinstance(values, AreaValues):
            v_min = np.min(values.min)
            v_max = np.max(values.max)
        else:
            v_min = np.min(values.values)
            v_max = np.max(values.values)

        x_min = np.min(x_values)
        x_max = np.max(x_values)
        x_stripes = np.linspace(x_min, x_max, 1000)

        y = np.linspace(v_min, v_max, 100)
        X, Y = np.meshgrid(x_stripes, y)

        extent = (x_min, x_max, v_min, v_max)

        ax.imshow(
            X, clim=clim, extent=extent, cmap=spectralmap, aspect="auto", alpha=0.5
        )


# From https://stackoverflow.com/a/44960748
def wavelength_to_rgb(wavelength: float, gamma: float = 0.8):
    """taken from http://www.noah.org/wiki/Wavelength_to_RGB_in_Python
    This converts a given wavelength of light to an
    approximate RGB color value. The wavelength must be given
    in nanometers in the range from 380 nm through 750 nm
    (789 THz through 400 THz).

    Based on code by Dan Bruton
    http://www.physics.sfasu.edu/astro/color/spectra.html
    Additionally alpha value set to 0.5 outside range
    """
    if wavelength >= 380 and wavelength <= 750:
        A = 1.0
    else:
        A = 0.2
    if wavelength < 380:
        wavelength = 380.0
    if wavelength > 750:
        wavelength = 750.0
    if wavelength >= 380 and wavelength <= 440:
        attenuation = 0.3 + 0.7 * (wavelength - 380) / (440 - 380)
        R: float = ((-(wavelength - 440) / (440 - 380)) * attenuation) ** gamma
        G: float = 0.0
        B: float = (1.0 * attenuation) ** gamma
    elif wavelength >= 440 and wavelength <= 490:
        R = 0.0
        G = ((wavelength - 440) / (490 - 440)) ** gamma
        B = 1.0
    elif wavelength >= 490 and wavelength <= 510:
        R = 0.0
        G = 1.0
        B = (-(wavelength - 510) / (510 - 490)) ** gamma
    elif wavelength >= 510 and wavelength <= 580:
        R = ((wavelength - 510) / (580 - 510)) ** gamma
        G = 1.0
        B = 0.0
    elif wavelength >= 580 and wavelength <= 645:
        R = 1.0
        G = (-(wavelength - 645) / (645 - 580)) ** gamma
        B = 0.0
    elif wavelength >= 645 and wavelength <= 750:
        attenuation = 0.3 + 0.7 * (750 - wavelength) / (750 - 645)
        R = (1.0 * attenuation) ** gamma
        G = 0.0
        B = 0.0
    else:
        R = 0.0
        G = 0.0
        B = 0.0
    return (R, G, B, A)


class ExportData(ToolBase):
    """Export data as CSV button"""

    default_keymap = ["C"]
    description = "Export plot as CSV"
    image = (
        Path(__file__).parent.joinpath("../style/icons/export_csv").resolve().as_posix()
    )

    def __init__(
        self,
        *args,
        parent: QWidget,
        plot_values: PixelValues | AreaValues,
        labels_type: LabelType,
        bands: list[str] | NDArray[np.int_] | NDArray[np.float64],
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.parent = parent
        self.plot_values = plot_values
        self.labels_type = labels_type
        self.bands = bands

    def trigger(self, *args, **kwargs) -> None:
        out_path, _filter = QFileDialog.getSaveFileName(
            self.parent, "Choose a filename to export to", "", "CSV files (*.csv *.txt)"
        )
        if not out_path:
            return

        if self.labels_type == LabelType.WAVELENGTH:
            band_header = "Wavelength"
        else:
            band_header = "Band"

        with open(out_path, "w", encoding="utf-8") as out_file:
            writer = csv.writer(out_file, dialect="excel", lineterminator="\n")
            match self.plot_values:
                case PixelValues(values):
                    writer.writerow([band_header, "Value"])
                    for row in zip(self.bands, values):
                        writer.writerow(row)

                case AreaValues(avg, min, max, quartile_low, quartile_high):
                    writer.writerow(
                        [band_header, "Minimum", "25%", "Average", "75%", "Maximum"]
                    )
                    for row in zip(
                        self.bands, min, quartile_low, avg, quartile_high, max
                    ):
                        writer.writerow(row)
