# Alfred — a private, local AI assistant

Alfred is a personal AI assistant that runs entirely on your own computer.
No account, no cloud API key, no telemetry. Once set up, it works fully offline.

---

**© 2026 mintedsage. All rights reserved.**

This code is shared publicly for transparency and feedback only. It is **not** licensed
for reuse, redistribution, modification, or commercial use without explicit written
permission from the author. Viewing the source does not grant any rights to copy or
reuse it.

If you're interested in using, licensing, or contributing to this project, please open
an issue or contact mntd.sage@gmail.com.

---

## Architecture

```
┌─────────────────────────────────────────────┐
│  UI  (FastAPI + HTML/JS, wrapped by pywebview)│  chat window, memory/task/note panels
├─────────────────────────────────────────────┤
│  Agent  (core/agent.py)                       │  butler persona, orchestration
├─────────────────────────────────────────────┤
│  RAG  (core/rag.py)                           │  merges memory + document retrieval
├───────────────┬───────────────┬───────────────┤
│ Memory Store  │ Document Store│ Tools         │  SQLite + local embeddings
│ (core/memory) │ (core/documents)│ (core/tools)│
├───────────────┴───────────────┴───────────────┤
│  LLM Client  (core/llm.py)                    │  talks to a local Ollama model
└─────────────────────────────────────────────┘
```

**Why this stack:**
- **Ollama** — the simplest reliable way to run and swap local open-weight models. Pull a model once; after that, no network calls are required for inference.
- **sentence-transformers** — computes text embeddings locally for retrieval (RAG). The model downloads once from Hugging Face on first run and is cached; every run after that is offline.
- **SQLite** — zero-config, file-based storage for memories, document chunks, tasks, reminders, and notes. Everything lives under `data/` on your disk.
- **Fernet (cryptography)** — encrypts memory and document content at rest. The key is generated locally on first run and stored with restricted file permissions; it is never transmitted anywhere.
- **FastAPI + pywebview** — a small local web server wrapped in a native desktop window, so there's a real chat UI without needing a browser tab, and without the complexity of a full Electron-style app.

**Privacy guarantees baked into the design:**
- The server only binds to `127.0.0.1` — never reachable from your network.
- The only third parties Alfred ever talks to are: (1) your local Ollama instance, and (2) Hugging Face, once, to download the embedding model weights. No user content is ever sent to either during normal operation, and Ollama itself is local.
- All memories and document chunks are encrypted at rest (toggle via `config.ENCRYPT_AT_REST`).
- You own your data: view, edit, and delete any memory from the sidebar at any time — nothing is hidden.

---

## Setup

1. **Install [Ollama](https://ollama.com)** and pull a model:
   ```bash
   ollama pull llama3.1
   ```
   You can pull others too (`mistral`, `qwen2.5`, `phi3`...) — Alfred lets you switch between whichever models you've pulled, from the sidebar.

2. **Install Python dependencies** (Python 3.10+):
   ```bash
   cd alfred
   python -m venv .venv && source .venv/bin/activate   # optional but recommended
   pip install -r requirements.txt
   ```

3. **Run Alfred:**
   ```bash
   python main.py
   ```
   The first run downloads the embedding model (one-time, needs internet). Every run after that works fully offline as long as Ollama is running locally.

---

## What works today (MVP — Milestone 1)

- Local chat with a butler persona, via any Ollama model, switchable from the UI.
- Long-term memory: add/view/delete facts, preferences, goals from the sidebar; encrypted at rest.
- Basic RAG: memories are semantically retrieved and injected into context for every chat turn.
- Document ingestion (`.txt`, `.md`, `.pdf`) with chunking, embedding, and semantic search; a summarize endpoint.
- Simple local tools: tasks, notes, reminders (structurally in place; not yet invoked autonomously by the model).
- All storage local, encrypted, and inspectable — nothing leaves the machine.

## Roadmap

- **M2** — Deeper document workflows: auto-chunked long-file summarization, citation of source snippets in chat replies, drag-and-drop ingestion from the UI.
- **M3** — Native tool-calling: let the model itself decide to call `add_task`, `search_files`, etc. via Ollama's function-calling support, rather than the user driving tools purely through the sidebar.
- **M4** — Richer memory management: importance-based decay/review prompts, memory categories/tags in the UI, conflict detection ("this contradicts something I remember").
- **M5** — Coding assistant tool (local repo-aware Q&A), reminders that actually fire as OS notifications, packaged installer (PyInstaller) so non-technical users don't need a Python environment.

## Project layout

```
alfred/
├── config.py              # all paths, model defaults, retrieval/security settings
├── main.py                # desktop app entry point
├── core/
│   ├── llm.py              # Ollama connector, model switching
│   ├── embeddings.py       # local embedding model wrapper
│   ├── security.py         # encryption-at-rest (Fernet)
│   ├── memory.py           # long-term memory store + semantic search
│   ├── documents.py        # file ingestion, chunking, semantic search
│   ├── rag.py               # combines memory + document retrieval into context
│   ├── tools.py             # tasks, reminders, notes, file search
│   └── agent.py             # Alfred's persona + orchestration
├── ui/
│   ├── app.py               # FastAPI backend
│   └── static/              # index.html, style.css, chat.js
└── data/                    # your local, encrypted data (gitignored)
```
