# @property doesn't work with static methods, but this simple decorator does
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class staticproperty(property, Generic[T]):
    def __init__(
        self,
        fget: Callable[[], T],
        doc: str | None = ...,
    ) -> None:
        super().__init__(fget, doc=doc)

    def __get__(self, cls, owner) -> T:
        return self.fget()
