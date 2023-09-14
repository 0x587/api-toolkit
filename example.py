import uvicorn
from fastapi import FastAPI

app = FastAPI()

# run app
uvicorn.run(app)
