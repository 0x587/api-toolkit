from abc import ABC, abstractmethod
from typing import List, Type, Optional, Union, Any, Callable

from fastapi import HTTPException, Response
from graphviz import Digraph
from sqlmodel import SQLModel

from api_toolkit.crud import SQLModelCRUDRouter
from api_toolkit.crud.crud import SESSION_FUNC
from .types import T, DEPENDENCIES
from .utils import StatusRegistrar
from .models import StateItemBase

BAD_REQUEST = HTTPException(400, "Bad Request")


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
            get_all_route: Union[bool, DEPENDENCIES] = True,
            get_all_in_state_route: Union[bool, DEPENDENCIES] = True,
            get_one_route: Union[bool, DEPENDENCIES] = True,
            create_route: Union[bool, DEPENDENCIES] = True,
            # unimplemented
            create_in_state_route: Union[bool, DEPENDENCIES] = False,
            update_route: Union[bool, DEPENDENCIES] = True,
            delete_one_route: Union[bool, DEPENDENCIES] = True,
            delete_all_route: Union[bool, DEPENDENCIES] = True,
            delete_all_in_state_route: Union[bool, DEPENDENCIES] = True,
            **kwargs: Any,
    ) -> None:
        super().__init__(
            db_func, db_model, create_schema, update_schema, prefix, tags,
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
                summary="Get all items in this state",
                dependencies=get_all_in_state_route,
            )
        if create_in_state_route:
            self._add_api_route(
                "/",
                self._create_in_state(),
                methods=["POST"],
                response_model=self.schema,  # type: ignore
                summary="Create item in this state",
                dependencies=create_in_state_route,
            )
        if delete_all_in_state_route:
            self._add_api_route(
                "/",
                self._delete_all_in_state(),
                methods=["DELETE"],
                response_model=Optional[List[self.schema]],  # type: ignore
                summary="Delete all items in this state",
                dependencies=delete_all_in_state_route,
            )
        if self.registrar:
            for (from_state, to_state), trans_info in self.registrar.transitions().items():
                self._add_api_route(
                    f"/transition/{from_state.name}-to-{to_state.name}",
                    trans_info.func,
                    methods=["POST"],
                    summary=f"Transition this item from state {from_state.name} to state {to_state.name}",
                    response_model=self.registrar.response_model(),
                    error_responses=[BAD_REQUEST],
                    dependencies=trans_info.dependencies
                )
            self._add_api_route(
                f"/flow/chart",
                self._generate_flowchart,
                methods=["GET"],
                summary=f"Generate flowchart",
                dependencies=[],
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

    def _generate_flowchart(self):
        dot = Digraph(comment=f'{self.prefix} Flowchart')
        dot.attr(rankdir='LR')
        dot.attr(fontname='FangSong')
        for state in self.registrar.state_type.__members__.values():
            dot.node(str(state.value), state.name)
        for (from_state, to_state), v in self.registrar.state_transition_process.items():
            dot.edge(str(from_state.value), str(to_state.value), label=v.name)

        image_data = dot.pipe(format='png')

        response = Response(content=image_data)
        response.headers['Content-Type'] = 'image/png'
        return response
