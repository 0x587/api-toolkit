from fastapi import HTTPException, status, Depends
from typing import Any, Callable, List, Type, Optional, Union, Generator

from pydantic import UUID4

from api_toolkit.crud import SQLModelCRUDRouter
from api_toolkit.crud.types import DEPENDENCIES, PYDANTIC_SCHEMA as SCHEMA
from .models import AuthItemBase
from .. import Auth
from ..models import GP

try:
    from sqlmodel import SQLModel, Session, select, col
except ImportError:
    SQLModel = None
    Session = None
    select = None
    col = None
    sqlmodel_installed = False
else:
    sqlmodel_installed = True

assert sqlmodel_installed, "package sqlmodel must be installed."

NO_AUTH_OF_THIS_GROUP = HTTPException(status.HTTP_403_FORBIDDEN,
                                      "You don't have permission to access resources of this group.")

NO_THIS_GROUP = HTTPException(status.HTTP_404_NOT_FOUND,
                              "No such group.")

CALLABLE = Callable[..., SQLModel]
CALLABLE_LIST = Callable[..., List[SQLModel]]
SESSION_FUNC = Callable[..., Generator[Session, Any, None]]


class AuthCRUDRouter(SQLModelCRUDRouter):
    db_model: Type[AuthItemBase]

    def __init__(
            self,
            auth: Auth,
            db_func: SESSION_FUNC,
            db_model: Type[AuthItemBase],
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
            change_owner_route: Union[bool, DEPENDENCIES] = True,
            **kwargs: Any
    ):
        self.auth = auth
        self.db_func = db_func
        self.db_model = db_model
        super().__init__(
            db_func=db_func,
            db_model=db_model,
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
        self._add_api_route(
            path=f"/{{item_id}}/change_owner",
            endpoint=self._change_owner(),
            methods=["POST"],
            response_model=Optional[self.db_model],  # type: ignore
            summary="Change Owner",
            dependencies=change_owner_route,
        )

    def _require_own_groups(self):
        def route(group_id: Optional[UUID4] = None,
                  own_groups: List[GP] = Depends(self.auth.own_groups)) -> List[GP]:
            if not group_id:
                return own_groups

            for group in own_groups:
                if group.id == group_id:
                    return [group]
            raise NO_AUTH_OF_THIS_GROUP

        return route

    def _require_own_group(self):
        def route(group_id: UUID4,
                  own_groups: List[GP] = Depends(self.auth.own_groups)) -> GP:
            for group in own_groups:
                if group.id == group_id:
                    return group
            raise NO_AUTH_OF_THIS_GROUP

        return route

    def _get_all(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        def route(groups: List[GP] = Depends(self._require_own_groups()),
                  db: Session = Depends(self.db_func)) -> List[SQLModel]:
            return db.exec(
                select(self.db_model)
                .where(col(self.db_model.own_group_id).in_([g.id for g in groups]))
            ).all()

        return route

    def _get_one(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def route(item_id: self._pk_type,  # type: ignore
                  groups: List[GP] = Depends(self._require_own_groups()),
                  db: Session = Depends(self.db_func)) -> SQLModel:
            item = db.get(self.db_model, item_id)
            if not item:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
            if item.own_group_id not in [g.id for g in groups]:
                raise NO_AUTH_OF_THIS_GROUP
            return item

        return route

    def _create(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def route(model: self.create_schema,  # type: ignore
                  group: GP = Depends(self._require_own_group()),
                  db: Session = Depends(self.db_func)) -> SQLModel:
            db_model: SQLModel = self.db_model(**model.dict())
            db_model.own_group_id = group.id
            db.add(db_model)
            db.commit()
            db.refresh(db_model)
            return db_model

        return route

    def _update(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def route(item_id: self._pk_type,  # type: ignore
                  model: self.update_schema,  # type: ignore
                  groups: List[GP] = Depends(self._require_own_groups()),
                  db: Session = Depends(self.db_func)) -> SQLModel:
            db_model: SQLModel = self._get_one()(item_id, groups, db)
            for key, value in model.dict(exclude={self._pk}).items():
                if hasattr(db_model, key):
                    setattr(db_model, key, value)
            db.commit()
            db.refresh(db_model)
            return db_model

        return route

    def _delete_all(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        def route(groups: List[GP] = Depends(self._require_own_groups()),
                  db: Session = Depends(self.db_func)) -> List[SQLModel]:
            for item in db.exec(
                    select(self.db_model).where(
                        col(self.db_model.own_group_id).in_([g.id for g in groups]))
            ).all():
                db.delete(item)
            db.commit()
            return self._get_all()(groups, db)

        return route

    def _delete_one(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def route(item_id: self._pk_type,  # type: ignore
                  groups: List[GP] = Depends(self._require_own_groups()),
                  db: Session = Depends(self.db_func)) -> None:
            db_model: SQLModel = self._get_one()(item_id, groups, db)
            db.delete(db_model)
            db.commit()
            return db_model

        return route

    def _change_owner(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def route(item_id: self._pk_type,  # type: ignore
                  target_group: GP = Depends(self._require_own_group()),
                  db: Session = Depends(self.db_func)) -> SQLModel:
            db_model: SQLModel = db.get(self.db_model, item_id)
            db_model.own_group_id = target_group.id
            db.commit()
            db.refresh(db_model)
            return db_model

        return route
