from abc import ABC, abstractmethod
from typing import Optional

from PyQt6.QtWidgets import QWidget

from lib import HsImage
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
