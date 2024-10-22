import redis
import numpy as np
import json
from utils import cosine_similarity

redis_client = redis.StrictRedis(host="localhost", port=6379, db=0)


def get_cached_embedding(embedding_vector):
    keys = redis_client.keys("embedding:*")
    best_match = None
    best_similarity = -1

    for key in keys:
        # Retrieve stored embedding
        data = json.loads(redis_client.get(key))
        stored_embedding = np.array(data["embedding"])

        # Compare using cosine similarity
        similarity = cosine_similarity(embedding_vector, stored_embedding)
        if similarity > best_similarity:
            best_similarity = similarity
            best_match = data
    return best_match, best_similarity


def cache_embedding(prompt, embedding_vector, response):
    # Store the new embedding and its response in Redis
    key = f"embedding:{prompt}"
    redis_data = {
        "embedding": embedding_vector.tolist(),
        "response": response,
    }
    redis_client.set(key, json.dumps(redis_data))
