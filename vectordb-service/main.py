import chromadb
from chromadb.config import Settings
from fastapi import FastAPI, HTTPException

from models import StoreRequest, SearchRequest

app = FastAPI(title="VectorDB Service")

# ------------------ CHROMA INIT ------------------

client = chromadb.PersistentClient(
    path="./chromadb"
)

collection = client.get_or_create_collection(
    name="rag_chunks"
)

# ------------------ API ENDPOINTS ------------------

@app.get("/health")
def health_check():
    """Health check endpoint for Docker"""
    return {"status": "ok", "service": "vectordb"}

@app.post("/store")
def store_vectors(req: StoreRequest):
    try:
        ids = [
            f"{req.doc_id}_{i}"
            for i in range(len(req.chunks))
        ]

        metadatas = [
            {"doc_id": req.doc_id}
            for _ in req.chunks
        ]

        collection.add(
            ids=ids,
            documents=req.chunks,
            embeddings=req.embeddings,
            metadatas=metadatas
        )

        # No need to call persist() - PersistentClient auto-persists

        return {
            "message": "Vectors stored",
            "count": len(ids)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
def search_vectors(req: SearchRequest):
    try:
        results = collection.query(
            query_embeddings=[req.embedding],
            n_results=req.top_k
        )

        response = []
        for i in range(len(results["documents"][0])):
            response.append({
                "text": results["documents"][0][i],
                "score": results["distances"][0][i],
                "doc_id": results["metadatas"][0][i]["doc_id"]
            })

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{doc_id}")
def delete_document_vectors(doc_id: int):
    try:
        collection.delete(
            where={"doc_id": doc_id}
        )

        # No need to call persist() - PersistentClient auto-persists

        return {"message": "Document vectors deleted"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))