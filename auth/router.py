from fastapi import APIRouter, Depends
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend
from pydantic import UUID4
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from .config import AuthConfigBase


class GroupRouter(APIRouter):
    def __init__(self, config: AuthConfigBase, fastapi_users: FastAPIUsers, get_async_session, **kwargs):
        self._get_async_session = get_async_session
        self._config = config
        super().__init__(**kwargs)

        self.add_api_route(
            path="/",
            endpoint=self._get_all(),
            methods=["GET"],
            tags=config.group_tags or ["auth"],
            dependencies=[Depends(fastapi_users.current_user(active=True, superuser=True))],
        )

        self.add_api_route(
            path="/{group_id}",
            endpoint=self._delete(),
            methods=["DELETE"],
            tags=config.group_tags or ["auth"],
            dependencies=[Depends(fastapi_users.current_user(active=True, superuser=True))],
        )

        self.add_api_route(
            path="/register",
            endpoint=self._register(),
            methods=["POST"],
            tags=config.group_tags or ["auth"],
            dependencies=[Depends(fastapi_users.current_user(active=True, superuser=True))],
        )

    def _get_all(self):
        async def get_all(db: AsyncSession = Depends(self._get_async_session)):
            return (await db.exec(select(self._config.GroupDB))).all()

        return get_all

    def _delete(self):
        async def delete(group_id: UUID4,
                         db: AsyncSession = Depends(self._get_async_session)):
            group = await db.get(self._config.GroupDB, group_id)
            await db.delete(group)
            await db.commit()
            return group

        return delete

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
        self._get_async_session = get_async_session
        self._config = config

        self.include_router(
            fastapi_users.get_auth_router(auth_backend),
            prefix="/auth/jwt",
            tags=config.auth_tags or ["auth"],
        )
        self.include_router(
            fastapi_users.get_register_router(config.UserRead, config.UserCreate),
            prefix="/auth",
            tags=config.auth_tags or ["auth"],
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
            tags=config.user_tags or ["auth"],
        )

        self.include_router(
            GroupRouter(config, fastapi_users, get_async_session),
            prefix="/groups",
            tags=config.group_tags or ["auth"],
        )

        self.add_api_route(
            path="/users",
            endpoint=self._get_all(),
            methods=["GET"],
            tags=config.user_tags or ["auth"],
            dependencies=[Depends(fastapi_users.current_user(active=True, superuser=True))],
        )

    def _get_all(self):
        async def get_all(db: AsyncSession = Depends(self._get_async_session)
                          ) -> Page[self._config.User]:  # type: ignore
            query = select(self._config.UserDB).where(self._config.UserDB.is_superuser == False)
            return await paginate(db, query)

        return get_all
