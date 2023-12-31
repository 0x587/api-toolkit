from enum import Enum
from typing import Any, Callable, List, Type, Optional, Union, Generator

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate
from fastapi import Depends
from sqlalchemy import text

from .base import CRUDGenerator, NOT_FOUND
from . import utils
from .types import DEPENDENCIES, PYDANTIC_SCHEMA as SCHEMA

try:
    from sqlmodel import SQLModel, Session, select
except ImportError:
    SQLModel = None
    Session = None
    select = None
    sqlmodel_installed = False
else:
    sqlmodel_installed = True

CALLABLE = Callable[..., SQLModel]
CALLABLE_LIST = Callable[..., Page[SQLModel]]

SESSION_FUNC = Callable[..., Generator[Session, Any, None]]


class SQLModelCRUDRouter(CRUDGenerator[SCHEMA]):
    db_model: Type[SQLModel]

    def __init__(
            self,
            db_func: SESSION_FUNC,
            db_model: Type[SQLModel],
            filter_fields: Optional[List[str]] = None,
            order_fields: Optional[List[str]] = None,
            create_schema: Optional[Type[SCHEMA]] = None,
            update_schema: Optional[Type[SCHEMA]] = None,
            prefix: Optional[str] = None,
            tags: Optional[List[str]] = None,
            get_all_route: Union[bool, DEPENDENCIES] = True,
            get_one_route: Union[bool, DEPENDENCIES] = True,
            create_route: Union[bool, DEPENDENCIES] = True,
            update_route: Union[bool, DEPENDENCIES] = True,
            delete_one_route: Union[bool, DEPENDENCIES] = True,
            delete_all_route: Union[bool, DEPENDENCIES] = True,
            **kwargs: Any
    ):
        assert sqlmodel_installed, "package sqlmodel must be installed."
        self.db_func = db_func
        self.db_model = db_model
        self._pk: str = db_model.__table__.primary_key.columns.keys()[0]
        self._pk_type: type = utils.get_pk_type(db_model, self._pk)
        self.pure_fields: List[str] = [field_name for field_name, field_type in self.db_model.__annotations__.items() if
                                       not hasattr(field_type, 'Config')]
        self.filter_fields = filter_fields or []
        self.order_fields = order_fields or []
        super().__init__(
            schema=db_model,
            create_schema=create_schema,
            update_schema=update_schema,
            prefix=prefix or db_model.__tablename__,
            tags=tags,
            get_all_route=get_all_route,
            get_one_route=get_one_route,
            create_route=create_route,
            update_route=update_route,
            delete_one_route=delete_one_route,
            delete_all_route=delete_all_route,
            **kwargs
        )

    def _order_by_depend(self):
        fields_enum = Enum(f'{self.db_model.__name__}OrderFields',
                           {field_name: field_name for field_name in self.pure_fields
                            if field_name in self.order_fields})

        order_dir_enum = Enum(f'{self.db_model.__name__}OrderDir', {'asc': 'asc', 'desc': 'desc'})

        def route(order_by: Optional[fields_enum] = None,
                  order_dir: Optional[order_dir_enum] = order_dir_enum('asc')):
            if not order_by:
                return None
            if order_by not in fields_enum:
                raise ValueError(f"order_by value is not a valid field name: {order_by.value}")
            if order_dir.value not in ['asc', 'desc']:
                raise ValueError(f"order_dir value must be 'asc' or 'desc': {order_dir.value}")
            return order_by, order_dir

        return route

    def _filter_depend(self):
        fields_enum = Enum(f'{self.db_model.__name__}FilterFields',
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

    def _get_all(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        def route(db: Session = Depends(self.db_func),
                  order=Depends(self._order_by_depend()),
                  filter_=Depends(self._filter_depend())) -> Page[SQLModel]:
            query = select(self.db_model)
            if order:
                order_key, order_dir = order
                query = query.order_by(text(f'{order_key.value} {order_dir.value}'))
            if filter_:
                filter_key, filter_value = filter_
                query = query.where(text(f'{filter_key.value} = :filter_value')).params(filter_value=filter_value)
            return paginate(db, query)

        return route

    def _get_one(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def route(
                item_id: self._pk_type, db: Session = Depends(self.db_func)  # type: ignore
        ) -> SQLModel:
            model: SQLModel = db.get(self.db_model, item_id)

            if model:
                return model
            else:
                raise NOT_FOUND from None

        return route

    def _create(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def route(
                model: self.create_schema,  # type: ignore
                db: Session = Depends(self.db_func),
        ) -> SQLModel:
            db_model: SQLModel = self.db_model(**model.dict())
            db.add(db_model)
            db.commit()
            db.refresh(db_model)
            return db_model

        return route

    def _update(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def route(
                item_id: self._pk_type,  # type: ignore
                model: self.update_schema,  # type: ignore
                db: Session = Depends(self.db_func),
        ) -> SQLModel:
            db_model: SQLModel = self._get_one()(item_id, db)

            for key, value in model.dict(exclude={self._pk}).items():
                if hasattr(db_model, key):
                    setattr(db_model, key, value)

            db.commit()
            db.refresh(db_model)

            return db_model

        return route

    def _delete_all(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        def route(db: Session = Depends(self.db_func)) -> Page[SQLModel]:
            for item in db.exec(select(self.db_model)).all():
                db.delete(item)
            db.commit()
            return self._get_all()(db=db)

        return route

    def _delete_one(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def route(
                item_id: self._pk_type, db: Session = Depends(self.db_func)  # type: ignore
        ) -> SQLModel:
            db_model: SQLModel = self._get_one()(item_id, db)
            db.delete(db_model)
            db.commit()

            return db_model

        return route
