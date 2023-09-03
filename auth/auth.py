from typing import List, Coroutine, Any, Callable

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_users import FastAPIUsers
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from api_toolkit.auth.config import AuthConfigBase
from api_toolkit.auth.models import UP, GP

NOT_ANY_GROUP = HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                              detail="You are not in any group.")


class Auth:
    _router: APIRouter
    _fastapi_users: FastAPIUsers

    def __init__(self, config: AuthConfigBase, _router: APIRouter, _fastapi_users: FastAPIUsers, get_async_session):
        self._config = config
        self._get_async_session = get_async_session
        self._router = _router
        self._fastapi_users = _fastapi_users
        self.current_user = self._fastapi_users.current_user()
        self.current_active_user = self._fastapi_users.current_user(active=True)
        self.current_verified_user = self._fastapi_users.current_user(active=True, verified=True)
        self.current_superuser = self._fastapi_users.current_user(active=True, superuser=True)
        self.current_group = self._current_group()
        self.own_groups = self._own_groups()

    def _current_group(self) -> Callable[[UP, AsyncSession], Coroutine[Any, Any, GP]]:
        async def _current_group(user: UP = Depends(self.current_user),
                                 db: AsyncSession = Depends(self._get_async_session)) -> GP:
            group = await db.get(self._config.GroupDB, user.group_id)
            if not group:
                raise NOT_ANY_GROUP
            return group

        return _current_group

    def _own_groups(self) -> Callable[[GP, AsyncSession], Coroutine[Any, Any, List[GP]]]:
        async def _own_groups(g: GP = Depends(self.current_group),
                              db: AsyncSession = Depends(self._get_async_session)) -> List[GP]:
            async def get_children(group: GP, groups: List[GP]):
                for child in (await db.execute(select(self._config.GroupDB).where(
                        self._config.GroupDB.parent_id == group.id))).all():
                    groups.append(*child)
                    for cg in child:
                        await get_children(cg, groups)

            gs = [g]
            await get_children(g, gs)
            return gs

        return _own_groups

    @property
    def router(self):
        return self._router
