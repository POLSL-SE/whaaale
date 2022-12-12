from enum import Enum
from math import inf
from typing import Generic, Optional, TypeAlias, TypeVar, Callable, Any

import numpy as np
import numpy.typing as npt

Coordinates: TypeAlias = tuple[int, int]
ScalarType = TypeVar("ScalarType", np.floating, np.signedinteger, np.unsignedinteger)


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


class NormalisationMethod(Enum):
    """Defines how floating point data should be normalised."""

    GLOBAL = 1
    """Global maximum and minimum (excluding negative values) should be used as 1 and 0"""
    BAND = 2
    """Maximum and minimum must be separate for each band"""


class HsImage(Generic[ScalarType]):
    """Hyperspectral image data"""

    def __init__(
        self,
        data: npt.NDArray[ScalarType],
        bpp: Optional[int] = None,
        normalisation: Optional[NormalisationMethod] = None,
        labels: Optional[list[str]] = None,
        labels_type: Optional[LabelType] = None,
    ) -> None:
        if data.ndim != 3:
            raise ValueError('"data" parameter must have 3 dimensions')

        pos_mask = data >= 0

        if (data.dtype.kind == "i" or data.dtype.kind == "u") and bpp is None:
            raise RuntimeError("Integer data loaded, but bpp is None")
        if data.dtype.kind == "f":
            match normalisation:
                case None:
                    raise RuntimeError(
                        "Floating point dara loaded, but normalisation is None"
                    )
                case NormalisationMethod.GLOBAL:
                    ax = None
                case NormalisationMethod.BAND:
                    ax = (0, 1)

            norm_min = np.amin(data, axis=ax, initial=np.inf, where=pos_mask)
            norm_max = np.amax(data, axis=ax, initial=-np.inf, where=pos_mask)

            if ax is None and (norm_min == np.inf or norm_max == -np.inf):
                raise ValueError(
                    "Image contains invalid data - all values are negative or infinity."
                )
            if ax is not None:
                norm_min[norm_min == np.inf] = 0
                norm_max[norm_max == -np.inf] = 0

            self.norm_div: Optional[npt.NDArray[np.floating] | float] = (
                norm_max - norm_min
            )
            self.norm_min: Optional[npt.NDArray[np.floating] | float] = norm_min

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
        self.normalisation = normalisation
        self.bpp = bpp
        """Bits per pixel for integer data"""
        self.labels = labels
        """Labels for all bands"""
        self.labels_type = labels_type
        """Origin and type of labels"""
        self.bands = bands
        """Number of bands in the image"""
        self.pos_mask = pos_mask
        """A boolean mask of non-negative data"""

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
        if self.bpp is not None:
            threshold = ((1 << self.bpp) - 1) ** 2 * threshold_percent / 100
        else:
            threshold = threshold_percent / 100.0
        flattened = self.normalised().reshape((h * w, b))
        mse: npt.NDArray[np.float_] = (
            np.square(flattened - base).mean(axis=1).reshape((h, w))
        )
        return mse <= threshold

    def get_band(self, idx: int) -> npt.NDArray[ScalarType]:
        """Returns a single band of the image."""
        return self.data[:, :, idx]

    def get_RGB_bands(
        self, r_idx: int, g_idx: int, b_idx: int
    ) -> npt.NDArray[ScalarType]:
        """Returns three selected bands of the image."""
        assert self.bands >= 3
        return self.data[:, :, (r_idx, g_idx, b_idx)]

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

    def normalised(self):
        """Returns image data normalised to [0, 1] range if the data is integer. Integer data is left unchanged."""
        if self.norm_div is None or self.norm_min is None:
            return self.data
        else:
            return (self.data - self.norm_min) / self.norm_div

    def get_norm_prop(self, *args: tuple[int] | tuple[int, int, int]):
        if self.normalisation == NormalisationMethod.GLOBAL:
            if self.norm_min is None or self.norm_div is None:
                raise RuntimeError("Global normalisation, but values are None")
            return self.norm_min, self.norm_div
        elif isinstance(self.norm_min, np.ndarray) and isinstance(
            self.norm_div, np.ndarray
        ):
            if len(args) == 1:
                return self.norm_min[*args], self.norm_div[*args]
            else:
                return (
                    self.norm_min[
                        args,
                    ],
                    self.norm_div[
                        args,
                    ],
                )

    @staticmethod
    def _normalise(
        func: Callable[[Any, int], npt.NDArray]
        | Callable[[Any, int, int, int], npt.NDArray]
    ):
        def wrapper(self, *args):
            norm_data = self.get_norm_prop(*args)
            if norm_data is None:
                return func(self, *args)
            norm_min, norm_max = norm_data
            return (func(self, *args) - norm_min) / norm_max

        return wrapper

    @_normalise
    def get_band_normalised(self, idx: int):
        """Returns a single band of the image normalised to [0, 1]."""
        return self.get_band(idx)

    @_normalise
    def get_RGB_bands_normalised(self, r_idx: int, g_idx: int, b_idx: int):
        """Returns three selected bands of the image normalised to [0, 1]."""
        return self.get_RGB_bands(r_idx, g_idx, b_idx)

    def as_8bpp(self, data: npt.NDArray[np.signedinteger | np.unsignedinteger]):
        assert data.dtype.kind == "i" or data.dtype.kind == "u"
        assert self.bpp and self.bpp >= 8

        bpp_diff = self.bpp - 8
        # Type conversion to uint8 is time consuming, but Qt expects data in such format.
        # We cant just pass 32-bit values capped at 255
        rounded = ((data + (1 << (bpp_diff - 1))) >> bpp_diff).astype(np.uint8)
        rounded[rounded < 0] = 0
        return rounded
