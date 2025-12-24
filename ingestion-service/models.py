import sqlite3
from datetime import datetime

DB_PATH = "data/documents.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()

def insert_document(filename: str, status: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO documents (filename, status, created_at)
    VALUES (?, ?, ?)
    """, (filename, status, datetime.utcnow().isoformat()))

    conn.commit()
    doc_id = cursor.lastrowid
    conn.close()
    return doc_id

def update_status(doc_id: int, status: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE documents SET status = ? WHERE id = ?
    """, (status, doc_id))

    conn.commit()
    conn.close()

def list_documents():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, filename, status, created_at FROM documents")
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "filename": row[1],
            "status": row[2],
            "created_at": row[3]
        }
        for row in rows
    ]

def delete_document(doc_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()
