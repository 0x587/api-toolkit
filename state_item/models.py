from datetime import datetime
from enum import IntEnum
from abc import ABCMeta

from sqlmodel import SQLModel, Field

StateBase = IntEnum


class StateItemBase(SQLModel, metaclass=ABCMeta):
    state: StateBase
    created_time: datetime = Field(default_factory=datetime.now)
    updated_time: datetime = Field(default_factory=datetime.now)
