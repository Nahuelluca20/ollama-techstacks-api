from fastapi import APIRouter, Request, HTTPException
from typing import Union
import ollama
import numpy as np
from redis_operations import get_cached_embedding, cache_embedding

ollama_router = APIRouter()


@ollama_router.get("/ollama")
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

    best_match, best_similarity = get_cached_embedding(embedding_vector)

    THRESHOLD = 0.7
    if best_similarity > THRESHOLD:
        print(best_match["response"])
        return {"results": best_match["response"]}

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
        responses.append({"link": link, "short_response": response_text})

        cache_embedding(prompt, embedding_vector, responses)

    return {"results": responses}
