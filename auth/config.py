import uuid
from typing import Optional

from fastapi_users import schemas
from fastapi_users_db_sqlmodel import SQLModelBaseUserDB


class AuthConfig:
    class User(schemas.BaseUser):
        first_name: Optional[str]
        last_name: Optional[str]

    class UserRead(User):
        pass

    class UserCreate(schemas.BaseUserCreate, User):
        pass

    class UserUpdate(schemas.BaseUserUpdate, User):
        pass

    class UserDB(SQLModelBaseUserDB, User, table=True):
        pass
