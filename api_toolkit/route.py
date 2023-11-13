"""
route层 用于对接fastapi
"""
import warnings
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Generic, Type, TypeVar, Callable, Generator, Any, Sequence, Optional, List, Dict
from sqlalchemy.orm import Session, class_mapper
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
    register = {}

    def __init__(self,
                 model: Type[DB_MODEL],
                 schema: Type[SCHEMA],
                 db_func: DB_FUNC,
                 filter_fields: Optional[Sequence[str]] = None,
                 ):
        super().__init__()
        if model.__name__ in Route.register:
            raise ValueError(f"Model {model.__name__} already registered")
        Route.register[model.__name__] = self
        self.control: Control = Control(ORM(model))
        self.db_func: DB_FUNC = db_func
        self.schema = schema
        self.model = model

        self.SINGLE_PK = len(model.__table__.primary_key.columns.keys()) == 1
        if not self.SINGLE_PK:
            warnings.warn(f"Model {model.__name__} has multiple primary keys")
        self._pk: str = model.__table__.primary_key.columns.keys()[0]
        self._pk_type: type = get_pk_type(schema, self._pk)

        # TODO:
        # self._pkk: Dict[str, Type] = {
        #     k: get_pk_type(schema, k)
        #     for k, v in model.__table__.primary_key.columns.keys()
        # }

        self.prefix = f'/{model.__tablename__}'
        self.tags = [model.__tablename__.upper()]

        mapper = class_mapper(model)
        self.pure_fields: List[str] = [field_name for field_name, field_type in self.model.__annotations__.items() if
                                       not hasattr(field_type, 'Config')]
        self.fields = {}
        self.filter_fields = filter_fields or self.pure_fields

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

    def _filter_depend(self):
        fields_enum = Enum(f'{self.model.__name__}FilterFields',
                           {field_name: field_name for field_name in self.pure_fields
                            if field_name in self.filter_fields})

        def route(filter_by: Optional[fields_enum] = None,
                  filter_value: Optional[Any] = None):
            if not filter_by:
                return None
            if filter_by not in fields_enum:
                raise ValueError(f"filter_by value is not a valid field name: {filter_by.value}")
            return filter_by, filter_value

        return route

    def _get_all(self) -> CALLABLE_LIST:
        def route(db=Depends(self.db_func),
                  filter_=Depends(self._filter_depend())) \
                -> Sequence[self.schema]:  # type: ignore
            print(filter_)
            return self.control.get_all(db)

        return route
