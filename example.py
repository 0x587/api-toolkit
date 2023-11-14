from api_toolkit.generate import CodeGenerator
from metadata.models import *

g = CodeGenerator()
g.generate_tables()
g.generate_route()

from fastapi import FastAPI
import uvicorn
from inner_code.routers import *

app = FastAPI()
app.include_router(video_study_router)
app.include_router(video_router)
app.include_router(sentence_router)
app.include_router(video_record_router)
uvicorn.run(app)
