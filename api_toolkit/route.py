"""
route层 用于对接fastapi
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Generic, Type, TypeVar, Callable, Generator, Any, Sequence
from sqlalchemy.orm import Session
from pydantic import BaseModel
from pydantic import __version__ as pydantic_version

from .orm import DB_MODEL, ORM
from .control import Control

DB_FUNC = Callable[..., Generator[Session, Any, None]]
SCHEMA = TypeVar('SCHEMA', bound=BaseModel)
CALLABLE = Callable[..., SCHEMA]
CALLABLE_LIST = Callable[..., Sequence[SCHEMA]]

PYDANTIC_MAJOR_VERSION = int(pydantic_version.split(".", maxsplit=1)[0])

NOT_FOUND = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")


def get_pk_type(schema: Type[SCHEMA], pk_field: str) -> Any:
    if PYDANTIC_MAJOR_VERSION >= 2:
        return schema.model_fields[pk_field].annotation
    else:
        return schema.__fields__[pk_field].type_


class Route(APIRouter, Generic[DB_MODEL]):
    def __init__(self, model: Type[DB_MODEL], schema: Type[SCHEMA], db_func: DB_FUNC):
        super().__init__()
        self.control: Control = Control(ORM(model))
        self.db_func: DB_FUNC = db_func
        self.schema = schema

        assert len(model.__table__.primary_key.columns.keys()) == 1, "Only support single primary key"
        self._pk: str = model.__table__.primary_key.columns.keys()[0]
        self._pk_type: type = get_pk_type(schema, self._pk)

        self.prefix = f'/{model.__tablename__}'

        self.add_api_route(
            path='/get_one',
            endpoint=self._get_one(),
            methods=['POST']
        )

        self.add_api_route(
            path='/get_all',
            endpoint=self._get_all(),
            methods=['POST']
        )

    def _get_one(self) -> CALLABLE:
        def route(ident: self._pk_type,  # type: ignore
                  db=Depends(self.db_func)) \
                -> self.schema:  # type: ignore
            res = self.control.get_one(db, ident)
            if res:
                return self.schema.from_orm(res)
            else:
                raise NOT_FOUND

        return route

    def _get_all(self) -> CALLABLE_LIST:
        def route(db=Depends(self.db_func)) \
                -> Sequence[self.schema]:  # type: ignore
            return self.control.get_all(db)

        return route
