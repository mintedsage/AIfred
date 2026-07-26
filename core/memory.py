"""
memory.py — Alfred's long-term memory.

Stores user facts, preferences, goals, projects, and notes in a local SQLite
database. Content is encrypted at rest (see core/security.py). Each memory
also stores an embedding vector so it can be retrieved semantically, not just
by exact keyword match.

The user can list, add, edit, and delete memories at any time — nothing is
hidden from them; this is their data.
"""

import sqlite3
import time
import uuid
import numpy as np

from config import MEMORY_DB_PATH
from core.security import vault
from core.embeddings import embed, embed_many, cosine_similarity


SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    content_enc BLOB NOT NULL,
    category TEXT NOT NULL DEFAULT 'note',
    importance INTEGER NOT NULL DEFAULT 3,
    embedding BLOB NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
"""


class Memory:
    """A single decrypted memory, for display/editing in the UI."""

    def __init__(self, id, content, category, importance, created_at, updated_at):
        self.id = id
        self.content = content
        self.category = category
        self.importance = importance
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "category": self.category,
            "importance": self.importance,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class MemoryStore:
    def __init__(self, db_path=MEMORY_DB_PATH):
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.conn.execute(SCHEMA)
        self.conn.commit()

    # --- CRUD ---------------------------------------------------------

    def add(self, content: str, category: str = "note", importance: int = 3) -> str:
        """Store a new memory. category examples: 'preference', 'goal', 'project', 'fact', 'note'."""
        mem_id = str(uuid.uuid4())
        now = time.time()
        vec = embed(content).tobytes()
        content_enc = vault.encrypt(content)
        self.conn.execute(
            "INSERT INTO memories (id, content_enc, category, importance, embedding, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (mem_id, content_enc, category, importance, vec, now, now),
        )
        self.conn.commit()
        return mem_id

    def update(self, mem_id: str, content: str = None, category: str = None, importance: int = None) -> bool:
        row = self.conn.execute("SELECT content_enc, category, importance FROM memories WHERE id = ?", (mem_id,)).fetchone()
        if row is None:
            return False
        current_content = vault.decrypt(row[0])
        new_content = content if content is not None else current_content
        new_category = category if category is not None else row[1]
        new_importance = importance if importance is not None else row[2]

        vec = embed(new_content).tobytes() if content is not None else None
        now = time.time()

        if vec is not None:
            self.conn.execute(
                "UPDATE memories SET content_enc=?, category=?, importance=?, embedding=?, updated_at=? WHERE id=?",
                (vault.encrypt(new_content), new_category, new_importance, vec, now, mem_id),
            )
        else:
            self.conn.execute(
                "UPDATE memories SET category=?, importance=?, updated_at=? WHERE id=?",
                (new_category, new_importance, now, mem_id),
            )
        self.conn.commit()
        return True

    def delete(self, mem_id: str) -> bool:
        cur = self.conn.execute("DELETE FROM memories WHERE id = ?", (mem_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def get_all(self) -> list[Memory]:
        rows = self.conn.execute(
            "SELECT id, content_enc, category, importance, created_at, updated_at FROM memories ORDER BY updated_at DESC"
        ).fetchall()
        return [
            Memory(r[0], vault.decrypt(r[1]), r[2], r[3], r[4], r[5])
            for r in rows
        ]

    # --- Retrieval ------------------------------------------------------

    def search(self, query: str, top_k: int = 4) -> list[Memory]:
        """Semantic search over stored memories, most relevant first."""
        rows = self.conn.execute(
            "SELECT id, content_enc, category, importance, embedding, created_at, updated_at FROM memories"
        ).fetchall()
        if not rows:
            return []

        query_vec = embed(query)
        matrix = np.stack([np.frombuffer(r[4], dtype=np.float32) for r in rows])
        sims = cosine_similarity(query_vec, matrix)

        # Blend semantic similarity with a small importance boost so critical
        # facts (e.g. importance=5) surface slightly more readily than trivia.
        importance_boost = np.array([r[3] for r in rows], dtype=np.float32) * 0.02
        scores = sims + importance_boost

        order = np.argsort(-scores)[:top_k]
        return [
            Memory(rows[i][0], vault.decrypt(rows[i][1]), rows[i][2], rows[i][3], rows[i][5], rows[i][6])
            for i in order
        ]
