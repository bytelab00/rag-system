# Microservices RAG Architecture

A modular **Retrieval-Augmented Generation (RAG)** system built with **LangChain**, **Ollama Models**, and **Docker Compose**.
This project demonstrates a decoupled microservices architecture for document ingestion, vectorization, storage, and retrieval.

---

## Architecture

The system consists of four independent services communicating via HTTP on a shared Docker network.

| Service       | Port | Responsibility                                              | Stack                     |
| ------------- | ---- | ----------------------------------------------------------- | ------------------------- |
| **Ingestion** | 8001 | Document parsing (PDF/TXT/DOCX), chunking, metadata storage | PyPDF2, LangChain, SQLite |
| **Embedding** | 8002 | Converts text chunks into vector embeddings                 | Sentence-Transformers     |
| **Vector DB** | 8003 | Stores embeddings and performs cosine similarity search     | ChromaDB / FAISS, NumPy   |
| **Query**     | 8004 | Orchestrates RAG pipeline: retrieval + LLM inference        | OpenAI API / Ollama       |

---

## Technology Stack

- **Core:** Python 3.10+, FastAPI, Uvicorn
- **Infrastructure:** Docker, Docker Compose
- **ML / AI:** LangChain (text splitting), Sentence-Transformers (`all-MiniLM-L6-v2`)
- **Data:** SQLite, ChromaDB

---

## Project Structure

```
rag-system/
├── docker-compose.yml     # Service orchestration
├── ingestion-service/     # File processing & chunking
├── embedding-service/     # Vector generation
├── vectordb-service/      # Similarity search
└── query-service/         # RAG pipeline controller
```

---

## Setup & Deployment

### Prerequisites

- Docker
- Docker Compose
- Local Ollama setup (Llama3)

### Configuration

Set environment variables in `docker-compose.yml`:

```
environment:
  - EMBEDDING_SERVICE_URL=http://embedding:8002
  - VECTOR_DB_URL=http://vectordb:8003
```

### Execution

Build and launch the container network:

```
docker-compose up --build
```

---

## API Usage

### 1. Ingest Document

Upload a file to the ingestion service to populate the vector index.

```
curl -X POST "http://localhost:8001/upload" \
  -F "file=@/path/to/test.pdf"
```

### 2. Query System

Submit a natural language question.
The system retrieves relevant context and generates an answer.

```
curl -X POST "http://localhost:8004/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "Summarize the architectural constraints mentioned in the document."}'
```
