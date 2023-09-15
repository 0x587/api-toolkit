from typing import TypeVar
from sqlalchemy.orm import Session

PK_TYPE = TypeVar("PK_TYPE")
DB_MODEL = TypeVar("DB_MODEL")
DataBaseProtocol = TypeVar("DataBaseProtocol", bound=Session)
