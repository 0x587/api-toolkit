"""
ORM层 用于生成查询语句
"""
from sqlalchemy import select, Select
from sqlalchemy.orm import DeclarativeBase
from typing import Generic, TypeVar, Type


class ORMBase(DeclarativeBase):
    pass


DB_MODEL = TypeVar('DB_MODEL', bound=ORMBase)
PK_TYPE = TypeVar('PK_TYPE')


class ORM(Generic[DB_MODEL]):
    def __init__(self, model: Type[DB_MODEL]):
        self.model: Type[DB_MODEL] = model

    def get_pk_name(self) -> str:
        pk = self.model.metadata.tables[self.model.__tablename__].primary_key
        return pk.columns_autoinc_first[0].key

    def query_get_one(self, ident: PK_TYPE) -> Select:
        return select(self.model).where(self.model.__dict__[self.get_pk_name()].__eq__(ident))

    def query_get_all(self) -> Select:
        return select(self.model)
