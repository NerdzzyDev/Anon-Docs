from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
APP_DIR = BASE_DIR / "app"
STATIC_DIR_FALLBACK = BASE_DIR / "static"
STATIC_DIR_REACT = BASE_DIR / "frontend" / "dist"
STATIC_DIR = STATIC_DIR_REACT if STATIC_DIR_REACT.exists() else STATIC_DIR_FALLBACK
RESULTS_DIR = Path(os.getenv("RESULTS_DIR", "/tmp/anon_docs_results"))
UPLOADS_DIR = RESULTS_DIR / "uploads"

load_dotenv(BASE_DIR / ".env", override=False)


@dataclass(frozen=True)
class Settings:
    llm_enabled: bool = os.getenv("LLM_ENABLED", "0") == "1"
    use_openai: bool = os.getenv("USE_OPENAI", "0") == "1"
    llm_provider: str = os.getenv("LLM_PROVIDER", "off")

    openai_model: str = os.getenv("OPENAI_MODEL", "o4-mini")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://openai.htk.ge/v1")
    openai_proxy: str = os.getenv("OPENAI_PROXY", "socks5h://127.0.0.1:2080")

    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3")

    llm_chunk_size: int = int(os.getenv("LLM_CHUNK_SIZE", "3500"))
    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "20"))

    pdf_font_path: str = os.getenv("PDF_FONT_PATH", "").strip()
    pdf_llm_assist: bool = os.getenv("PDF_LLM_ASSIST", "0") == "1"
    pdf_llm_max_chars: int = int(os.getenv("PDF_LLM_MAX_CHARS", "12000"))


settings = Settings()

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
