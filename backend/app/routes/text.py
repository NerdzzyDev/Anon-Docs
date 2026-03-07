from __future__ import annotations

from fastapi import APIRouter

from app.core.config import RESULTS_DIR
from app.schemas.text import TextAnonymizeRequest, TextAnonymizeResponse
from app.services.anonymizer import text_response_for_ui
from app.utils.io import save_result_text

router = APIRouter()


@router.post("/api/anonymize", response_model=TextAnonymizeResponse)
def anonymize_text(payload: TextAnonymizeRequest) -> TextAnonymizeResponse:
    anonymized_text, highlighted_html = text_response_for_ui(payload.text, payload.options)
    result_path = save_result_text(anonymized_text, RESULTS_DIR)
    return TextAnonymizeResponse(
        anonymized_text=anonymized_text,
        highlighted_html=highlighted_html,
        result_path=result_path,
    )
