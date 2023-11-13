from typing import Generic, Type, Sequence

from api_toolkit.orm import DataBaseProtocol, DB_MODEL
from api_toolkit.view._types import ORM_MODEL


class BaseView(Generic[ORM_MODEL]):

    def __init__(self, db: DataBaseProtocol, orm_model: Type[ORM_MODEL]):
        self.db = db
        self.orm_model = orm_model

    def get_all(self) -> Sequence[DB_MODEL]:
        return self.db.scalars(self.orm_model.get_all_query()).all()

    def get_one(self, ident) -> DB_MODEL:
        return self.db.scalar(self.orm_model.get_one_query(ident))

    def create(self, data: DB_MODEL) -> DB_MODEL:
        return self.orm_model.create(data)

    def create_some(self, data: Sequence[DB_MODEL]) -> Sequence[DB_MODEL]:
        return self.orm_model.create_some(data)

    def delete_all(self) -> None:
        return self.orm_model.delete_all()

    def delete_one(self, ident) -> None:
        return self.orm_model.delete_one(ident)
