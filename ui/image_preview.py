from typing import Optional

import numpy as np
import numpy.typing as npt
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QGridLayout, QLabel, QSizePolicy, QWidget


class ImagePreview(QWidget):
    img_data: Optional[npt.NDArray[np.uint8 | np.float32]] = None

    def __init__(
        self, parent: Optional[QWidget], flags: Qt.WindowType = Qt.WindowType.Widget
    ) -> None:
        super().__init__(parent, flags)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.label.setMouseTracking(True)
        self.label.setText("Open an image")

        grid_layout = QGridLayout()
        grid_layout.addWidget(self.label)
        self.setLayout(grid_layout)

    def render_rgb(self, rgb_bands: npt.NDArray[np.uint8]):
        self.img_data = rgb_bands.copy()
        self.image = QImage(
            self.img_data.data,
            self.img_data.shape[1],
            self.img_data.shape[0],
            3 * self.img_data.shape[1],
            QImage.Format.Format_RGB888,
        )
        self.pixmap = QPixmap.fromImage(self.image)
        self.label.setPixmap(self.pixmap)

    def render_rgb_f(self, rgb_bands: npt.NDArray[np.floating]):
        img_data = rgb_bands.astype(np.float32)
        h, w, _ = img_data.shape
        self.img_data = np.append(
            img_data, np.ones((h, w, 1), dtype=np.float32), axis=2
        ).copy()
        self.image = QImage(
            self.img_data.data,
            self.img_data.shape[1],
            self.img_data.shape[0],
            16 * self.img_data.shape[1],
            QImage.Format.Format_RGBX32FPx4,
        )
        self.pixmap = QPixmap.fromImage(self.image)
        self.label.setPixmap(self.pixmap)

    def render_single(self, band: npt.NDArray[np.uint8]):
        self.img_data = band.copy()
        self.image = QImage(
            self.img_data.data,
            self.img_data.shape[1],
            self.img_data.shape[0],
            self.img_data.shape[1],
            QImage.Format.Format_Grayscale8,
        )
        self.pixmap = QPixmap.fromImage(self.image)
        self.label.setPixmap(self.pixmap)

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
            3 * self.img_data.shape[1],
            QImage.Format.Format_RGB888,
        )
        self.pixmap = QPixmap.fromImage(self.image)
        self.label.setPixmap(self.pixmap)
