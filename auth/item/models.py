import uuid

from pydantic import UUID4
from sqlmodel import SQLModel, Field, Relationship


class AuthItemBase(SQLModel):
    id: UUID4 = Field(primary_key=True, default_factory=uuid.uuid4)
    own_group_id: UUID4 = Field(foreign_key="group.id", index=True)
    own_group: "GroupDB" = Relationship()  # type: ignore
