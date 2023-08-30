from fastapi import APIRouter
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend

from .config import AuthConfig


class AuthRouter(APIRouter):
    def __init__(self,
                 fastapi_users: FastAPIUsers,
                 auth_backend: AuthenticationBackend,
                 config: AuthConfig,
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
        self.include_router(
            fastapi_users.get_reset_password_router(),
            prefix="/auth",
            tags=["auth"],
        )
        self.include_router(
            fastapi_users.get_verify_router(config.UserRead),
            prefix="/auth",
            tags=["auth"],
        )
        self.include_router(
            fastapi_users.get_users_router(config.UserRead, config.UserUpdate),
            prefix="/users",
            tags=["users"],
        )
