from fastapi import Depends
from pydantic import BaseModel
from typing import TypeVar, Optional, Sequence

PYDANTIC_MODEL = TypeVar('PYDANTIC_MODEL', bound=BaseModel)
DEPENDENCIES = Optional[Sequence[Depends]]
