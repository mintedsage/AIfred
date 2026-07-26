"""
rag.py — retrieval-augmented context assembly.

Given the user's latest message, pulls the most relevant long-term memories
and document chunks, and formats them into a compact context block that gets
prepended to the conversation sent to the LLM.
"""

from pathlib import Path

from config import MEMORY_TOP_K, DOCUMENT_TOP_K
from core.memory import MemoryStore
from core.documents import DocumentStore


def _friendly_name(path: str) -> str:
    """Show a short filename instead of a full local path in the context sent to the model."""
    return Path(path).name


def build_context(query: str, memory_store: MemoryStore, document_store: DocumentStore) -> str:
    memories = memory_store.search(query, top_k=MEMORY_TOP_K)
    doc_hits = document_store.search(query, top_k=DOCUMENT_TOP_K)

    parts = []

    if memories:
        mem_lines = [f"- ({m.category}) {m.content}" for m in memories]
        parts.append("Relevant things you know about the user:\n" + "\n".join(mem_lines))

    if doc_hits:
        doc_lines = [
            f"- From \"{_friendly_name(h['source'])}\" (chunk {h['chunk_index']}): {h['content'][:400]}"
            for h in doc_hits
        ]
        parts.append("Relevant excerpts from the user's own files:\n" + "\n".join(doc_lines))

    if not parts:
        return ""

    return "\n\n".join(parts)
