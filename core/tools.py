"""
tools.py — the actions Alfred can take on your behalf.

  - Tasks:     a to-do list
  - Reminders: time-tagged notes
  - Notes:     free-form notes, separate from long-term "memory" facts
  - FileSearch: find files on disk by name/extension under a given root

As of M3, these are wired into core/agent.py as tools the LLM can invoke
directly via Ollama's native tool-calling, rather than dispatched from
keywords — the model itself decides when to add a task, set a reminder, etc.
"""

import sqlite3
import time
import uuid
from pathlib import Path

from config import TOOLS_DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY, content TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0, created_at REAL
);
CREATE TABLE IF NOT EXISTS reminders (
    id TEXT PRIMARY KEY, content TEXT NOT NULL, remind_at REAL, created_at REAL
);
CREATE TABLE IF NOT EXISTS notes (
    id TEXT PRIMARY KEY, title TEXT, content TEXT NOT NULL, created_at REAL
);
"""


class ToolBox:
    def __init__(self, db_path=TOOLS_DB_PATH):
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    # --- Tasks ---------------------------------------------------------
    def add_task(self, content: str) -> str:
        tid = str(uuid.uuid4())
        self.conn.execute("INSERT INTO tasks (id, content, done, created_at) VALUES (?, ?, 0, ?)",
                           (tid, content, time.time()))
        self.conn.commit()
        return tid

    def complete_task(self, task_id: str) -> bool:
        cur = self.conn.execute("UPDATE tasks SET done=1 WHERE id=?", (task_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def list_tasks(self, include_done: bool = False) -> list[dict]:
        q = "SELECT id, content, done, created_at FROM tasks"
        if not include_done:
            q += " WHERE done = 0"
        q += " ORDER BY created_at DESC"
        rows = self.conn.execute(q).fetchall()
        return [{"id": r[0], "content": r[1], "done": bool(r[2]), "created_at": r[3]} for r in rows]

    # --- Reminders -------------------------------------------------------
    def add_reminder(self, content: str, remind_at: float) -> str:
        rid = str(uuid.uuid4())
        self.conn.execute("INSERT INTO reminders (id, content, remind_at, created_at) VALUES (?, ?, ?, ?)",
                           (rid, content, remind_at, time.time()))
        self.conn.commit()
        return rid

    def add_reminder_in(self, content: str, minutes_from_now: float) -> str:
        """Convenience wrapper for tool-calling: easier for a model to say
        'remind me in 20 minutes' than to compute a raw epoch timestamp."""
        return self.add_reminder(content, time.time() + max(0, minutes_from_now) * 60)

    def list_reminders(self) -> list[dict]:
        rows = self.conn.execute("SELECT id, content, remind_at FROM reminders ORDER BY remind_at ASC").fetchall()
        return [{"id": r[0], "content": r[1], "remind_at": r[2]} for r in rows]

    # --- Notes -----------------------------------------------------------
    def add_note(self, content: str, title: str = "") -> str:
        nid = str(uuid.uuid4())
        self.conn.execute("INSERT INTO notes (id, title, content, created_at) VALUES (?, ?, ?, ?)",
                           (nid, title, content, time.time()))
        self.conn.commit()
        return nid

    def list_notes(self) -> list[dict]:
        rows = self.conn.execute("SELECT id, title, content, created_at FROM notes ORDER BY created_at DESC").fetchall()
        return [{"id": r[0], "title": r[1], "content": r[2], "created_at": r[3]} for r in rows]

    # --- File search -------------------------------------------------------
    @staticmethod
    def search_files(root: str, query: str, max_results: int = 25) -> list[str]:
        """Find files under `root` whose name contains `query` (case-insensitive)."""
        root_path = Path(root).expanduser()
        if not root_path.exists():
            return []
        query_lower = query.lower()
        matches = []
        for p in root_path.rglob("*"):
            if p.is_file() and query_lower in p.name.lower():
                matches.append(str(p))
                if len(matches) >= max_results:
                    break
        return matches
