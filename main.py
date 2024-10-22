import json
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
import redis
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

redis_client = redis.StrictRedis(host="localhost", port=6379, db=0)


class Item(BaseModel):
    name: str
    price: float
    is_offered: Union[bool, None] = None


@app.get("/")
def read_root():
    return {"root": "Hello world!"}


def cosine_similarity(vecA, vecB):
    dot_product = np.dot(vecA, vecB)
    normA = np.linalg.norm(vecA)
    normB = np.linalg.norm(vecB)
    return dot_product / (normA * normB)


@app.get("/api/ollama")
async def ask_ollama(prompt: Union[str, None] = None, request: Request = None):
    if prompt is None:
        raise HTTPException(status_code=400, detail="Prompt not provided")

    embed_response = ollama.embeddings(model="mxbai-embed-large", prompt=prompt)
    embedding_vector = np.array(embed_response["embedding"])

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

        # Search for similarity in cached embeddings in Redis
        keys = redis_client.keys("embedding:*")
        best_match = None
        best_similarity = -1
        print("keys", keys)

        for key in keys:
            # Retrieve stored embedding
            data = json.loads(redis_client.get(key))
            stored_embedding = np.array(data["embedding"])

            # Compare using cosine similarity
            similarity = cosine_similarity(embedding_vector, stored_embedding)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = data
        print("best_match", best_match)

        THRESHOLD = 0.8
        if best_similarity > THRESHOLD:

            print(
                {
                    "message": "Similar response found in cache",
                    "similarity": best_similarity,
                    "cached_response": best_match["response"],
                }
            )

            responses.append(
                {
                    "link": "link",
                    "short_response": best_match["response"],
                }
            )
            return {"results": responses}

        for metadata, document in zip(results["metadatas"][0], results["documents"][0]):
            link = metadata["links"].split()[0]

            context = f"Based on this info: {document[:100]}... Link: {link}"
            prompt_for_ollama = context + f" Provide a brief response to: {prompt}"

            generation_response = ollama.generate(
                model="llama3.2",
                prompt=prompt_for_ollama,
                options={"num_predict": 50},
            )
            results = collection.query(
                query_embeddings=[embed_response["embedding"]], n_results=3
            )

            response_text = generation_response["response"].strip()
            responses.append(
                {
                    "link": link,
                    "short_response": response_text,
                }
            )

            # Store the new embedding and its response in Redis
            key = f"embedding:{prompt}"
            redis_data = {
                "embedding": embedding_vector.tolist(),  # store the embedding
                "response": responses[0]["short_response"],  # save the first answer
            }

            redis_client.set(key, json.dumps(redis_data))

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
