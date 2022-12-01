import os
import traceback
from typing import Optional, Type

from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget

from lib import HsImage
from loaders.abstract import AbstractFileLoader
from loaders.envi import ENVILoader
from loaders.matlab import MatlabLoader


class Loader:
    loaders: list[Type[AbstractFileLoader]] = [ENVILoader, MatlabLoader]

    def __init__(self, parent: QWidget) -> None:
        self.parent = parent
        self.extensions_map: dict[str, Type[AbstractFileLoader]] = {}
        for loader in self.loaders:
            for extension in loader.EXTENSIONS:
                if extension in self.extensions_map:
                    raise Exception(
                        f"Extension {extension} claimed by {loader} has been already registered by {self.extensions_map[extension].__name__}."
                    )
                self.extensions_map[extension] = loader

    def load_file(self, path: str) -> Optional[HsImage]:
        # extension starts with a "."
        _, extension = os.path.splitext(path)
        file_loader = self.extensions_map[extension[1:]]
        return file_loader.load_file(path, self.parent)

    def filters(self) -> list[str]:
        # prefix extensions with "*." and append them after the filter name
        return [
            f"{loader.FILE_FILTER_NAME} ({' '.join(['*.' + ext for ext in loader.EXTENSIONS])})"
            for loader in self.loaders
        ]

    def open_file(self) -> Optional[HsImage]:
        """Show an "Open file" dialog and load the selected file. Returns `None` on failure or when cancelled, `HsImage` otherwise."""
        file_filter = ";;".join(self.filters())
        file_path, used_filter = QFileDialog.getOpenFileName(
            self.parent, "Open image", "", file_filter
        )

        if not file_path:
            # User pressed Cancel
            return

        try:
            return self.load_file(file_path)
        except Exception as err:
            message_box = QMessageBox(self.parent)
            message_box.setIcon(QMessageBox.Icon.Warning)
            # Append the error message to text instead of using informative text to force width scaling
            message_box.setText("Loading file failed\n\n" + str(err))
            message_box.setDetailedText(traceback.format_exc())
            message_box.exec()

        return
