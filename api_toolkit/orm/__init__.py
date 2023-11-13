from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from ._base import BaseORM
from ._types import DB_MODEL, DataBaseProtocol


class Base(DeclarativeBase):
    pass


__all__ = [
    "Base",
    "Mapped",
    "mapped_column",
    "DataBaseProtocol",
    "BaseORM",
    "DB_MODEL",
]
