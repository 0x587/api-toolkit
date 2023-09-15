from typing import Generic, Any, List, Type

from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy.orm import Query

from ._types import DB_MODEL, PK_TYPE, DataBaseProtocol


class BaseORM(Generic[DB_MODEL]):

    def __init__(self, db: DataBaseProtocol, db_model: Type[DB_MODEL]):
        self.db = db
        self.db_model = db_model

    def get_pk_name(self) -> List[str]:
        pk: PrimaryKeyConstraint = self.db_model.metadata.tables[self.db_model.__tablename__].primary_key
        return [column.key for column in pk.columns_autoinc_first]

    def get_all(self) -> Query[DB_MODEL]:
        return self.db.query(self.db_model)

    def get_one(self, ident: PK_TYPE) -> DB_MODEL:
        return self.db.get(self.db_model, ident)

    def create(self, data: DB_MODEL) -> DB_MODEL:
        self.db.add(data)
        self.db.commit()
        self.db.refresh(data)
        return data

    def delete_all(self) -> None:
        self.db.query(self.db_model).delete()
        self.db.commit()

    def delete_one(self, ident: PK_TYPE) -> None:
        self.db.delete(self.get_one(ident))
        self.db.commit()

    def update(self, ident: PK_TYPE, **kwargs: Any) -> DB_MODEL:
        entity = self.get_one(ident)
        for key, value in kwargs.items():
            if key in self.get_pk_name():
                continue
            if hasattr(entity, key):
                setattr(entity, key, value)
        self.db.commit()
        self.db.refresh(entity)
        return entity
