from abc import ABC, abstractmethod
from typing import Tuple


class Link(ABC):
    @abstractmethod
    def two_sides(self) -> Tuple[str, str]:
        pass


class OneManyLink(Link):
    """
    OneManyLink is a link between one object and many objects.
    Must set in one side.
    """

    def __init__(self, one: str, many: str):
        self.one = one
        self.many = many

    def two_sides(self) -> Tuple[str, str]:
        return self.one, self.many


class ManyManyLink(Link):
    """
    ManyManyLink is a link between many objects and many objects.
    Just could set in one side.
    """

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def two_sides(self) -> Tuple[str, str]:
        return self.left, self.right
