from typing import Any, Callable, Type, Optional, List, Union

from fastapi import APIRouter, Depends
from sqlmodel import Session, select, SQLModel

from crud import SQLModelCRUDRouter, CRUDGenerator
from crud.crud import CALLABLE_LIST, SESSION_FUNC
from crud.types import DEPENDENCIES, PYDANTIC_SCHEMA as SCHEMA

from .base import StateItemCRUDGenerator


class StateItemCRUDRouter(StateItemCRUDGenerator):

    def _get_all_in_state(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        def route(state: self.registrar.state_type,  # type: ignore
                  db: Session = Depends(self.db_func)):
            return db.exec(
                select(self.db_model).
                where(self.db_model.state == state)
            ).all()

        return route

    def _create_in_state(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        def route(state: self.registrar.state_type,  # type: ignore
                  db: Session = Depends(self.db_func)):
            raise NotImplementedError

        return route

    def _delete_all_in_state(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        def route(state: self.registrar.state_type,  # type: ignore
                  db: Session = Depends(self.db_func)) -> List[SQLModel]:
            for item in db.exec(select(self.db_model)).all():
                db.delete(item)
            db.commit()
            return self._get_all_in_state()(state=state, db=db)

        return route
