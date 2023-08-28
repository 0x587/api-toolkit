from typing import Any, Callable, List, Type, Generator, Optional, Union

from fastapi import Depends, HTTPException

from .base import CRUDGenerator, NOT_FOUND
from . import utils
from .types import DEPENDENCIES, PAGINATION, PYDANTIC_SCHEMA as SCHEMA

try:
    from sqlmodel import SQLModel, Session, select
except ImportError:
    SQLModel = None
    Session = None
    sqlmodel_installed = False
else:
    sqlmodel_installed = True

CALLABLE = Callable[..., SQLModel]
CALLABLE_LIST = Callable[..., List[SQLModel]]

SESSION_FUNC = Callable[..., Session]


class SQLModelCRUDRouter(CRUDGenerator[SCHEMA]):
    db_model: Type[SQLModel]

    def __init__(
            self,
            db_func: SESSION_FUNC,
            db_model: Type[SQLModel],
            create_schema: Optional[Type[SCHEMA]] = None,
            update_schema: Optional[Type[SCHEMA]] = None,
            prefix: Optional[str] = None,
            tags: Optional[List[str]] = None,
            paginate: Optional[int] = None,
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
        super().__init__(
            schema=db_model,
            create_schema=create_schema,
            update_schema=update_schema,
            prefix=prefix or db_model.__tablename__,
            tags=tags,
            paginate=paginate,
            get_all_route=get_all_route,
            get_one_route=get_one_route,
            create_route=create_route,
            update_route=update_route,
            delete_one_route=delete_one_route,
            delete_all_route=delete_all_route,
            **kwargs
        )

    def _get_all(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        def route(db: Session = Depends(self.db_func)) -> List[SQLModel]:
            return db.exec(
                select(self.db_model)
            ).all()

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
        def route(db: Session = Depends(self.db_func)) -> List[SQLModel]:
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
