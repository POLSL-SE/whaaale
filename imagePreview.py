from typing import Optional

from PySide2.QtCore import QPoint, QRect
from PySide2.QtGui import QMouseEvent, QPixmap
from PySide2.QtWidgets import QRubberBand, QWidget


class ImagePreview(QWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.bitmap = QPixmap()
        self.rubber_band: Optional[QRubberBand] = None

    def on_mouse_down(self, event: QMouseEvent) -> None:
        self.start_position = event.pos()
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
        self.rubber_band.setGeometry(
            QRect(self.start_position, QPoint())
        )
        self.rubber_band.show()

    def on_mouse_up(self, event: QMouseEvent) -> None:
        self.rubber_band.hide()

    def on_mouse_move(self, event: QMouseEvent) -> None:
        if not self.start_position:
            return
        self.rubber_band.setGeometry(
            QRect(self.start_position, event.pos()).normalized()
        )

    def render_single(self, band: ndarray, bpp: int) -> None:
        pass

    def render_rgb(self, rgb_bands: ndarray, bpp: int) -> None:
        pass

    def render_similar(self, band: ndarray, bpp: int, mask: ndarray) -> None:
        pass
