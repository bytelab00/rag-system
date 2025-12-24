import os
import requests
import numpy as np
from fastapi import FastAPI, HTTPException
from sentence_transformers import SentenceTransformer

from models import EmbedRequest, EmbedBatchRequest

VECTORDB_URL = os.getenv("VECTORDB_URL", "http://vectordb:8003")
MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

app = FastAPI(title="Embedding Service")

# Load model once at startup
model = SentenceTransformer(MODEL_NAME)

# ------------------ HELPERS ------------------

def store_vectors(doc_id: int, chunks: list, embeddings: list):
    payload = {
        "doc_id": doc_id,
        "chunks": chunks,
        "embeddings": embeddings
    }

    response = requests.post(
        f"{VECTORDB_URL}/store",
        json=payload,
        timeout=60
    )

    if response.status_code != 200:
        raise RuntimeError("VectorDB storage failed")

# ------------------ API ENDPOINTS ------------------

@app.post("/embed")
def embed_text(req: EmbedRequest):
    try:
        vector = model.encode(req.text).tolist()
        return {"embedding": vector}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/embed-batch")
def embed_batch(req: EmbedBatchRequest):
    try:
        embeddings = model.encode(req.chunks)
        embeddings = [vec.tolist() for vec in embeddings]

        store_vectors(req.doc_id, req.chunks, embeddings)

        return {
            "message": "Embeddings generated and stored",
            "chunks": len(req.chunks)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
