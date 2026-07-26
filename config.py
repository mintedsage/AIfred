"""
config.py — central configuration for Alfred.

Everything that other modules need to know about paths, default models,
and storage locations lives here so it's easy to audit or change in one place.
"""

from pathlib import Path

# --- Directories -----------------------------------------------------------
# Everything Alfred stores lives under DATA_DIR, on your own machine, always.
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

MEMORY_DB_PATH = DATA_DIR / "memory.db"
DOCUMENTS_DB_PATH = DATA_DIR / "documents.db"
TOOLS_DB_PATH = DATA_DIR / "tools.db"
KEY_FILE_PATH = DATA_DIR / "secret.key"

# --- Local LLM (Ollama) -----------------------------------------------------
# Ollama must be installed and running locally: https://ollama.com
# Pull a model once (e.g. `ollama pull llama3.1`) and Alfred works fully offline.
OLLAMA_HOST = "http://localhost:11434"
DEFAULT_MODEL = "llama3.1"
AVAILABLE_MODELS_FALLBACK = ["llama3.1", "mistral", "qwen2.5", "phi3"]

# --- Embeddings (for RAG) ---------------------------------------------------
# Downloaded once from Hugging Face on first run, cached locally, then offline.
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# --- Retrieval tuning --------------------------------------------------------
MEMORY_TOP_K = 4
DOCUMENT_TOP_K = 4
DOCUMENT_CHUNK_SIZE = 800       # characters per chunk
DOCUMENT_CHUNK_OVERLAP = 100

# --- Security ----------------------------------------------------------------
# If True, memory/document contents are encrypted at rest with a locally
# generated key (see core/security.py). The key never leaves your machine.
ENCRYPT_AT_REST = True

# --- UI ------------------------------------------------------------------
UI_HOST = "127.0.0.1"
UI_PORT = 8731

# --- Voice (STT/TTS) ---------------------------------------------------------
# Speech-to-text: faster-whisper, runs fully local. Model size trades off
# speed vs. accuracy: "tiny", "base", "small", "medium", "large-v3".
# "base" is a reasonable default for a laptop CPU.
STT_MODEL_SIZE = "base"
STT_DEVICE = "cpu"            # set to "cuda" if the user has a supported GPU
STT_COMPUTE_TYPE = "int8"     # int8 is fast and light on CPU; use "float16" on GPU

# Text-to-speech: pyttsx3, drives the OS's own built-in voice engine offline.
TTS_RATE = 175                # words per minute
TTS_VOLUME = 1.0              # 0.0 - 1.0
