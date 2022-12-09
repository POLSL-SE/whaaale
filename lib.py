from enum import Enum
from math import inf
from typing import Generic, Optional, TypeAlias, TypeVar

import numpy as np
import numpy.typing as npt

Coordinates: TypeAlias = tuple[int, int]
ScalarType = TypeVar("ScalarType", bound=np.generic, covariant=True)


class LabelType(Enum):
    """Describes the origin of image labels.

    The following values are available:
    - `AUTO`
    - `WAVELENGTH`
    - `CUSTOM_STR`
    """

    AUTO = 0
    """An integer sequence generated automatically, convertible to `int`, same as `list(range(n_bands))`"""
    WAVELENGTH = 1
    """Floating point numbers representing wavelengths (in nm), convertible to `float`"""
    CUSTOM_STR = 2
    """Custom string labels, conversion to numeric type should not be attempted"""


class HsImage(Generic[ScalarType]):
    """Hyperspectral image data"""

    def __init__(
        self,
        data: npt.NDArray[ScalarType],
        bpp: int,
        labels: Optional[list[str]] = None,
        labels_type: Optional[LabelType] = None,
    ) -> None:
        if data.ndim != 3:
            raise ValueError('"data" parameter must have 3 dimensions')

        bands = data.shape[2]
        if labels is None:
            labels = [str(x) for x in range(bands)]
            labels_type = LabelType.AUTO
        else:
            if len(labels) != bands:
                raise ValueError(
                    "Number of labels must be equal to the number of bands"
                )
            if labels_type is None:
                # `CUSTOM_STR` is a safe fallback value
                labels_type = LabelType.CUSTOM_STR

        self.data = data
        self.bpp = bpp
        """Bits per pixel"""
        self.labels = labels
        """Labels for all bands"""
        self.labels_type = labels_type
        """Origin and type of labels"""
        self.bands = bands
        """Number of bands in the image"""

    def get_pixel(self, x: int, y: int) -> npt.NDArray[ScalarType]:
        """Returns a single pixel of the image as a 1D `ndarray`."""
        return self.data[x, y]

    def get_area(self, p1: Coordinates, p2: Coordinates) -> npt.NDArray[ScalarType]:
        """Returns a subarray from the image bounded by `p1` and `p2`."""
        x_min, x_max = (p1[0], p2[0]) if p1[0] <= p2[0] else (p2[0], p1[0])
        y_min, y_max = (p1[1], p2[1]) if p1[1] <= p2[1] else (p2[1], p1[1])
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

    def closest_rgb_idx(self):
        """Returns indexes of bands with wavelengths closest to RGB pixel frequencies or `None`."""
        if self.labels_type != LabelType.WAVELENGTH:
            return

        R_WAVELENGTH = 630
        G_WAVELENGTH = 532
        B_WAVELENGTH = 465
        diff_r = inf
        diff_g = inf
        diff_b = inf
        r_idx = 0
        g_idx = 0
        b_idx = 0
        try:
            for i, l in enumerate(self.labels):
                lf = float(l)
                dr = abs(R_WAVELENGTH - lf)
                dg = abs(G_WAVELENGTH - lf)
                db = abs(B_WAVELENGTH - lf)
                if dr < diff_r:
                    diff_r = dr
                    r_idx = i
                if dg < diff_g:
                    diff_g = dg
                    g_idx = i
                if db < diff_b:
                    diff_b = db
                    b_idx = i
        except ValueError:
            return

        if max(diff_r, diff_g, diff_b) < 30:
            return r_idx, g_idx, b_idx
