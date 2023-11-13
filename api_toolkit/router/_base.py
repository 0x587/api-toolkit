from abc import abstractmethod, ABC
from typing import Generic, Type, Sequence, Any, Callable, Union

from fastapi import APIRouter

from api_toolkit.router._types import DEPENDENCIES
from api_toolkit.view import ORM_MODEL


class CRUDBase(Generic[ORM_MODEL], APIRouter, ABC):
    schema: Type[ORM_MODEL]
    create_schema: Type[ORM_MODEL]
    update_schema: Type[ORM_MODEL]

    def __init__(
            self,
            get_all_route: Union[bool, DEPENDENCIES] = True,
            get_one_route: Union[bool, DEPENDENCIES] = True,
            create_one_route: Union[bool, DEPENDENCIES] = True,
            create_some_route: Union[bool, DEPENDENCIES] = True,
            update_route: Union[bool, DEPENDENCIES] = True,
            delete_one_route: Union[bool, DEPENDENCIES] = True,
            delete_all_route: Union[bool, DEPENDENCIES] = True,
    ):
        super().__init__()
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

    @abstractmethod
    def _get_all(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _get_one(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _create_one(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _create_some(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _update(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _delete_one(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _delete_all(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError
