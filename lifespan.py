import os
import ollama
import chromadb
from contextlib import asynccontextmanager
from info_list import info


@asynccontextmanager
async def lifespan(app):

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

    app.state.collection = collection
    yield
