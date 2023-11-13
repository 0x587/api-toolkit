from typing import Generic, Type, Sequence, Any, Callable, Union, Generator, Optional

from fastapi import APIRouter, HTTPException, Depends

from api_toolkit.orm import DB_MODEL, BaseORM, DataBaseProtocol
from api_toolkit.router._types import DEPENDENCIES
from api_toolkit.view import ORM_MODEL
import api_toolkit.router._utils as utils

NOT_FOUND = HTTPException(404, "Item not found")


class CRUDBase(Generic[ORM_MODEL], APIRouter):
    schema: Type[ORM_MODEL]
    create_schema: Type[ORM_MODEL]
    update_schema: Type[ORM_MODEL]

    def __init__(
            self,
            db_func: Callable[..., Generator[DataBaseProtocol, Any, None]],
            model: Type[DB_MODEL],
            schema: Type[ORM_MODEL],
            create_schema: Optional[Type[ORM_MODEL]] = None,
            update_schema: Optional[Type[ORM_MODEL]] = None,
            get_all_route: Union[bool, DEPENDENCIES] = True,
            get_one_route: Union[bool, DEPENDENCIES] = True,
            create_one_route: Union[bool, DEPENDENCIES] = True,
            create_some_route: Union[bool, DEPENDENCIES] = True,
            update_route: Union[bool, DEPENDENCIES] = True,
            delete_one_route: Union[bool, DEPENDENCIES] = True,
            delete_all_route: Union[bool, DEPENDENCIES] = True,
    ):
        super().__init__()
        self.db_func = db_func
        self.model = model
        self.schema = schema
        self.create_schema = create_schema or schema
        self.update_schema = update_schema or schema
        self.orm = BaseORM(Depends(db_func), model)
        assert len(schema.__table__.primary_key.columns) == 1, (
            'CRUD operations are only supported for models with a single primary key.'
        )
        self._pk: str = schema.__table__.primary_key.columns.keys()[0]
        self._pk_type: type = utils.get_pk_type(schema, self._pk)

        if get_all_route:
            self.add_api_route(
                '/get_all',
                self._get_all(),
                methods=['POST'],
                dependencies=get_all_route if isinstance(get_all_route, Sequence) else None,
            )
        if get_one_route:
            self.add_api_route(
                '/get_one',
                self._get_one(),
                methods=['POST'],
                dependencies=get_one_route if isinstance(get_one_route, Sequence) else None,
            )
        if create_some_route:
            self.add_api_route(
                '/create_some',
                self._create_some(),
                methods=['POST'],
                dependencies=create_some_route if isinstance(create_some_route, Sequence) else None,
            )
        if create_one_route:
            self.add_api_route(
                '/create_one',
                self._create_one(),
                methods=['POST'],
                dependencies=create_one_route if isinstance(create_one_route, Sequence) else None,
            )
        if update_route:
            self.add_api_route(
                '/update',
                self._update(),
                methods=['POST'],
                dependencies=update_route if isinstance(update_route, Sequence) else None,
            )
        if delete_one_route:
            self.add_api_route(
                '/delete_one',
                self._delete_one(),
                methods=['POST'],
                dependencies=delete_one_route if isinstance(delete_one_route, Sequence) else None,
            )
        if delete_all_route:
            self.add_api_route(
                '/delete_all',
                self._delete_all(),
                methods=['POST'],
                dependencies=delete_all_route if isinstance(delete_all_route, Sequence) else None,
            )

    def _get_all(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        def route(db: DataBaseProtocol = Depends(self.db_func)):
            return db.scalars(self.orm.get_all_query()).all()

        return route

    def _get_one(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        def route(ident: self._pk_type,  # type: ignore
                  db: DataBaseProtocol = Depends(self.db_func)):
            return db.scalar(self.orm.get_one_query(ident))

        return route

    def _create_one(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        def route(data: self.create_schema):  # type: ignore
            return self.orm.create(data)

        return route

    def _create_some(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        def route(data: self.create_schema):  # type: ignore
            return self.orm.create_some(data)

        return route

    def _update(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        def route(ident: self._pk_type,  # type: ignore
                  model: self.update_schema,  # type: ignore
                  ):
            return self.orm.update(ident, **model.dict())

        return route

    def _delete_one(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        def route(ident: self._pk_type):  # type: ignore
            return self.orm.delete_one(ident)

        return route

    def _delete_all(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        def route():
            return self.orm.delete_all()

        return route
