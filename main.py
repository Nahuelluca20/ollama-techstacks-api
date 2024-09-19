from typing import Union
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from pydantic import BaseModel

import chromadb
import ollama
from info_list import info


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = chromadb.Client()
    collection = client.create_collection("tech_stacks")

    for i, d in enumerate(info):
        response = ollama.embeddings(model="mxbai-embed-large", prompt=d)
        embedding = response["embedding"]
        collection.add(ids=[str(i)], embeddings=[embedding], documents=[d])

    # Store collection in app state
    app.state.collection = collection
    yield

    print("Finished")


app = FastAPI(lifespan=lifespan)


class Item(BaseModel):
    name: str
    price: float
    is_offered: Union[bool, None] = None


@app.get("/")
def read_root():
    return {"root": "Hello world!"}


@app.get("/api")
def api_root():
    return {"Hello": "api route"}


@app.get("/api/items/{item_id}")
def read_items(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.get("/api/ollama")
async def ask_ollama(prompt: Union[str, None] = None, request: Request = None):
    if prompt == None:
        return {"error": "Prompt not provided"}

    response = ollama.embeddings(model="mxbai-embed-large", prompt=prompt)

    collection = request.app.state.collection
    results = collection.query(query_embeddings=[response["embedding"]], n_results=1)
    data = results["documents"][0][0]

    if data:
        return {"Answer": data}
    else:
        return {"Answer": "Error"}
