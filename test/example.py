from api_toolkit.generate import CodeGenerator
from metadata.models import *

g = CodeGenerator()
g.parse_models()
g.generate_tables()
# g.generate_tables()
# g.generate_route()
#
# from fastapi import FastAPI
# from fastapi_pagination import add_pagination
# import uvicorn
# from inner_code.routers import *
#
# app = FastAPI()
# app.include_router(video_study_router)
# app.include_router(video_router)
# app.include_router(sentence_router)
# app.include_router(video_record_router)
# add_pagination(app)
# uvicorn.run(app)
