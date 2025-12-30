import os
import requests
import time
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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

# ------------------ CORS CONFIG ------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://frontend:80",
        "http://frontend-service:80"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------

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

def send_chunks(doc_id: int, chunks: list, retries=5, delay=5):
    """
    Send chunks to Embedding Service with retry if service is not ready.
    """
    payload = {"doc_id": doc_id, "chunks": chunks}

    for attempt in range(1, retries + 1):
        try:
            print(f"[INFO] Sending chunks to Embedding Service (attempt {attempt})...")
            response = requests.post(
                f"{EMBEDDING_SERVICE_URL}/embed-batch",
                json=payload,
                timeout=60
            )
            if response.status_code == 200:
                print(f"[INFO] Successfully sent {len(chunks)} chunks for doc_id={doc_id}")
                return
            else:
                print(f"[WARN] Embedding service returned {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"[WARN] Attempt {attempt}: Embedding service not ready ({e})")

        time.sleep(delay)

    raise RuntimeError("Embedding service failed after multiple retries")

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
