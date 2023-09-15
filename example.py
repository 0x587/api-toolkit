import uvicorn
from fastapi import FastAPI

from api_toolkit.orm import BaseORM
from models import *

from db import engine, get_db

Base.metadata.create_all(engine)

orm = BaseORM(next(get_db()), Ratee)

app = FastAPI()

# run app
# uvicorn.run(app)
