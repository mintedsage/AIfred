"""
llm.py — the connection to Alfred's "brain": a locally running Ollama model.

No cloud API keys, no external calls. As long as `ollama serve` is running
locally and at least one model has been pulled, this works fully offline.
"""

from typing import Iterator
import ollama

from config import OLLAMA_HOST, DEFAULT_MODEL, AVAILABLE_MODELS_FALLBACK


class LLMClient:
    """Thin wrapper around the Ollama client that supports swapping models at runtime."""

    def __init__(self, model: str = DEFAULT_MODEL, host: str = OLLAMA_HOST):
        self.client = ollama.Client(host=host)
        self.model = model

    def set_model(self, model: str) -> None:
        self.model = model

    def list_models(self) -> list[str]:
        """Return the models currently pulled and available locally."""
        try:
            resp = self.client.list()
            models = [m["model"] for m in resp.get("models", [])]
            return models or AVAILABLE_MODELS_FALLBACK
        except Exception:
            # Ollama not reachable yet — surface a sane fallback instead of crashing the UI.
            return AVAILABLE_MODELS_FALLBACK

    def chat(self, messages: list[dict]) -> str:
        """Non-streaming chat completion. messages: [{"role": "...", "content": "..."}]"""
        response = self.client.chat(model=self.model, messages=messages, stream=False)
        return response["message"]["content"]

    def chat_with_tools(self, messages: list[dict], tools: list[dict]):
        """Chat completion that offers the model a set of callable tools
        (Ollama native tool-calling). Returns the raw message object, which
        may contain plain `content`, `tool_calls`, or both — the caller
        (agent.py) is responsible for executing any requested tool calls and
        feeding results back."""
        response = self.client.chat(model=self.model, messages=messages, tools=tools, stream=False)
        return response["message"]

    def chat_stream(self, messages: list[dict]) -> Iterator[str]:
        """Streaming chat completion, yields text chunks as they arrive."""
        stream = self.client.chat(model=self.model, messages=messages, stream=True)
        for chunk in stream:
            piece = chunk.get("message", {}).get("content", "")
            if piece:
                yield piece
