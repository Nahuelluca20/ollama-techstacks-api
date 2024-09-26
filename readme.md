# FastAPI Tech Stack Recommender

This project is an API built with FastAPI that provides tech stack recommendations based on user queries. It uses embeddings and a vector database to find relevant information and generate responses.

## Features

- API endpoint for tech stack queries
- Uses Chroma DB for embedding storage and search
- Integration with Ollama for embedding generation and responses
- CORS handling to allow requests from a local frontend

## Requirements

- Python 3.7+
- FastAPI
- Chroma DB
- Ollama
- Pydantic

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install fastapi chromadb ollama pydantic
   ```

## Usage

1. Start the server:
   ```
   fastapi dev main.py
   ```
2. The API will be available at `http://localhost:8000`

## Endpoints

- `GET /`: Root route
- `GET /api`: Basic API route
- `GET /api/items/{item_id}`: Example route with path and query parameters
- `GET /api/ollama`: Main endpoint for tech stack queries

## How it works

1. On startup, the application loads tech stack information into a Chroma DB collection.
2. When a query is received, an embedding is generated for the query.
3. The most similar documents are searched for in the vector database.
4. Ollama is used to generate short responses based on the found information.
5. Responses are returned along with relevant links.

## Contributing

Contributions are welcome. Please open an issue to discuss major changes before submitting a pull request.

## License

[MIT](https://choosealicense.com/licenses/mit/)
