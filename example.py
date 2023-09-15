import uvicorn
from fastapi import FastAPI

from models import *

from db import engine

Base.metadata.create_all(engine)

app = FastAPI()

# run app
uvicorn.run(app)
