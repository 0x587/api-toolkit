import uuid
from datetime import datetime
from typing import Optional, List, Protocol, TypeVar

from fastapi_users import schemas
from fastapi_users.models import UserProtocol as BaseUserProtocol

from fastapi_users_db_sqlmodel import SQLModelBaseUserDB
from pydantic import UUID4
from sqlalchemy.orm import backref
from sqlmodel import SQLModel, Field, Relationship


class UserProtocol(BaseUserProtocol):
    group_id: Optional[UUID4]
    group: Optional["GP"]


class GroupProtocol(Protocol):
    id: UUID4
    name: str
    is_active: bool = True

    users: List["UP"]
    parent_id: Optional[UUID4]
    children: List["GP"]


UP = TypeVar("UP", bound=UserProtocol)
GP = TypeVar("GP", bound=GroupProtocol)


# <editor-fold desc="User Model">

class BaseUser(schemas.BaseUser):
    created_at: datetime


BaseUserCreate = schemas.BaseUserCreate
BaseUserUpdate = schemas.BaseUserUpdate


# BaseUserDB = SQLModelBaseUserDB
class BaseUserDB(SQLModelBaseUserDB):
    group_id: Optional[UUID4] = Field(default=None, foreign_key="group.id")
    group: Optional["GroupDB"] = Relationship(back_populates="users")  # type: ignore

    created_at: datetime = Field(default_factory=datetime.now, nullable=True)


# </editor-fold>

# <editor-fold desc="Group Model">
class BaseGroup(SQLModel):
    id: UUID4
    name: str
    is_active: bool = True
    parent_id: UUID4
    created_at: datetime


class BaseGroupCreate(SQLModel):
    name: str
    is_active: Optional[bool] = True
    parent_id: Optional[UUID4]


class BaseGroupUpdate(BaseGroup):
    name: Optional[str]
    is_active: Optional[bool] = True
    parent_id: Optional[UUID4]


class BaseGroupDB(SQLModel):
    __tablename__ = "group"

    id: UUID4 = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    name: Optional[str] = Field(default=None, nullable=True)
    is_active: bool = Field(True, nullable=False)

    users: List["UserDB"] = Relationship(back_populates="group")  # type: ignore

    parent_id: Optional[UUID4] = Field(default=None, foreign_key="group.id")
    children: List["GroupDB"] = Relationship(  # type: ignore
        sa_relationship_kwargs=dict(
            cascade="all",
            backref=backref("parent", remote_side="GroupDB.id"),
        )
    )

    created_at: datetime = Field(default_factory=datetime.now, nullable=True)

    class Config:
        orm_mode = True

# </editor-fold>
