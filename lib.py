from typing import Generic, TypeAlias, TypeVar

import numpy as np
import numpy.typing as npt

Coordinates: TypeAlias = tuple[int, int]
ScalarType = TypeVar("ScalarType", bound=np.generic, covariant=True)


class HsImage(Generic[ScalarType]):
    """Hyperspectral image data"""

    def __init__(
        self, data: npt.NDArray[ScalarType], bpp: int, labels: list[str] | None = None
    ) -> None:
        if data.ndim != 3:
            raise ValueError('"data" parameter must have 3 dimensions')

        bands = data.shape[2]
        if labels is None:
            labels = [str(x) for x in range(bands)]
        elif len(labels) != bands:
            raise ValueError("Number of labels must be equal to the number of bands")

        self.data = data
        self.bpp = bpp
        """Bits per pixel"""
        self.labels = labels
        """Labels for all bands"""
        self.bands = bands
        """Number of bands in the image"""

    def get_pixel(self, x: int, y: int) -> npt.NDArray[ScalarType]:
        """Returns a single pixel of the image as a 1D `ndarray`."""
        return self.data[x, y]

    def get_area(self, p1: Coordinates, p2: Coordinates) -> npt.NDArray[ScalarType]:
        """Returns a subarray from the image bounded by `p1` and `p2`."""
        x_min, x_max = p1[0], p2[0] if p1[0] <= p2[0] else p2[0], p1[0]
        y_min, y_max = p1[1], p2[1] if p1[1] <= p2[1] else p2[1], p1[1]
        # Add 1, because ranges don't include the upper bound
        x_max += 1
        y_max += 1
        return self.data[x_min:x_max, y_min:y_max]

    def get_similar(
        self, base_coordinates: Coordinates, threshold_percent: float
    ) -> npt.NDArray[np.bool_]:
        """Returns a truth mask of pixels similar to the one with `base_coordinates` within threshold defined as percent of the maximum MSE (depends on `bpp`)."""
        base = self.data[base_coordinates]
        h, w, b = self.data.shape
        threshold = ((1 << self.bpp) - 1) ** 2 * threshold_percent / 100
        flattened = self.data.reshape((h * w, b))
        mse: npt.NDArray[np.float_] = (
            np.square(flattened - base).mean(axis=1).reshape((h, w))
        )
        return mse <= threshold

    def get_band(self, idx: int) -> npt.NDArray[ScalarType]:
        """Returns a single band of the image."""
        return self.data[:, :, idx]

    def get_RGB_bands(
        self, r_inx: int, g_idx: int, b_idx: int
    ) -> npt.NDArray[ScalarType]:
        """Returns three selected bands of the image."""
        assert self.bands >= 3
        return self.data[:, :, (r_inx, g_idx, b_idx)]
