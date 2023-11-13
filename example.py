import uvicorn
from fastapi import FastAPI

from db import get_db, engine
from api_toolkit.orm import ORMBase
from api_toolkit.route import Route
from models import ProjectDB, ProjectSchema

ORMBase.metadata.create_all(engine)

project_route = Route(ProjectDB, ProjectSchema, get_db)

app = FastAPI()
app.include_router(project_route)
uvicorn.run(app)
