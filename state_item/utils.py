import datetime
from typing import Generic, Type, TypeVar, Dict, Tuple, Callable, Union, Optional, Sequence, get_type_hints

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

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
    _db_func: Callable[[], Session]

    class Model(BaseModel):
        code: int = 200
        msg: str = 'success'

    def response_model(self):
        return self.Model

    def __init__(self, db_func: Callable[[], Session]):
        self._db_func = db_func

    def bind(self, state_type: Type[StateType], state_item_type: Type[StateItemType]):
        self.state_type = state_type
        self.state_item_type = state_item_type

    def register(self, from_state: StateType, to_state: StateType, dependencies: DEPENDENCIES = True):
        def decorator(func: StateTransFunc):
            hints = get_type_hints(func)
            vars_with_type = ', '.join(
                [f'{var_name}: {var_type.__name__}' for var_name, var_type in get_type_hints(func).items()])
            var_names = ', '.join(hints.keys())

            def wrapper(item_id: int, db: Session, *args, **kwargs):
                runtime_self: StateItemBase = db.get(self.state_item_type, item_id)
                print(runtime_self)
                runtime_obj = self.state_item_type.from_orm(runtime_self)
                if runtime_self.state != from_state:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail=f"Current state is <{runtime_obj.state.name}>, not <{from_state.name}>, "
                                               f"cannot use <{func.__name__}> to transit to <{to_state.name}>")

                runtime_self.state = to_state
                runtime_self.updated_time = datetime.datetime.now()
                func(runtime_self, *args, **kwargs)
                db.commit()

                return {
                    'code': 200,
                    'msg': 'success',
                }

            global_dict = {'wrapper': wrapper, 'db_func': self._db_func, 'Depends': Depends, 'Session': Session}
            code = f"""
def wrapper_reshape(item_id: int{',' if vars_with_type else ''} {vars_with_type}, db: Session = Depends(db_func)):
    return wrapper(item_id, db, {var_names})
            """

            exec(code, global_dict)
            wrapper_reshape: StateTransFunc = global_dict.get('wrapper_reshape')  # type: ignore
            self._state_transition_process[(from_state, to_state)] = (
                StateTransInfo(func=wrapper_reshape, dependencies=dependencies))
            return wrapper

        return decorator

    def transitions(self) -> Dict[StateTransIdentifier, StateTransInfo]:
        return self._state_transition_process.copy()
