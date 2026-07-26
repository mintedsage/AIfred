"""
documents.py — Alfred's knowledge of your files.

Lets you import .txt, .md, and .pdf files. Each file is split into
overlapping chunks, embedded locally, and stored (encrypted) in SQLite so
Alfred can later search and summarize your own material — never anyone else's,
and never sent anywhere.
"""

import sqlite3
import time
import uuid
from pathlib import Path
import numpy as np

from config import (
    DOCUMENTS_DB_PATH,
    DOCUMENT_CHUNK_SIZE,
    DOCUMENT_CHUNK_OVERLAP,
)
from core.security import vault
from core.embeddings import embed, embed_many, cosine_similarity


SCHEMA = """
CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY,
    source_path TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content_enc BLOB NOT NULL,
    embedding BLOB NOT NULL,
    created_at REAL NOT NULL
);
"""


def _read_text_from_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in (".txt", ".md"):
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    raise ValueError(f"Unsupported file type: {suffix}")


def _chunk_text(text: str, size=DOCUMENT_CHUNK_SIZE, overlap=DOCUMENT_CHUNK_OVERLAP) -> list[str]:
    text = text.strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return chunks


class DocumentStore:
    def __init__(self, db_path=DOCUMENTS_DB_PATH):
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.conn.execute(SCHEMA)
        self.conn.commit()

    def ingest_file(self, path: str) -> int:
        """Import a file, returns number of chunks stored."""
        p = Path(path).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(path)

        text = _read_text_from_file(p)
        chunks = _chunk_text(text)
        if not chunks:
            return 0

        vectors = embed_many(chunks)
        now = time.time()
        # Remove any previous chunks for this same file so re-imports don't duplicate.
        self.conn.execute("DELETE FROM chunks WHERE source_path = ?", (str(p),))

        for i, (chunk, vec) in enumerate(zip(chunks, vectors)):
            self.conn.execute(
                "INSERT INTO chunks (id, source_path, chunk_index, content_enc, embedding, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), str(p), i, vault.encrypt(chunk), vec.tobytes(), now),
            )
        self.conn.commit()
        return len(chunks)

    def list_sources(self) -> list[str]:
        rows = self.conn.execute("SELECT DISTINCT source_path FROM chunks").fetchall()
        return [r[0] for r in rows]

    def remove_source(self, path: str) -> int:
        cur = self.conn.execute("DELETE FROM chunks WHERE source_path = ?", (path,))
        self.conn.commit()
        return cur.rowcount

    def search(self, query: str, top_k: int = 4) -> list[dict]:
        rows = self.conn.execute(
            "SELECT id, source_path, chunk_index, content_enc, embedding FROM chunks"
        ).fetchall()
        if not rows:
            return []

        query_vec = embed(query)
        matrix = np.stack([np.frombuffer(r[4], dtype=np.float32) for r in rows])
        sims = cosine_similarity(query_vec, matrix)
        order = np.argsort(-sims)[:top_k]

        return [
            {
                "source": rows[i][1],
                "chunk_index": rows[i][2],
                "content": vault.decrypt(rows[i][3]),
                "score": float(sims[i]),
            }
            for i in order
        ]
