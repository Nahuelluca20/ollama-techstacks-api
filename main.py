from dotenv import load_dotenv
from fastapi import FastAPI

from routes.ollama_routes import ollama_router
from routes.kv_routes import kv_router

import redis

from fastapi.middleware.cors import CORSMiddleware

from lifespan import lifespan

load_dotenv()


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

redis_client = redis.StrictRedis(host="localhost", port=6379, db=0)

app.include_router(ollama_router, prefix="/api")
app.include_router(kv_router, prefix="/api")


@app.get("/")
def read_root():
    return {"root": "Hello world!"}
