from typing import TypeVar, Generic, Protocol
from sqlalchemy.orm import DeclarativeMeta

T = TypeVar("T")
DB_MODEL = TypeVar("DB_MODEL", bound=DeclarativeMeta)
