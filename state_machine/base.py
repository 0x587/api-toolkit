from abc import ABC, abstractmethod
from typing import List, Type, Optional, Union, Any, Callable

from sqlmodel import SQLModel

from crud import CRUDGenerator, SQLModelCRUDRouter
from crud.crud import SESSION_FUNC
from .types import T, DEPENDENCIES
from .utils import StatusRegistrar
from .models import StateItemBase


class StateItemCRUDGenerator(SQLModelCRUDRouter, ABC):
    registrar: StatusRegistrar
    db_model: Type[StateItemBase]

    def __init__(
            self,
            registrar: StatusRegistrar,
            db_func: SESSION_FUNC,
            db_model: Type[SQLModel],
            create_schema: Optional[Type[T]] = None,
            update_schema: Optional[Type[T]] = None,
            prefix: Optional[str] = None,
            tags: Optional[List[str]] = None,
            paginate: Optional[int] = None,
            get_all_route: Union[bool, DEPENDENCIES] = True,
            get_all_in_state_route: Union[bool, DEPENDENCIES] = True,
            get_one_route: Union[bool, DEPENDENCIES] = True,
            create_route: Union[bool, DEPENDENCIES] = True,
            create_in_state_route: Union[bool, DEPENDENCIES] = True,
            update_route: Union[bool, DEPENDENCIES] = True,
            delete_one_route: Union[bool, DEPENDENCIES] = True,
            delete_all_route: Union[bool, DEPENDENCIES] = True,
            delete_all_in_state_route: Union[bool, DEPENDENCIES] = True,
            **kwargs: Any,
    ) -> None:
        super().__init__(
            db_func, db_model, create_schema, update_schema, prefix, tags, paginate,
            get_all_route, get_one_route, create_route, update_route,
            delete_one_route, delete_all_route, **kwargs,
        )
        self.registrar = registrar
        if get_all_in_state_route:
            self._add_api_route(
                "/",
                self._get_all_in_state(),
                methods=["GET"],
                response_model=Optional[List[self.schema]],  # type: ignore
                summary="Get all items in state",
                dependencies=get_all_in_state_route,
            )
        if create_in_state_route:
            self._add_api_route(
                "/",
                self._create_in_state(),
                methods=["POST"],
                response_model=self.schema,  # type: ignore
                summary="Create item in state",
                dependencies=create_in_state_route,
            )
        if delete_all_in_state_route:
            self._add_api_route(
                "/",
                self._delete_all_in_state(),
                methods=["DELETE"],
                response_model=Optional[List[self.schema]],  # type: ignore
                summary="Delete all items in state",
                dependencies=delete_all_in_state_route,
            )

    @abstractmethod
    def _get_all_in_state(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _create_in_state(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _delete_all_in_state(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError
