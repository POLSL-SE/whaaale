import os
from string import whitespace
from typing import Optional

import numpy.typing as npt
from osgeo import gdal
from PyQt6.QtWidgets import QWidget

from lib import HsImage, LabelType
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

        if data.dtype.kind == "f":
            bpp = None
            normalisation = ENVILoader.get_normalisation(parent)
            if normalisation is None:
                return
        else:
            bpp = ENVILoader.get_bpp(data, parent)
            if bpp is None:
                return
            normalisation = None

        image = HsImage(
            data,
            bpp=bpp,
            normalisation=normalisation,
            labels=labels,
            labels_type=labels_type,
        )
        return image
