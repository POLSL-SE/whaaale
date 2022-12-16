# This is a demo to test packaging
import math
import os
from enum import Enum
from sys import argv, exit
from typing import Optional

import numpy as np
import numpy.typing as npt
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenuBar,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from lib import Coordinates, HsImage
from loaders.loader import Loader
from ui.image_preview import ImagePreview
from ui.spectral_viewer import SpectralViewer


class ApplicationState(Enum):
    NO_IMAGE = 0
    IMAGE_LOADED = 1
    SELECT_PX = 2
    SELECT_AREA_FIRST = 3
    SELECT_AREA_SECOND = 4
    SELECT_SIMILAR = 5


class ImageMode(Enum):
    MONO = 0
    RGB = 1
    SIMILAR = 2


class MainWindow(QMainWindow):
    state = ApplicationState.NO_IMAGE
    image_mode = ImageMode.MONO
    band_mono = 0
    band_r = 0
    band_g = 0
    band_b = 0
    image: Optional[HsImage] = None
    threshold = 1.0
    ignore_threshold_change = False
    similar_mask: Optional[npt.NDArray[np.bool8]] = None

    def start(self):
        self.resize(1280, 720)
        self.setup_ui()
        self.setup_logic()
        self.setWindowTitle("Whaaale")
        self.show()

    def setup_logic(self):
        self.loader = Loader(self)
        self.image_preview.register_handlers(self.on_mouse_down, self.on_mouse_up)

    def setup_ui(self):
        # ****** Widget placing ******
        central_widget = QWidget(self)
        central_widget.resize(100, 100)
        self.setCentralWidget(central_widget)

        layout = QGridLayout(central_widget)
        central_widget.setLayout(layout)
        # Toolbar with image mode and bands selection
        toolbar_image_settings = QVBoxLayout()
        toolbar_mode = QHBoxLayout()
        toolbar_image_settings.addLayout(toolbar_mode)
        # Toolbar with tools (magic wand, select pixel/area) section
        toolbar_tools = QVBoxLayout()
        viewer = QHBoxLayout()
        spectrum_graph = QHBoxLayout()
        layout.addLayout(
            toolbar_image_settings, 0, 0, 2, 2
        )  # row, column, rowSpan, columnSpan
        layout.addLayout(toolbar_tools, 2, 0, 2, 2)
        layout.addLayout(viewer, 0, 2, 4, 6)
        layout.addLayout(spectrum_graph, 4, 2, 4, 6)

        # ****** Elements of layout ******

        # ****** Buttons ******

        self.single_band_button = QPushButton(self)
        self.single_band_button.setText("Single")
        self.single_band_button.clicked.connect(self.single_band_click)

        self.fake_col_button = QPushButton(self)
        self.fake_col_button.setText("Fake color")
        self.fake_col_button.clicked.connect(self.fake_col_click)

        self.single_band_settings = QWidget(central_widget)
        sb_settings_layout = QFormLayout(self.single_band_settings)
        sb_settings_layout.setContentsMargins(0, 0, 0, 0)
        self.sb_combo = QComboBox(self.single_band_settings)
        self.sb_combo.currentIndexChanged.connect(self.mono_band_changed)
        sb_settings_layout.addRow("Mono band", self.sb_combo)
        self.single_band_settings.setLayout(sb_settings_layout)

        self.rgb_band_settings = QWidget(central_widget)
        rgb_settings_layout = QFormLayout(self.rgb_band_settings)
        rgb_settings_layout.setContentsMargins(0, 0, 0, 0)
        self.rgb_combo_r = QComboBox(self.rgb_band_settings)
        self.rgb_combo_r.currentIndexChanged.connect(self.r_band_changed)
        self.rgb_combo_g = QComboBox(self.rgb_band_settings)
        self.rgb_combo_g.currentIndexChanged.connect(self.g_band_changed)
        self.rgb_combo_b = QComboBox(self.rgb_band_settings)
        self.rgb_combo_b.currentIndexChanged.connect(self.b_band_changed)
        rgb_settings_layout.addRow("Red band", self.rgb_combo_r)
        rgb_settings_layout.addRow("Green band", self.rgb_combo_g)
        rgb_settings_layout.addRow("Blue band", self.rgb_combo_b)
        self.rgb_band_settings.setLayout(rgb_settings_layout)
        self.rgb_band_settings.setVisible(False)

        # ****** Magic Wand ******

        self.label_wand = QLabel("Magic wand", self)

        self.button_magic = QPushButton(self)
        self.button_magic.setText("Magic wand")
        self.button_magic.clicked.connect(self.magic_wand_click)

        # Magic wand settings
        mw_settings_widget = QWidget(central_widget)
        magic_wand_layout = QFormLayout(mw_settings_widget)
        magic_wand_layout.setContentsMargins(0, 0, 0, 0)

        threshold_label = QLabel("Threshold (% of max MSE)")
        magic_wand_layout.setWidget(
            0, QFormLayout.ItemRole.SpanningRole, threshold_label
        )

        self.input_magic_wand = QDoubleSpinBox(mw_settings_widget)
        self.input_magic_wand.setDecimals(6)
        self.input_magic_wand.setMinimum(0.000001)
        self.input_magic_wand.setMaximum(80.0)
        self.input_magic_wand.setSingleStep(0.1)
        self.input_magic_wand.setValue(1.0)
        self.input_magic_wand.valueChanged.connect(self.threshold_input_changed)

        self.slider_magic_wand = QSlider(Qt.Orientation.Horizontal, mw_settings_widget)
        self.slider_magic_wand.setMinimum(0)
        self.slider_magic_wand.setMaximum(80)
        self.slider_magic_wand.setValue(60)
        self.slider_magic_wand.setTickPosition(QSlider.TickPosition.TicksBothSides)
        self.slider_magic_wand.setTickInterval(5)
        self.slider_magic_wand.setTracking(True)
        self.slider_magic_wand.valueChanged.connect(self.threshold_slider_changed)

        magic_wand_layout.addRow(self.input_magic_wand, self.slider_magic_wand)

        # ****** Spectral curve ******

        self.label_spectral = QLabel("Spectral curve", self)

        self.select_point = QPushButton(self)
        self.select_point.setText("Select point")
        self.select_point.clicked.connect(self.select_point_click)

        self.select_area = QPushButton(self)
        self.select_area.setText("Select area")
        self.select_area.clicked.connect(self.select_area_click)

        # ****** Add elements to layout ******

        """Change the order of toolbars; maybe select_point/area to toolbar1?"""

        toolbar_mode.addWidget(self.single_band_button)
        toolbar_mode.addWidget(self.fake_col_button)

        toolbar_image_settings.addWidget(self.single_band_settings)
        toolbar_image_settings.addWidget(self.rgb_band_settings)

        toolbar_tools.addWidget(self.label_wand)
        toolbar_tools.addWidget(self.button_magic)
        toolbar_tools.addWidget(mw_settings_widget)

        toolbar_tools.addWidget(self.label_spectral)
        toolbar_tools.addWidget(self.select_point)
        toolbar_tools.addWidget(self.select_area)

        self.spectral_viewer = SpectralViewer(self)
        spectrum_graph.addWidget(self.spectral_viewer)
        self.image_preview = ImagePreview(self)
        viewer.addWidget(self.image_preview)

        # ****** Menu bar ******
        self._createMenuBar()

    def _createMenuBar(self):
        menuBar = QMenuBar(self)
        self.setMenuBar(menuBar)
        fileMenu = menuBar.addMenu("&File")

        # File menu
        action_open = QAction("Open", self)
        action_open.triggered.connect(self.open_click)
        action_open.setShortcut(QKeySequence.StandardKey.Open)
        action_exit = QAction("Exit", self)
        action_exit.triggered.connect(lambda: exit())
        action_exit.setShortcuts(QKeySequence.StandardKey.Quit)
        fileMenu.addAction(action_open)
        fileMenu.addAction(action_exit)

    """Methods responsible for handling interaction with buttons etc."""

    def single_band_click(self):
        print("clicked single band")
        if self.state != ApplicationState.NO_IMAGE:
            self.image_preview.clear_rubber_band()
            self.image_mode = ImageMode.MONO
            self.state = ApplicationState.IMAGE_LOADED
            self.rgb_band_settings.setVisible(False)
            self.single_band_settings.setVisible(True)
            self.render_image()

    def fake_col_click(self):
        print("clicked fake color")
        if self.state != ApplicationState.NO_IMAGE:
            self.image_preview.clear_rubber_band()
            self.image_mode = ImageMode.RGB
            self.state = ApplicationState.IMAGE_LOADED
            self.rgb_band_settings.setVisible(True)
            self.single_band_settings.setVisible(False)
            self.render_image()

    def magic_wand_click(self):
        print("clicked magic wand")
        self.image_preview.clear_rubber_band()
        self.state = ApplicationState.SELECT_SIMILAR

    def select_point_click(self):
        print("clicked select point")
        self.image_preview.clear_rubber_band()
        self.state = ApplicationState.SELECT_PX

    def select_area_click(self):
        print("clicked select area")
        self.image_preview.clear_rubber_band()
        self.state = ApplicationState.SELECT_AREA_FIRST

    def open_click(self):
        print("clicked open in menu bar")
        img = self.loader.open_file()
        if img is not None:
            # Set NO_IMAGE to disable some event handlers
            self.state = ApplicationState.NO_IMAGE
            for combo in [
                self.sb_combo,
                self.rgb_combo_r,
                self.rgb_combo_g,
                self.rgb_combo_b,
            ]:
                combo.clear()
                combo.addItems(img.labels)

            rgb_idx = img.closest_rgb_idx()
            if rgb_idx is not None:
                self.image_mode = ImageMode.RGB
                self.band_r, self.band_g, self.band_b = rgb_idx
                self.rgb_combo_r.setCurrentIndex(self.band_r)
                self.rgb_combo_g.setCurrentIndex(self.band_g)
                self.rgb_combo_b.setCurrentIndex(self.band_b)
                self.band_mono = 0
                self.rgb_band_settings.setVisible(True)
                self.single_band_settings.setVisible(False)
            else:
                self.image_mode = ImageMode.MONO
                self.band_r, self.band_g, self.band_b = 0, 0, 0
                self.band_mono = 0
                self.rgb_band_settings.setVisible(False)
                self.single_band_settings.setVisible(True)

            self.image_preview.clear_rubber_band()
            self.spectral_viewer.clear()
            self.spectral_viewer.update_labels(img.labels, img.labels_type)
            self.image = img
            self.state = ApplicationState.IMAGE_LOADED
            self.similar_mask = None

            self.render_image()

    def mono_band_changed(self, idx: int):
        print(
            "Mono band changed to",
            idx,
            "ignoring"
            if self.state == ApplicationState.NO_IMAGE or idx == -1
            else "processing",
        )
        if self.state != ApplicationState.NO_IMAGE or idx == -1:
            self.band_mono = idx
            self.render_image()

    def r_band_changed(self, idx: int):
        print(
            "Red band changed to",
            idx,
            "ignoring"
            if self.state == ApplicationState.NO_IMAGE or idx == -1
            else "processing",
        )
        if self.state != ApplicationState.NO_IMAGE or idx == -1:
            self.band_r = idx
            if self.image_mode == ImageMode.RGB:
                self.render_image()

    def g_band_changed(self, idx: int):
        print(
            "Green band changed to",
            idx,
            "ignoring"
            if self.state == ApplicationState.NO_IMAGE or idx == -1
            else "processing",
        )
        if self.state != ApplicationState.NO_IMAGE or idx == -1:
            self.band_g = idx
            if self.image_mode == ImageMode.RGB:
                self.render_image()

    def b_band_changed(self, idx: int):
        print(
            "Blue band changed to",
            idx,
            "ignoring"
            if self.state == ApplicationState.NO_IMAGE or idx == -1
            else "processing",
        )
        if self.state != ApplicationState.NO_IMAGE or idx == -1:
            self.band_b = idx
            if self.image_mode == ImageMode.RGB:
                self.render_image()

    def threshold_input_changed(self, new_val: float):
        if self.threshold == new_val or self.ignore_threshold_change:
            self.ignore_threshold_change = False
            return

        print("Threshold input changed to", new_val)
        self.threshold = new_val
        slider_pos = 10 * (math.log10(new_val) + 6)
        self.ignore_threshold_change = True
        self.slider_magic_wand.setValue(int(slider_pos))

    def threshold_slider_changed(self, tick: int):
        if self.ignore_threshold_change:
            self.ignore_threshold_change = False
            return

        print("Threshold slider changed to", tick)
        val = pow(10, tick / 10 - 6)
        if self.threshold != val:
            self.threshold = val
            self.ignore_threshold_change = True
            self.input_magic_wand.setValue(val)

    def on_mouse_down(self, coordinates: Coordinates):
        print("mouse down at", coordinates)
        if self.state == ApplicationState.SELECT_AREA_FIRST:
            self.start_position = coordinates
            self.state = ApplicationState.SELECT_AREA_SECOND
            self.image_preview.draw_rubber_band(coordinates)

    def on_mouse_up(self, coordinates: Coordinates):
        print("mouse up at", coordinates)
        assert self.image is not None

        match self.state:
            case ApplicationState.SELECT_PX:
                px = self.image.get_pixel(*coordinates)
                self.spectral_viewer.from_pixel(px)
                self.state = ApplicationState.IMAGE_LOADED
            case ApplicationState.SELECT_AREA_SECOND:
                self.image_preview.clear_rubber_band()
                self.state = ApplicationState.IMAGE_LOADED
                area = self.image.get_area(self.start_position, coordinates)
                self.spectral_viewer.from_area(area)
            case ApplicationState.SELECT_SIMILAR:
                self.state = ApplicationState.IMAGE_LOADED
                self.similar_mask = self.image.get_similar(coordinates, self.threshold)
                self.image_mode = ImageMode.SIMILAR
                self.rgb_band_settings.setVisible(False)
                self.single_band_settings.setVisible(True)
                self.render_image()

    def render_image(self):
        assert self.image is not None

        if self.image.data.dtype.kind == "f":
            match self.image_mode:
                case ImageMode.MONO:
                    self.image_preview.render_single_f(
                        self.image.get_band_normalised(self.band_mono)
                    )
                case ImageMode.RGB:
                    self.image_preview.render_rgb_f(
                        self.image.get_RGB_bands_normalised(
                            self.band_r, self.band_g, self.band_b
                        )
                    )
                case ImageMode.SIMILAR:
                    assert self.similar_mask is not None
                    self.image_preview.render_similar_f(
                        self.image.get_band_normalised(self.band_mono),
                        self.similar_mask,
                    )
        else:
            match self.image_mode:
                case ImageMode.MONO:
                    data = self.image.get_band(self.band_mono)
                    data = self.image.as_8bpp(data)
                    self.image_preview.render_single(data)
                case ImageMode.RGB:
                    data = self.image.get_RGB_bands(
                        self.band_r, self.band_g, self.band_b
                    )
                    data = self.image.as_8bpp(data)
                    self.image_preview.render_rgb(data)
                case ImageMode.SIMILAR:
                    assert self.similar_mask is not None
                    data = self.image.get_band(self.band_mono)
                    data = self.image.as_8bpp(data)
                    self.image_preview.render_similar(data, self.similar_mask)


def main():
    if os.name == "nt":
        if not "QT_QPA_PLATFORM" in os.environ:
            os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=2"
        if not "QT_STYLE_OVERRIDE" in os.environ:
            os.environ["QT_STYLE_OVERRIDE"] = "fusion"

    a = QApplication(argv)
    main_window = MainWindow()
    main_window.start()
    a.exec()


if __name__ == "__main__":
    main()
