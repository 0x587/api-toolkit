from typing import TypeVar
from api_toolkit.orm import BaseORM

ORM_MODEL = TypeVar('ORM_MODEL', bound=BaseORM)
