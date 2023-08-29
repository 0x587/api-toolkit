import datetime
from typing import Generic, Type, TypeVar, Dict, Tuple, Callable, Union, Optional, Sequence

from fastapi import Depends
from pydantic import BaseModel

from .models import StateBase, StateItemBase

StateType = TypeVar('StateType', bound=StateBase)
StateItemType = TypeVar('StateItemType', bound=StateItemBase)

StateTransFunc = Callable[[StateItemType, ...], None]
StateTransIdentifier = Tuple[StateType, StateType]
DEPENDENCIES = Optional[Sequence[Depends]]


class StateTransInfo:
    func: StateTransFunc
    dependencies: Union[bool, DEPENDENCIES]

    def __init__(self, func: StateTransFunc, dependencies: Union[bool, DEPENDENCIES]):
        self.func = func
        self.dependencies = dependencies


class StatusRegistrar(Generic[StateType, StateItemType]):
    state_type = Type[StateType]
    state_item_type: Type[StateItemType]
    _state_transition_process: Dict[StateTransIdentifier, StateTransInfo] = {}

    def __init__(self, state_type: Type[StateType], state_item_type: Type[StateItemType]):
        self.state_type = state_type
        self.state_item_type = state_item_type

    def register(self, from_state: StateType, to_state: StateType, dependencies: DEPENDENCIES = True):
        def decorator(func: StateTransFunc):
            a = func.__code__
            print(func.__code__.co_varnames)

            def wrapper(*args, **kwargs):
                runtime_self: StateItemBase = args[0]
                if runtime_self.state != from_state:
                    raise ValueError(f"Current state is \"{runtime_self.state.name}\", not \"{from_state.name}\", "
                                     f"cannot use \"{func.__name__}\" to transit to \"{to_state.name}\"")
                runtime_self.state = to_state
                runtime_self.updated_time = datetime.datetime.now()
                return func(*args, **kwargs)

            self._state_transition_process[(from_state, to_state)] = (
                StateTransInfo(func=func, dependencies=dependencies))
            return wrapper

        return decorator

    def transitions(self) -> Dict[StateTransIdentifier, StateTransInfo]:
        return self._state_transition_process.copy()
