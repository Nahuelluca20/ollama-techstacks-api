import os
from typing import Union
from contextlib import asynccontextmanager

from annoy import AnnoyIndex
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
import numpy as np
from pydantic import BaseModel

import chromadb
import ollama
from info_list import info

from fastapi.middleware.cors import CORSMiddleware
from kv_operations import kv_delete, kv_put, kv_get, test_kv_access

load_dotenv()

embedding_dimension = 1024


@asynccontextmanager
async def lifespan(app: FastAPI):
    kv_auth = os.getenv("KV_AUTH")
    if not kv_auth:
        raise ValueError("KV_AUTH no está configurado en el archivo .env")

    client = chromadb.Client()
    collection = client.create_collection("tech_stacks")

    for i, item in enumerate(info):
        description = item["description"]
        links = " ".join(item["links"])
        combined_text = f"{description} {links}"

        response = ollama.embeddings(model="mxbai-embed-large", prompt=combined_text)
        embedding = response["embedding"]

        collection.add(
            ids=[str(i)],
            embeddings=[embedding],
            documents=[combined_text],
            metadatas=[{"description": description, "links": links}],
        )

    # Store collection in app state
    app.state.collection = collection
    yield

    print("Finished")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Item(BaseModel):
    name: str
    price: float
    is_offered: Union[bool, None] = None


@app.get("/")
def read_root():
    return {"root": "Hello world!"}


@app.get("/api/ollama")
async def ask_ollama(prompt: Union[str, None] = None, request: Request = None):
    if prompt is None:
        raise HTTPException(status_code=400, detail="Prompt not provided")

    embed_response = ollama.embeddings(model="mxbai-embed-large", prompt=prompt)
    prompt_embedding = np.array(embed_response["embedding"]).astype("float32")

    collection = request.app.state.collection
    results = collection.query(
        query_embeddings=[embed_response["embedding"]],
        n_results=3,
        include=["metadatas", "documents"],
    )

    if not results["ids"] or not results["metadatas"] or not results["documents"]:
        raise HTTPException(status_code=404, detail="No relevant results found")

    try:
        responses = []
        for metadata, document in zip(results["metadatas"][0], results["documents"][0]):
            link = metadata["links"].split()[0]

            context = f"Based on this info: {document[:100]}... Link: {link}"
            prompt_for_ollama = context + f" Provide a brief response to: {prompt}"

            generation_response = ollama.generate(
                model="llama3.2",
                prompt=prompt_for_ollama,
                options={"num_predict": 50},
            )

            response_text = generation_response["response"].strip()
            responses.append(
                {
                    "link": link,
                    "short_response": response_text,
                }
            )

            annoy_index.add_item(len(prompt_cache), prompt_embedding)
            prompt_cache[len(prompt_cache)] = prompt
            await kv_put(prompt, response_text)

        return {"results": responses}
    except (IndexError, KeyError) as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing results: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


class KVRequest(BaseModel):
    key_name: str
    value: str


@app.put("/api/kv-value")
async def add_kv_value(request: KVRequest):
    val = kv_put(request.key_name, request.value)
    return {"success": val}


@app.get("/api/kv-value/{key_name}")
async def get_kv_value(key_name: str):
    val = kv_get(key_name)
    return {"value": val}


@app.delete("/api/kv-value/{key_name}")
async def delete_kv_value(key_name: str):
    success = kv_delete(key_name)
    return {"success": success}


@app.get("/api/test-kv")
async def test_kv():
    test_kv_access()
