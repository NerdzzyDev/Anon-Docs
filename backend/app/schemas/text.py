from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.options import AnonymizeOptions


class TextAnonymizeRequest(BaseModel):
    text: str = Field(..., min_length=1)
    options: AnonymizeOptions


class TextAnonymizeResponse(BaseModel):
    anonymized_text: str
    highlighted_html: str
    result_path: str
