import os
import requests
from fastapi import FastAPI, HTTPException

from models import QueryRequest

EMBEDDING_SERVICE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://embedding:8002")
VECTORDB_SERVICE_URL = os.getenv("VECTORDB_SERVICE_URL", "http://vectordb:8003")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

app = FastAPI(title="Query Service")

# ------------------ HELPERS ------------------

def embed_query(text: str):
    response = requests.post(
        f"{EMBEDDING_SERVICE_URL}/embed",
        json={"text": text},
        timeout=30
    )

    if response.status_code != 200:
        raise RuntimeError("Embedding service failed")

    return response.json()["embedding"]

def search_vectors(embedding: list, top_k: int):
    response = requests.post(
        f"{VECTORDB_SERVICE_URL}/search",
        json={
            "embedding": embedding,
            "top_k": top_k
        },
        timeout=30
    )

    if response.status_code != 200:
        raise RuntimeError("Vector search failed")

    return response.json()

def build_prompt(context_chunks: list, question: str):
    context_text = "\n\n".join(
        f"- {chunk['text']}" for chunk in context_chunks
    )

    return f"""
You are a helpful assistant.
Answer the question using ONLY the context below.
If the answer is not in the context, say "I don't know".

Context:
{context_text}

Question:
{question}

Answer:
""".strip()

def call_ollama(prompt: str):
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=1200
    )

    if response.status_code != 200:
        raise RuntimeError("Ollama generation failed")

    return response.json()["response"]

# ------------------ API ENDPOINTS ------------------

@app.post("/query")
def query_rag(req: QueryRequest):
    try:
        embedding = embed_query(req.question)
        chunks = search_vectors(embedding, req.top_k)

        if not chunks:
            return {"answer": "No relevant context found."}

        prompt = build_prompt(chunks, req.question)
        answer = call_ollama(prompt)

        return {
            "question": req.question,
            "answer": answer,
            "sources": [
                {
                    "doc_id": c["doc_id"],
                    "score": c["score"]
                }
                for c in chunks
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}
