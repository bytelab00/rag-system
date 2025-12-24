import os
import requests
from fastapi import FastAPI, UploadFile, File, HTTPException
from langchain_text_splitters import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader
from docx import Document

from models import (
    init_db,
    insert_document,
    update_status,
    list_documents,
    delete_document
)

EMBEDDING_SERVICE_URL = "http://embedding:8002"

app = FastAPI(title="Ingestion Service")

# Ensure data folder exists
os.makedirs("data", exist_ok=True)
init_db()

# ------------------ UTIL FUNCTIONS ------------------

def extract_text(file: UploadFile) -> str:
    if file.filename.endswith(".txt"):
        return file.file.read().decode("utf-8")

    if file.filename.endswith(".pdf"):
        reader = PdfReader(file.file)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if file.filename.endswith(".docx"):
        doc = Document(file.file)
        return "\n".join(p.text for p in doc.paragraphs)

    raise HTTPException(status_code=400, detail="Unsupported file type")

def split_text(text: str):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    return splitter.split_text(text)

def send_chunks(doc_id: int, chunks: list):
    payload = {
        "doc_id": doc_id,
        "chunks": chunks
    }

    response = requests.post(
        f"{EMBEDDING_SERVICE_URL}/embed-batch",
        json=payload,
        timeout=60
    )

    if response.status_code != 200:
        raise RuntimeError("Embedding service failed")

# ------------------ API ENDPOINTS ------------------

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        doc_id = insert_document(file.filename, "processing")

        text = extract_text(file)
        chunks = split_text(text)

        send_chunks(doc_id, chunks)

        update_status(doc_id, "completed")

        return {
            "message": "Document processed successfully",
            "doc_id": doc_id,
            "chunks": len(chunks)
        }

    except Exception as e:
        update_status(doc_id, "failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
def get_documents():
    return list_documents()

@app.delete("/documents/{doc_id}")
def remove_document(doc_id: int):
    delete_document(doc_id)

    # also delete vectors from vectordb
    try:
        requests.delete(f"http://vectordb:8003/documents/{doc_id}")
    except Exception:
        pass

    return {"message": "Document deleted"}
