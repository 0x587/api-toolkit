import uuid
from enum import IntEnum
from pydantic import UUID4
from sqlalchemy import String, Enum, UUID, ForeignKey
from sqlalchemy.orm import relationship, MappedAsDataclass

from api_toolkit.orm import Base, Mapped, mapped_column


class Sex(IntEnum):
    Male = 0
    Female = 1


class RateeDB(MappedAsDataclass, Base):
    __tablename__ = 'ratee'

    id: Mapped[UUID4] = mapped_column(UUID, primary_key=True, default_factory=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), default='')
    sex: Mapped[Sex] = mapped_column(Enum(Sex), default=Sex.Female)

    rate_records: Mapped[list['RateRecordDB']] = relationship(
        'RateRecordDB', back_populates='ratee', default_factory=list)


class ProjectDB(MappedAsDataclass, Base):
    __tablename__ = 'project'

    id: Mapped[UUID4] = mapped_column(UUID, primary_key=True, default_factory=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), default='')

    rate_records: Mapped[list['RateRecordDB']] = relationship(
        'RateRecordDB', back_populates='project', default_factory=list)


class RateRecordDB(MappedAsDataclass, Base):
    __tablename__ = 'rate_record'

    ratee_id: Mapped[UUID4] = mapped_column(ForeignKey(RateeDB.id), primary_key=True, default=None)
    ratee: Mapped[RateeDB] = relationship(
        RateeDB, back_populates='rate_records', default=None)

    project_id: Mapped[UUID4] = mapped_column(ForeignKey(ProjectDB.id), primary_key=True, default=None)
    project: Mapped[ProjectDB] = relationship(
        ProjectDB, back_populates='rate_records', default=None)

    value: Mapped[float] = mapped_column(default=0.0)
