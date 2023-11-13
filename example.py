import uvicorn
from fastapi import FastAPI

from db import get_db, engine
from api_toolkit.orm import ORMBase
from api_toolkit.route import Route
from models import ProjectDB, ProjectSchema, RateeDB, RateeSchema, RateRecordDB, RateRecordSchema

ORMBase.metadata.create_all(engine)

project_route = Route(ProjectDB, ProjectSchema, get_db)
ratee_route = Route(RateeDB, RateeSchema, get_db)
rate_record_route = Route(RateRecordDB, RateRecordSchema, get_db)

app = FastAPI()
app.include_router(project_route)
app.include_router(ratee_route)
app.include_router(rate_record_route)
uvicorn.run(app)
