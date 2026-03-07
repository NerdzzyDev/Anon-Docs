from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Protocol

import httpx

from app.core.config import settings

try:
    from openai import OpenAI  # type: ignore
except Exception:
    OpenAI = None  # type: ignore


class LLMClient(Protocol):
    def anonymize_text(self, prompt: str) -> str | None: ...


@dataclass
class OpenAIClient:
    def anonymize_text(self, prompt: str) -> str | None:
        if not (settings.use_openai and settings.openai_api_key and OpenAI):
            return None

        proxy_url = settings.openai_proxy
        if isinstance(proxy_url, str) and proxy_url.startswith("socks5h://"):
            proxy_url = "socks5://" + proxy_url[len("socks5h://"):]

        http_client = httpx.Client(proxies=proxy_url, timeout=90.0)
        client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url, http_client=http_client)
        try:
            if hasattr(client, "responses"):
                resp = client.responses.create(model=settings.openai_model, input=prompt)
                return getattr(resp, "output_text", None)
            resp = client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
            )
            if resp.choices:
                return resp.choices[0].message.content
        finally:
            try:
                http_client.close()
            except Exception:
                pass
        return None


@dataclass
class OllamaClient:
    def anonymize_text(self, prompt: str) -> str | None:
        try:
            with httpx.Client(timeout=90.0) as client:
                resp = client.post(
                    f"{settings.ollama_base_url}/api/generate",
                    json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("response")
        except Exception:
            return None


@dataclass
class NoopClient:
    def anonymize_text(self, prompt: str) -> str | None:
        return None


def get_llm_client() -> LLMClient:
    if settings.llm_provider == "ollama":
        return OllamaClient()
    if settings.llm_provider == "openai":
        return OpenAIClient()
    return NoopClient()


def extract_first_json_object(text: str) -> dict | None:
    if not text:
        return None
    text = text.strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None
