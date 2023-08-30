import uuid
from typing import Optional, Tuple

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users_db_sqlmodel import SQLModelUserDatabase, SQLModelUserDatabaseAsync
from sqlmodel.ext.asyncio.session import AsyncSession

from .auth import Auth
from .router import AuthRouter

from .config import AuthConfig


def make_auth_backend(secret: str) -> AuthenticationBackend:
    bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

    def get_jwt_strategy() -> JWTStrategy:
        return JWTStrategy(secret=secret, lifetime_seconds=3600)

    auth_backend = AuthenticationBackend(
        name="jwt",
        transport=bearer_transport,
        get_strategy=get_jwt_strategy,
    )
    return auth_backend


class AuthFactory:
    _config: AuthConfig = None

    def __init__(self, config: AuthConfig):
        self._config = config

    def config(self) -> AuthConfig:
        return self._config

    def _make_fastapi_users(self, get_async_session, secret: str) -> Tuple[FastAPIUsers, AuthenticationBackend]:
        self_config = self.config()
        auth_backend = make_auth_backend(secret)

        class UserManager(UUIDIDMixin, BaseUserManager[self_config.User, uuid.UUID]):
            reset_password_token_secret = secret
            verification_token_secret = secret

            async def on_after_register(self, user: self_config.User, request: Optional[Request] = None):
                print(f"User {user.id} has registered.")

            async def on_after_forgot_password(
                    self, user: self_config.User, token: str, request: Optional[Request] = None
            ):
                print(f"User {user.id} has forgot their password. Reset token: {token}")

            async def on_after_request_verify(
                    self, user: self_config.User, token: str, request: Optional[Request] = None
            ):
                print(f"Verification requested for user {user.id}. Verification token: {token}")

        async def get_user_db(session: AsyncSession = Depends(get_async_session)):
            yield SQLModelUserDatabaseAsync(session, self_config.UserDB)

        async def get_user_manager(user_db: SQLModelUserDatabase = Depends(get_user_db)):
            yield UserManager(user_db)

        fastapi_users = FastAPIUsers[self_config.User, uuid.UUID](get_user_manager, [auth_backend])
        return fastapi_users, auth_backend

    def __call__(self, get_async_session, secret: str) -> Auth:
        fastapi_users, auth_backend = self._make_fastapi_users(get_async_session, secret)
        router = AuthRouter(fastapi_users, auth_backend, self.config())
        return Auth(router, fastapi_users)
