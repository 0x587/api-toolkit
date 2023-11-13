from api_toolkit.orm import BaseORM, Base
from db import engine, get_db
from models import ProjectDB, RateeDB, RateRecordDB

Base.metadata.create_all(engine)

db = next(get_db())

Project = BaseORM(db, ProjectDB)
Ratee = BaseORM(db, RateeDB)
RateRecord = BaseORM(db, RateRecordDB)

p1 = Project.create(ProjectDB(name='TestProject1'))
p2 = Project.create(ProjectDB(name='TestProject2'))

r1 = Ratee.create(RateeDB(name='TestRatee1'))
r2 = Ratee.create(RateeDB(name='TestRatee2'))
