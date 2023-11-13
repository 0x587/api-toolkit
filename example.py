import json
from typing import Tuple

import uvicorn
from fastapi import FastAPI
from sqlalchemy import func, select
from sqlalchemy.orm import Bundle

from api_toolkit.orm import BaseORM
from models import *

from db import engine, get_db
from schemas import *

Base.metadata.create_all(engine)

ratee_orm = BaseORM(next(get_db()), RateeDB)
rate_record_orm = BaseORM(next(get_db()), RateRecordDB)

# r = ratee_orm.get_all().first()
# # print(json.dumps(Ratee(**r.__dict__)))
# print(r.__dict__)
# print(Ratee(**r.__dict__))
# print(rate_record_orm.get_one(('8c621d20-c0c6-4cb2-99d4-389d614c5020', 'ed6d60fd-da19-470a-9aef-64ba9fa7b1e2')))

db = next(get_db())

Project = BaseORM(db, ProjectDB)

projects = db.scalars(Project.get_all_query()).all()

print(db.scalar(Project.get_one_query(projects[0].id)))

p = ProjectDB(name='TestProject')
Project.create(p)

# stmt = (
#     select(func.min(RateeDB.name).label('ratee_name'),
#            func.min(ProjectDB.name).label('project_name'),
#            func.avg(RateRecordDB.value).label('value'))
#     .group_by(RateRecordDB.ratee_id, RateRecordDB.project_id)
#     .join(RateeDB)
#     .join(ProjectDB)
# )

# stmt = select(RateeDB)

# print(db.scalars(select(RateeDB.id)).first())
# print(db.scalars(select(RateeDB.id, RateeDB.name)).first())
# print(stmt)
#
# for row in db.execute(stmt).mappings():
#     print(row)
# print(RateRecordDetail(**row))

# print(RateRecordDetail.from_orm(**records[0].__dict__))

# app = FastAPI()

# run app
# uvicorn.run(app)
