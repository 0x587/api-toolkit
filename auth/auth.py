from fastapi import APIRouter
from fastapi_users import FastAPIUsers


class Auth:
    _router: APIRouter
    _fastapi_users: FastAPIUsers

    def __init__(self, _router: APIRouter, _fastapi_users: FastAPIUsers):
        self._router = _router
        self._fastapi_users = _fastapi_users
        self.current_user = self._fastapi_users.current_user
        self.current_active_user = self._fastapi_users.current_user(active=True)
        self.current_verified_user = self._fastapi_users.current_user(active=True, verified=True)
        self.current_superuser = self._fastapi_users.current_user(active=True, superuser=True)

    @property
    def router(self):
        return self._router
