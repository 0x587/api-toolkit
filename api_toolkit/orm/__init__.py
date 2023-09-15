from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from ._base import BaseORM


class Base(DeclarativeBase):
    pass


__all__ = [
    "Base",
    "Mapped",
    "mapped_column",
    "BaseORM"
]
