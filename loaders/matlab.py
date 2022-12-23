from typing import Any, BinaryIO, Optional

import h5py
import numpy as np
import numpy.typing as npt
import scipy.io as sio
from PyQt6.QtWidgets import QInputDialog, QWidget

from lib import HsImage
from loaders.abstract import AbstractFileLoader
from utils import staticproperty


class MatlabLoader(AbstractFileLoader):
    DIALOG_TITLE = "Matlab file loader"

    @staticproperty
    def FILE_FILTER_NAME() -> str:
        return "Matlab files"

    @staticproperty
    def EXTENSIONS() -> list[str]:
        return ["mat"]

    @staticmethod
    def load_hdf5(raw_file: BinaryIO, parent: QWidget) -> Optional[HsImage]:
        data = h5py.File(raw_file)
        names: list[str] = [
            k for k, v in data.items() if (not k.startswith("#") and v.ndim == 3)
        ]
        var_name = MatlabLoader.check_vars(data, names, parent)
        if var_name is None:
            return

        # Extract data as NumPy array
        # https://docs.h5py.org/en/stable/whatsnew/2.1.html#dataset-value-property-is-now-deprecated
        var: npt.NDArray = data[var_name][()]
        if var.dtype.kind != "i" and var.dtype.kind != "u" and var.dtype.kind != "f":
            raise NotImplementedError(
                f"Only integer and floating point types are supported, file uses {var.dtype.name}."
            )

        reordered = MatlabLoader.fix_array_order(var, parent)
        if reordered is None:
            return
        else:
            var = reordered

        if var.dtype.kind == "f":
            bpp = None
            normalisation = MatlabLoader.get_normalisation(parent)
            if normalisation is None:
                return
        else:
            bpp = MatlabLoader.get_bpp(var, parent)
            if bpp is None:
                return
            normalisation = None

        image = HsImage(var, bpp=bpp, normalisation=normalisation)
        return image

    @staticmethod
    def load_scipy(file: BinaryIO, parent: QWidget) -> Optional[HsImage]:
        data: dict[str, Any] = sio.loadmat(file)
        names = [
            k
            for k, v in data.items()
            if (not k.startswith("__")) and isinstance(v, np.ndarray) and v.ndim == 3
        ]
        var_name = MatlabLoader.check_vars(data, names, parent)
        if var_name is None:
            return

        var: npt.NDArray = data[var_name]
        if var.dtype.kind != "i" and var.dtype.kind != "u" and var.dtype.kind != "f":
            raise NotImplementedError(
                f"Only integer and floating point types are supported, file uses {var.dtype.name}."
            )

        reordered = MatlabLoader.fix_array_order(var, parent)
        if reordered is None:
            return
        else:
            var = reordered

        if var.dtype.kind == "f":
            bpp = None
            normalisation = MatlabLoader.get_normalisation(parent)
            if normalisation is None:
                return
        else:
            bpp = MatlabLoader.get_bpp(var, parent)
            if bpp is None:
                return
            normalisation = None

        image = HsImage(var, bpp=bpp, normalisation=normalisation)
        return image

    @staticmethod
    def check_vars(
        data: dict[str, Any] | h5py.File, names: list[str], parent: QWidget
    ) -> Optional[str]:
        n_names = len(names)
        if n_names == 0:
            raise RuntimeError("No 3D arrays found in the data file.")
        elif n_names > 1:
            shapes: list[tuple[int, int, int]] = [data[name].shape for name in names]
            var_name = MatlabLoader.select_var(parent, names, shapes)
        else:
            var_name = names[0]

        return var_name

    @staticmethod
    def select_var(
        parent: QWidget, vars: list[str], shapes: list[tuple[int, int, int]]
    ) -> Optional[str]:
        assert len(vars) == len(shapes)

        descriptions = [f"{var} {shape}" for (var, shape) in zip(vars, shapes)]
        selected, ok = QInputDialog.getItem(
            parent,
            MatlabLoader.DIALOG_TITLE,
            "Variable containing image:",
            descriptions,
            editable=False,
        )

        if not ok:
            return

        # Extract name from description. Variables can't contain spaces, so it's ok.
        name = selected.split(" ")[0]
        return name

    @staticmethod
    def load_file(path: str, parent: QWidget) -> Optional[HsImage]:
        with open(path, "rb") as file:
            header = file.read(19)
            # "rewind" back to the beginning
            file.seek(0)

            if header == b"MATLAB 7.3 MAT-file":
                image = MatlabLoader.load_hdf5(file, parent)
            else:
                image = MatlabLoader.load_scipy(file, parent)

        return image
