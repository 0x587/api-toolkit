from typing import Type, Protocol, List, Optional

from fastapi_users import schemas
from fastapi_users_db_sqlmodel import SQLModelBaseUserDB
from .models import BaseUser, BaseUserCreate, BaseUserUpdate, BaseGroup, BaseGroupCreate, BaseGroupUpdate, BaseGroupDB


class AuthConfigBase(Protocol):
    auth_tags: Optional[List[str]] = None
    user_tags: Optional[List[str]] = None
    group_tags: Optional[List[str]] = None

    User: Type[schemas.BaseUser] = BaseUser
    UserRead: Type[schemas.BaseUser] = BaseUser
    UserCreate: Type[schemas.BaseUserCreate] = BaseUserCreate
    UserUpdate: Type[schemas.BaseUserUpdate] = BaseUserUpdate
    UserDB: Type[SQLModelBaseUserDB]

    Group: Type[BaseGroup] = BaseGroup
    GroupRead: Type[BaseGroup] = BaseGroup
    GroupCreate: Type[BaseGroupCreate] = BaseGroupCreate
    GroupUpdate: Type[BaseGroupUpdate] = BaseGroupUpdate
    GroupDB: Type[BaseGroupDB]
