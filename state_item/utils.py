import datetime
from typing import Generic, Type, TypeVar, Dict, Tuple, Callable
from .models import StateBase, StateItemBase

StateType = TypeVar('StateType', bound=StateBase)
StateItemType = TypeVar('StateItemType', bound=StateItemBase)

StateTransitionFunc = Callable[[StateItemType, ...], None]


class StatusRegistrar(Generic[StateType, StateItemType]):
    state_type = Type[StateType]
    state_item_type: Type[StateItemType]
    __state_transition_funcs: Dict[Tuple[StateType, StateType], StateTransitionFunc] = {}

    def __init__(self, state_type: Type[StateType], state_item_type: Type[StateItemType]):
        self.state_type = state_type
        self.state_item_type = state_item_type

    def register(self, from_state: StateType, to_state: StateType):
        def decorator(func: StateTransitionFunc):
            def wrapper(*args, **kwargs):
                runtime_self: StateItemBase = args[0]
                if runtime_self.state != from_state:
                    raise ValueError(f"Current state is \"{runtime_self.state.name}\", not \"{from_state.name}\", "
                                     f"cannot use \"{func.__name__}\" to transit to \"{to_state.name}\"")
                runtime_self.state = to_state
                runtime_self.updated_time = datetime.datetime.now()
                return func(*args, **kwargs)

            self.__state_transition_funcs[(from_state, to_state)] = wrapper
            return wrapper

        return decorator
