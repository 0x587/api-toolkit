from pydantic import BaseModel, UUID4

from models import Sex


class Ratee(BaseModel):
    id: UUID4
    name: str
    sex: Sex


class Project(BaseModel):
    id: UUID4
    name: str


class RateRecord(BaseModel):
    ratee_id: UUID4
    project_id: UUID4
    value: float


class RateRecordDetail(BaseModel):
    ratee_name: str
    project_name: str
    value: float
