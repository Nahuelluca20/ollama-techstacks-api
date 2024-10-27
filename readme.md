# FastAPI Tech Stack Recommender

This project is an API built with FastAPI that provides tech stack recommendations based on user queries. It uses embeddings and a vector database to find relevant information and generate responses.

## Features

- API endpoint for tech stack queries
- Uses Chroma DB for embedding storage and search
- Integration with Ollama for embedding generation and responses
- CORS handling to allow requests from a local frontend
- Key-value storage with Redis
- Containerization with Docker

### Semantic Search

It can cache the answers in a redis and answer queries with the same semantic meaning.
[Semantic Search](./semantic-search.png)

## Requirements

- Docker and Docker Compose
- Python 3.7+ (for local development)

## Installation and Usage with Docker

1. Clone this repository
2. Navigate to the project directory
3. Run the following command to start the services:
   ```
   docker-compose up -d
   ```
4. The API will be available at `http://localhost:8000`

## Installation for Local Development

1. Clone this repository
2. Install dependencies:
   ```
   pip install fastapi chromadb ollama pydantic redis
   ```

## Usage in Local Development

1. Start the server:
   ```
   uvicorn main:app --reload
   ```
2. The API will be available at `http://localhost:8000`

## Endpoints

- `GET /`: Root route
- `GET /api`: Basic API route
- `GET /api/ollama`: Main endpoint for tech stack queries
- `PUT /api/kv-value`: Adds a value to the key-value database
- `GET /api/kv-value/{key_name}`: Retrieves a value from the key-value database
- `DELETE /api/kv-value/{key_name}`: Deletes a value from the key-value database
- `GET /api/test-kv`: Tests access to the key-value database

## How it works

1. On startup, the application loads tech stack information into a Chroma DB collection.
2. When a query is received, an embedding is generated for the query.
3. The most similar documents are searched for in the vector database.
4. Ollama is used to generate short responses based on the found information.
5. Responses are returned along with relevant links.
6. Redis is used for key-value storage for additional data.

## Contributing

Contributions are welcome. Please open an issue to discuss major changes before submitting a pull request.

## License

[MIT](https://choosealicense.com/licenses/mit/)
