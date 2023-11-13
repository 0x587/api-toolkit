"""
control层 用于完成数据库操作
"""
from sqlalchemy.orm import Session
from typing import Generic, Sequence
from .orm import ORM, PK_TYPE, DB_MODEL


class Control(Generic[DB_MODEL]):
    def __init__(self, orm: ORM):
        self.orm: ORM = orm

    def get_one(self, db: Session, ident: PK_TYPE):
        return db.scalars(self.orm.query_get_one(ident)).one_or_none()

    def get_all(self, db: Session) -> Sequence[DB_MODEL]:
        return db.scalars(self.orm.query_get_all()).all()
