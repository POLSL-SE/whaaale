from typing import Any, Callable, Optional

import numpy as np
import numpy.typing as npt
from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtGui import QImage, QMouseEvent, QPixmap, QFont
from PyQt6.QtWidgets import (
    QGridLayout,
    QLabel,
    QRubberBand,
    QScrollArea,
    QSizePolicy,
    QWidget,
)

from lib import Coordinates


class ImagePreview(QWidget):
    img_data: Optional[npt.NDArray[np.uint8 | np.float32]] = None
    handler_mouse_down: Optional[Callable[[Coordinates], Any]] = None
    handler_mouse_up: Optional[Callable[[Coordinates], Any]] = None

    def __init__(
        self, parent: Optional[QWidget], flags: Qt.WindowType = Qt.WindowType.Widget
    ) -> None:
        super().__init__(parent, flags)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        font = QFont()
        font.setPointSize(12)
        font.setBold(True)

        self.label = QLabel("Open an image to display preview.", self.scroll_area)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.label.setFont(font)
        self.scroll_area.setWidget(self.label)

        grid_layout = QGridLayout()
        grid_layout.addWidget(self.scroll_area)
        self.setLayout(grid_layout)

        self.rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self.label)
        self.rubber_band.setVisible(False)

        self._setup_handlers()

    def _setup_handlers(self):
        # In disabled (default) state mouse movement is tracked only when a button is pressed
        self.label.setMouseTracking(False)
        self.label.mousePressEvent = lambda ev: self._on_mouse_down(ev)
        self.label.mouseReleaseEvent = lambda ev: self._on_mouse_up(ev)
        self.label.mouseMoveEvent = lambda ev: self._on_mouse_move(ev)

    def _on_mouse_down(self, event: QMouseEvent):
        if self.handler_mouse_down is not None and self.img_data is not None:
            pos = event.position()
            x = int(pos.x())
            y = int(pos.y())
            self.handler_mouse_down(self.clamp_xy(x, y))
        event.accept()

    def _on_mouse_up(self, event: QMouseEvent):
        if self.handler_mouse_up is not None and self.img_data is not None:
            pos = event.position()
            x = int(pos.x())
            y = int(pos.y())
            self.handler_mouse_up(self.clamp_xy(x, y))
        event.accept()

    def _on_mouse_move(self, event: QMouseEvent):
        if self.rubber_band.isVisible():
            pos = event.position()
            x = int(pos.x())
            y = int(pos.y())
            x, y = self.clamp_xy(x, y)
            geometry = QRect.span(self.rubber_band_start, QPoint(x, y))
            self.rubber_band.setGeometry(geometry)
        event.accept()

    def register_handlers(
        self,
        on_mouse_down: Callable[[Coordinates], Any],
        on_mouse_up: Callable[[Coordinates], Any],
    ):
        self.handler_mouse_down = on_mouse_down
        self.handler_mouse_up = on_mouse_up

    def draw_rubber_band(self, start: Coordinates):
        self.rubber_band_start = QPoint(*start)
        self.rubber_band.move(self.rubber_band_start)
        self.rubber_band.resize(0, 0)
        self.rubber_band.setVisible(True)

    def clear_rubber_band(self):
        self.rubber_band.setVisible(False)

    def render_rgb(self, rgb_bands: npt.NDArray[np.uint8]):
        self.img_data = rgb_bands.copy()
        h, w, _ = self.img_data.shape
        self.image = QImage(
            self.img_data.data,
            w,
            h,
            self.img_data.strides[0],
            QImage.Format.Format_RGB888,
        )
        self._show_image()

    def render_rgb_f(self, rgb_bands: npt.NDArray[np.floating]):
        img_data = rgb_bands.astype(np.float32)
        h, w, _ = img_data.shape
        self.img_data = np.append(
            img_data, np.ones((h, w, 1), dtype=np.float32), axis=2
        ).copy()
        self.image = QImage(
            self.img_data.data,
            w,
            h,
            self.img_data.strides[0],
            QImage.Format.Format_RGBX32FPx4,
        )
        self._show_image()

    def render_single(self, band: npt.NDArray[np.uint8]):
        self.img_data = band.copy()
        h, w = self.img_data.shape
        self.image = QImage(
            self.img_data.data,
            w,
            h,
            self.img_data.strides[0],
            QImage.Format.Format_Grayscale8,
        )
        self._show_image()

    def render_single_f(self, band: npt.NDArray[np.floating]):
        self.render_single((band * 255).astype(np.uint8))

    def render_similar(self, band: npt.NDArray[np.uint8], mask: npt.NDArray[np.bool8]):
        band_3D = np.broadcast_to(band[..., None], band.shape + (3,)).copy()
        band_3D[mask] = np.array([255, 0, 0])
        self.img_data = band_3D
        self.image = QImage(
            self.img_data.data,
            self.img_data.shape[1],
            self.img_data.shape[0],
            self.img_data.strides[0],
            QImage.Format.Format_RGB888,
        )
        self._show_image()

    def render_similar_f(
        self, band: npt.NDArray[np.floating], mask: npt.NDArray[np.bool8]
    ):
        self.render_similar((band * 255).astype(np.uint8), mask)

    def _show_image(self):
        height = self.image.height()
        width = self.image.width()
        self.pixmap = QPixmap.fromImage(self.image)
        self.label.setPixmap(self.pixmap)
        self.label.setFixedSize(width, height)

    def clamp_xy(self, x: int, y: int):
        assert self.img_data is not None
        x = max(0, min(self.img_data.shape[1] - 1, x))
        y = max(0, min(self.img_data.shape[0] - 1, y))
        return x, y
