from __future__ import annotations

from decouple import config

LLM_MODEL = config("LLM_MODEL", default="qwen3")
LLM_TEMPERATURE = config("LLM_TEMPERATURE", default=0.0, cast=float)
OLLAMA_BASE_URL = config("OLLAMA_BASE_URL", default="http://localhost:11434/v1")
LLM_API_KEY = config("LLM_API_KEY", default="ollama")
