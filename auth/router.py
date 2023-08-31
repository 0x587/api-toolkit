from fastapi import APIRouter, Depends
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend
from sqlmodel.ext.asyncio.session import AsyncSession

from .config import AuthConfigBase


class GroupRouter(APIRouter):
    def __init__(self, config: AuthConfigBase, get_async_session, **kwargs):
        self._get_async_session = get_async_session
        self._config = config
        super().__init__(**kwargs)

        self.add_api_route(
            path="/register",
            endpoint=self._register(),
            methods=["POST"],
            tags=["auth"],
        )

    def _register(self):
        async def register(group: self._config.GroupCreate,  # noqa
                           db: AsyncSession = Depends(self._get_async_session)):
            group = self._config.GroupDB.from_orm(group)
            db.add(group)
            await db.commit()
            return group

        return register


class AuthRouter(APIRouter):
    def __init__(self,
                 fastapi_users: FastAPIUsers,
                 auth_backend: AuthenticationBackend,
                 config: AuthConfigBase,
                 get_async_session,
                 **kwargs):
        super().__init__(**kwargs)

        self.include_router(
            fastapi_users.get_auth_router(auth_backend),
            prefix="/auth/jwt",
            tags=["auth"],
        )
        self.include_router(
            fastapi_users.get_register_router(config.UserRead, config.UserCreate),
            prefix="/auth",
            tags=["auth"],
        )
        # self.include_router(
        #     fastapi_users.get_reset_password_router(),
        #     prefix="/auth",
        #     tags=["auth"],
        # )
        # self.include_router(
        #     fastapi_users.get_verify_router(config.UserRead),
        #     prefix="/auth",
        #     tags=["auth"],
        # )
        self.include_router(
            fastapi_users.get_users_router(config.UserRead, config.UserUpdate),
            prefix="/users",
            tags=["users"],
        )

        self.include_router(
            GroupRouter(config, get_async_session),
            prefix="/groups",
            tags=["groups"],
        )
