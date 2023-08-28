from datetime import datetime
from enum import IntEnum
from abc import ABCMeta

from sqlmodel import SQLModel

StateBase = IntEnum


class StateItemBase(SQLModel, metaclass=ABCMeta):
    state: StateBase
    created_time: datetime
    updated_time: datetime
