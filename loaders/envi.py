import os
from math import ceil, log2
from string import whitespace
from typing import Optional

import numpy as np
import numpy.typing as npt
from osgeo import gdal
from PyQt6.QtWidgets import QInputDialog, QWidget

from lib import HsImage, LabelType, ScalarType
from loaders.abstract import AbstractFileLoader
from utils import staticproperty

gdal.UseExceptions()


class ENVILoader(AbstractFileLoader):
    @staticproperty
    def FILE_FILTER_NAME() -> str:
        return "ENVI .hdr labelled raster"

    @staticproperty
    def EXTENSIONS() -> list[str]:
        return ["hdr"]

    @staticmethod
    def load_file(path: str, parent: QWidget) -> Optional[HsImage]:
        path_no_ext, _ = os.path.splitext(path)
        dataset: gdal.Dataset = gdal.Open(path_no_ext)
        # set pixel interleaving, so that bands will be the third dimension
        data: npt.NDArray = dataset.ReadAsArray(interleave="pixel")
        labels = None
        labels_type = LabelType.AUTO
        if "ENVI" in dataset.GetMetadataDomainList():
            metadata: dict[str, str] = dataset.GetMetadata("ENVI")
            if "_wavelength" in metadata:
                labels = [
                    x.strip(whitespace + "{}")
                    for x in metadata["_wavelength"].split(",")
                ]
                try:
                    [float(x) for x in labels]
                    labels_type = LabelType.WAVELENGTH
                except ValueError:
                    labels_type = LabelType.CUSTOM_STR

        max_bpp = data.itemsize * 8
        bpp = ENVILoader.get_bpp(data, max_bpp, parent)
        if bpp is None:
            return
        image = HsImage(data, bpp, labels, labels_type)
        return image

    @staticmethod
    def get_bpp(
        data: npt.NDArray[ScalarType], max: int, parent: QWidget
    ) -> Optional[int]:
        max_val: ScalarType = np.max(data)
        min_bpp = ceil(log2(max_val))

        bpp, ok = QInputDialog.getInt(
            parent,
            "ENVI file loader",
            "Bits per pixel:",
            min=min_bpp,
            max=max,
        )

        if not ok:
            return
        return bpp
