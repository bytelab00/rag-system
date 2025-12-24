from pydantic import BaseModel
from typing import List

class EmbedRequest(BaseModel):
    text: str

class EmbedBatchRequest(BaseModel):
    doc_id: int
    chunks: List[str]
