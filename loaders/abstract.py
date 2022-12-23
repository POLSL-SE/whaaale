from abc import ABC, abstractmethod
from math import ceil, log2
from typing import Optional

import numpy as np
import numpy.typing as npt
from PyQt6.QtWidgets import QInputDialog, QWidget

from lib import HsImage, NormalisationMethod, ScalarType
from utils import staticproperty


class AbstractFileLoader(ABC):
    @staticproperty
    @abstractmethod
    def FILE_FILTER_NAME() -> str:
        """A user friendly filter name for the "open file" dialog."""
        pass

    @staticproperty
    @abstractmethod
    def EXTENSIONS() -> list[str]:
        """A list of supported extensions.

        Examples:
        ```
            ["exe", "cmd"]
            ["png"]
            ["jpg", "jpeg"]
        ```
        """
        pass

    @staticmethod
    @abstractmethod
    def load_file(path: str, parent: QWidget) -> Optional[HsImage]:
        """Loads a file given its path. `parent` is provided to be used as a parent `QWidget` for dialogs/popups.
        Returns `None` if user cancels the operation.
        """
        pass

    @staticmethod
    def get_normalisation(parent: QWidget) -> Optional[NormalisationMethod]:
        GLOBAL = "Global"
        BAND = "Per band"
        norm, ok = QInputDialog.getItem(
            parent,
            "Whaaale - open file",
            "Normalisation method:",
            [GLOBAL, BAND],
            editable=False,
        )
        if norm == GLOBAL:
            return NormalisationMethod.GLOBAL
        if norm == BAND:
            return NormalisationMethod.BAND

    @staticmethod
    def get_bpp(data: npt.NDArray[ScalarType], parent: QWidget) -> Optional[int]:
        max = data.dtype.itemsize * 8
        max_val: ScalarType = np.max(data)
        min_bpp = ceil(log2(max_val))

        bpp, ok = QInputDialog.getInt(
            parent,
            "Whaaale - open file",
            "Bits per pixel:",
            min=min_bpp,
            max=max,
        )

        if ok:
            return bpp

    @staticmethod
    def fix_array_order(data: npt.NDArray[ScalarType], parent: QWidget):
        HWB = "[height, width, bands]"
        WHB = "[width, height, bands]"
        BHW = "[bands, height, width]"
        BWH = "[bands, width, height]"

        option, ok = QInputDialog.getItem(
            parent,
            "Whaaale - open file",
            f"Array order [{', '.join([str(x) for x in data.shape])}]:",
            [HWB, WHB, BHW, BWH],
            editable=False,
        )

        if not ok:
            return

        if option == HWB:
            return data
        elif option == WHB:
            return data.transpose((1, 0, 2))
        elif option == BHW:
            return data.transpose((1, 2, 0))
        elif option == BWH:
            return data.transpose((2, 1, 0))
