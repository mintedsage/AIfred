"""
app.py — local web server that powers Alfred's UI.

This only ever binds to 127.0.0.1 (see config.UI_HOST) — nothing here is
reachable from the network. It exists purely so the desktop window
(main.py, via pywebview) has a UI to render.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))  # allow `import core`, `import config`

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.agent import Alfred
from core.voice import stt, tts

app = FastAPI(title="Alfred")
alfred = Alfred()

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


# --- Chat -------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str


@app.post("/api/chat")
def chat(req: ChatRequest):
    reply = alfred.chat(req.message)
    return {"reply": reply}


# --- Models -------------------------------------------------------------------

class ModelRequest(BaseModel):
    model: str


@app.get("/api/models")
def list_models():
    return {"models": alfred.list_models(), "current": alfred.llm.model}


@app.post("/api/models")
def set_model(req: ModelRequest):
    alfred.set_model(req.model)
    return {"current": alfred.llm.model}


# --- Memory -------------------------------------------------------------------

class MemoryCreateRequest(BaseModel):
    content: str
    category: str = "note"
    importance: int = 3


class MemoryUpdateRequest(BaseModel):
    content: str | None = None
    category: str | None = None
    importance: int | None = None


@app.get("/api/memories")
def list_memories():
    return {"memories": [m.to_dict() for m in alfred.memory.get_all()]}


@app.post("/api/memories")
def create_memory(req: MemoryCreateRequest):
    mem_id = alfred.memory.add(req.content, req.category, req.importance)
    return {"id": mem_id}


@app.put("/api/memories/{mem_id}")
def update_memory(mem_id: str, req: MemoryUpdateRequest):
    ok = alfred.memory.update(mem_id, req.content, req.category, req.importance)
    if not ok:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"ok": True}


@app.delete("/api/memories/{mem_id}")
def delete_memory(mem_id: str):
    ok = alfred.memory.delete(mem_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"ok": True}


# --- Documents -------------------------------------------------------------------

class IngestRequest(BaseModel):
    path: str


@app.post("/api/documents/ingest")
def ingest_document(req: IngestRequest):
    try:
        n_chunks = alfred.documents.ingest_file(req.path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    return {"chunks": n_chunks}


@app.get("/api/documents")
def list_documents():
    return {"sources": alfred.documents.list_sources()}


@app.post("/api/documents/summarize")
def summarize_document(req: IngestRequest):
    summary = alfred.summarize_document(req.path)
    return {"summary": summary}


# --- Tools: tasks / reminders / notes -------------------------------------------

class TaskRequest(BaseModel):
    content: str


@app.get("/api/tasks")
def list_tasks():
    return {"tasks": alfred.tools.list_tasks()}


@app.post("/api/tasks")
def add_task(req: TaskRequest):
    return {"id": alfred.tools.add_task(req.content)}


@app.post("/api/tasks/{task_id}/complete")
def complete_task(task_id: str):
    ok = alfred.tools.complete_task(task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"ok": True}


class NoteRequest(BaseModel):
    title: str = ""
    content: str


@app.get("/api/notes")
def list_notes():
    return {"notes": alfred.tools.list_notes()}


@app.post("/api/notes")
def add_note(req: NoteRequest):
    return {"id": alfred.tools.add_note(req.content, req.title)}


# --- Voice: speech-to-text / text-to-speech, both fully local ------------------

@app.post("/api/voice/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """Accepts a recorded audio clip (webm/ogg/wav from the browser's
    MediaRecorder) and returns the transcribed text. Runs entirely locally
    via faster-whisper — the audio bytes never leave this machine."""
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio upload")
    suffix = Path(audio.filename or "clip.webm").suffix or ".webm"
    try:
        text = stt.transcribe(audio_bytes, suffix=suffix)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}")
    return {"text": text}


class SpeakRequest(BaseModel):
    text: str


@app.post("/api/voice/speak")
def speak_text(req: SpeakRequest):
    """Renders text to speech locally (OS voice engine via pyttsx3) and
    returns WAV audio bytes for the browser to play."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="No text to speak")
    try:
        wav_bytes = tts.speak_to_wav(req.text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Speech synthesis failed: {exc}")
    return Response(content=wav_bytes, media_type="audio/wav")
