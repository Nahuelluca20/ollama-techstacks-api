from typing import Union
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel

import chromadb
import ollama
from info_list import info

from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
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


@app.get("/api")
def api_root():
    return {"Hello": "api route"}


@app.get("/api/items/{item_id}")
def read_items(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


# @app.get("/api/ollama")
# async def ask_ollama(prompt: Union[str, None] = None, request: Request = None):
#     if prompt == None:
#         return {"error": "Prompt not provided"}

#     response = ollama.embeddings(model="mxbai-embed-large", prompt=prompt)

#     collection = request.app.state.collection
#     results = collection.query(
#         query_embeddings=[response["embedding"]],
#         n_results=3,
#         include=["metadatas", "distances"],
#     )

#     if results["metadatas"]:
#         metadata = results["metadatas"][0][0]
#         document = results["documents"][0][0]
#         link = metadata["links"].split()[0]

#         context = f"Based on the following information: {document}\n\nRelevant link: {link}\n\n"
#         prompt_for_ollama = (
#             context
#             + f"Please provide an elaborated response to the following query: {prompt}"
#         )

#         generation_response = ollama.generate(
#             model="llama3.1", prompt=prompt_for_ollama
#         )

#         return {"link": link, "response": generation_response["response"]}
#     else:
#         return {"Answer": "No se encontraron resultados"}


@app.get("/api/ollama")
async def ask_ollama(prompt: Union[str, None] = None, request: Request = None):
    if prompt is None:
        raise HTTPException(status_code=400, detail="Prompt not provided")

    embed_response = ollama.embeddings(model="mxbai-embed-large", prompt=prompt)

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
                model="llama3.1",
                prompt=prompt_for_ollama,
                options={"num_predict": 50},
            )

            responses.append(
                {
                    "link": link,
                    "short_response": generation_response["response"].strip(),
                }
            )

        return {"results": responses}
    except (IndexError, KeyError) as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing results: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
