from pydantic import BaseModel
from typing import List

class StoreRequest(BaseModel):
    doc_id: int
    chunks: List[str]
    embeddings: List[List[float]]

class SearchRequest(BaseModel):
    embedding: List[float]
    top_k: int = 5
