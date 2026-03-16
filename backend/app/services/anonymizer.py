from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Iterable, List, Tuple

from loguru import logger

from app.core.config import settings
from app.core.llm import extract_first_json_object, get_llm_client
from app.core.policies import apply_blacklist, apply_whitelist
from app.detectors.context import is_address_context
from app.detectors.name_ner import NameDetector
from app.detectors.validators import ValidatorDetector
from app.schemas.options import AnonymizeOptions


@dataclass(frozen=True)
class SpanEntity:
    start: int
    end: int
    label: str


_NAME_DETECTOR: NameDetector | None = None
_VALIDATOR_DETECTOR: ValidatorDetector | None = None


def _get_name_detector() -> NameDetector:
    global _NAME_DETECTOR
    if _NAME_DETECTOR is None:
        _NAME_DETECTOR = NameDetector()
    return _NAME_DETECTOR


def _get_validator_detector() -> ValidatorDetector:
    global _VALIDATOR_DETECTOR
    if _VALIDATOR_DETECTOR is None:
        _VALIDATOR_DETECTOR = ValidatorDetector()
    return _VALIDATOR_DETECTOR


def highlight_placeholders(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(
        r"(\[(?:ФИО|ПАСПОРТ|ДАТА РОЖДЕНИЯ|СНИЛС/ИНН|ТЕЛЕФОН|СЧЕТ/РЕКВИЗИТЫ|EMAIL|АДРЕС)(?:-\d+)?\])",
        r"<mark class='mask'>\1</mark>",
        escaped,
    )
    return escaped.replace("\n", "<br>")


def _collect_ner_spans(text: str, options: AnonymizeOptions) -> List[SpanEntity]:
    if not options.fio:
        return []
    det = _get_name_detector()
    spans: List[SpanEntity] = []
    for ent in det.detect(text):
        if is_address_context(text, ent):
            continue
        spans.append(SpanEntity(start=ent.start, end=ent.end, label=ent.label))
    return spans


def _collect_validator_spans(text: str, options: AnonymizeOptions) -> List[SpanEntity]:
    det = _get_validator_detector()
    spans: List[SpanEntity] = []
    for ent in det.detect(text):
        if ent.label == "[ПАСПОРТ]" and not options.passport:
            continue
        if ent.label == "[ДАТА РОЖДЕНИЯ]" and not options.birthdate:
            continue
        if ent.label == "[СНИЛС/ИНН]" and not options.snils_inn:
            continue
        if ent.label == "[ТЕЛЕФОН]" and not options.phone:
            continue
        if ent.label == "[СЧЕТ/РЕКВИЗИТЫ]" and not options.banking:
            continue
        spans.append(SpanEntity(start=ent.start, end=ent.end, label=ent.label))
    return spans


def _merge_spans(spans: Iterable[SpanEntity]) -> List[SpanEntity]:
    sorted_spans = sorted(spans, key=lambda s: (s.start, -(s.end - s.start)))
    merged: List[SpanEntity] = []
    for span in sorted_spans:
        if not merged:
            merged.append(span)
            continue
        last = merged[-1]
        if span.start >= last.end:
            merged.append(span)
            continue
        if (span.end - span.start) > (last.end - last.start):
            merged[-1] = span
    return merged


def replace_spans(text: str, spans: List[SpanEntity]) -> str:
    if not spans:
        return text
    result = text
    for span in sorted(spans, key=lambda s: s.start, reverse=True):
        result = result[: span.start] + span.label + result[span.end :]
    return result


def _build_llm_prompt(text: str) -> str:
    return (
        "Ты помогаешь анонимизировать текст. В тексте уже могут быть плейсхолдеры вида [ФИО-1], "
        "[СНИЛС/ИНН-2], [СЧЕТ/РЕКВИЗИТЫ-3] и т.п. Найди оставшиеся персональные данные "
        "(ФИО, адреса, телефоны, e-mail, ИНН, СНИЛС, ОГРН, ОГРНИП, КПП, БИК, номера счетов, паспорта, даты рождения). "
        "Верни ТОЛЬКО JSON вида: {\"items\":[{\"text\":\"...\",\"label\":\"[ФИО]\"|\"[СНИЛС/ИНН]\"|\"[СЧЕТ/РЕКВИЗИТЫ]\"|"
        "\"[ТЕЛЕФОН]\"|\"[ПАСПОРТ]\"|\"[ДАТА РОЖДЕНИЯ]\"|\"[EMAIL]\"|\"[АДРЕС]\"}]}. "
        "В поле text используй точные подстроки из входного текста. "
        "Не включай в ответ подстроки, которые уже содержат '[' или ']'. "
        "Если ничего не найдено, верни {\"items\":[]}.\n\n"
        f"ТЕКСТ:\n{text}"
    )


def _find_llm_spans(
    text: str,
    chunk_start: int,
    items: list[dict],
    options: AnonymizeOptions,
) -> List[SpanEntity]:
    spans: List[SpanEntity] = []
    for item in items:
        label = item.get("label")
        value = item.get("text")
        if not isinstance(label, str) or not isinstance(value, str):
            continue
        if "[" in value or "]" in value:
            continue
        if label not in {"[ФИО]", "[СНИЛС/ИНН]", "[СЧЕТ/РЕКВИЗИТЫ]", "[ТЕЛЕФОН]", "[ПАСПОРТ]", "[ДАТА РОЖДЕНИЯ]", "[EMAIL]", "[АДРЕС]"}:
            continue
        if label == "[ФИО]" and not options.fio:
            continue
        if label == "[СНИЛС/ИНН]" and not options.snils_inn:
            continue
        if label == "[СЧЕТ/РЕКВИЗИТЫ]" and not options.banking:
            continue
        if label == "[ТЕЛЕФОН]" and not options.phone:
            continue
        if label == "[ПАСПОРТ]" and not options.passport:
            continue
        if label == "[ДАТА РОЖДЕНИЯ]" and not options.birthdate:
            continue
        if not value.strip():
            continue
        for m in re.finditer(re.escape(value), text):
            start, end = m.span()
            if "[" in text[start:end] or "]" in text[start:end]:
                continue
            spans.append(SpanEntity(start=chunk_start + start, end=chunk_start + end, label=label))
    return spans


def _apply_llm_post_check(text: str, options: AnonymizeOptions) -> str:
    if not settings.llm_enabled or settings.llm_provider == "off":
        return text
    client = get_llm_client()
    chunk_size = max(500, settings.llm_chunk_size)
    overlap = 200
    spans: List[SpanEntity] = []
    start = 0
    logger.info("LLM post-check enabled (provider={}, model={})", settings.llm_provider, settings.ollama_model)
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunk = text[start:end]
        prompt = _build_llm_prompt(chunk)
        response = client.anonymize_text(prompt)
        data = extract_first_json_object(response or "")
        items = data.get("items") if isinstance(data, dict) else None
        if isinstance(items, list):
            logger.info("LLM post-check items found: {}", len(items))
            spans.extend(_find_llm_spans(chunk, start, items, options))
        if end == len(text):
            break
        start = end - overlap
        if start < 0:
            start = 0
    spans = _merge_spans(spans)
    spans = apply_plain_placeholders(spans)
    return replace_spans(text, spans)


def detect_spans_with_llm(text: str, options: AnonymizeOptions) -> List[SpanEntity]:
    spans = detect_spans(text, options)
    if not settings.llm_enabled or settings.llm_provider == "off":
        return spans
    client = get_llm_client()
    chunk_size = max(500, settings.llm_chunk_size)
    overlap = 200
    start = 0
    logger.info("LLM span detection enabled (provider={}, model={})", settings.llm_provider, settings.ollama_model)
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunk = text[start:end]
        prompt = _build_llm_prompt(chunk)
        response = client.anonymize_text(prompt)
        data = extract_first_json_object(response or "")
        items = data.get("items") if isinstance(data, dict) else None
        if isinstance(items, list):
            logger.info("LLM span detection items found: {}", len(items))
            spans.extend(_find_llm_spans(chunk, start, items, options))
        if end == len(text):
            break
        start = end - overlap
        if start < 0:
            start = 0
    return _merge_spans(spans)


def _normalize_key_for_span(text: str, span: SpanEntity) -> str:
    raw = text[span.start:span.end]
    label = span.label
    if label == "[ФИО]":
        words = re.findall(r"[А-ЯЁа-яё]+", raw)
        if not words:
            return re.sub(r"\W+", "", raw).lower()
        surname = words[0].lower()
        first_initial = words[1][0].lower() if len(words) > 1 else ""
        return f"{surname}:{first_initial}"
    if label in {"[ТЕЛЕФОН]", "[ПАСПОРТ]", "[СНИЛС/ИНН]", "[СЧЕТ/РЕКВИЗИТЫ]"}:
        digits = re.sub(r"\D+", "", raw)
        return digits or raw.lower()
    if label == "[ДАТА РОЖДЕНИЯ]":
        digits = re.sub(r"\D+", "", raw)
        return digits or raw.lower()
    return raw.lower()


def apply_numbered_placeholders_with_state(
    text: str,
    spans: List[SpanEntity],
    counters: dict[str, int],
    keys: dict[tuple[str, str], int],
) -> List[SpanEntity]:
    numbered: List[SpanEntity] = []
    for span in spans:
        base = span.label
        key = _normalize_key_for_span(text, span)
        map_key = (base, key)
        if map_key not in keys:
            counters[base] = counters.get(base, 0) + 1
            keys[map_key] = counters[base]
        idx = keys[map_key]
        numbered.append(SpanEntity(start=span.start, end=span.end, label=f"{base[:-1]}-{idx}]"))
    return numbered


def apply_numbered_placeholders(text: str, spans: List[SpanEntity]) -> List[SpanEntity]:
    return apply_numbered_placeholders_with_state(text, spans, {}, {})


def apply_plain_placeholders(spans: List[SpanEntity]) -> List[SpanEntity]:
    return [SpanEntity(start=s.start, end=s.end, label=s.label) for s in spans]


def detect_spans(text: str, options: AnonymizeOptions) -> List[SpanEntity]:
    spans = _merge_spans(_collect_ner_spans(text, options) + _collect_validator_spans(text, options))
    spans = apply_whitelist(spans, text)
    spans, extra = apply_blacklist(spans, text)
    spans = spans + [SpanEntity(start=s, end=e, label=label) for s, e, label in extra]
    return _merge_spans(spans)


def anonymize_text_no_llm(text: str, options: AnonymizeOptions) -> str:
    spans = detect_spans(text, options)
    spans = apply_plain_placeholders(spans)
    return replace_spans(text, spans)


def anonymize_text_value(text: str, options: AnonymizeOptions, prefer_llm: bool = True) -> str:
    if not text:
        return text

    anonymized = anonymize_text_no_llm(text, options)
    if prefer_llm:
        return _apply_llm_post_check(anonymized, options)
    return anonymized


def text_response_for_ui(source_text: str, options: AnonymizeOptions) -> tuple[str, str]:
    anonymized = anonymize_text_no_llm(source_text, options)
    return anonymized, highlight_placeholders(anonymized)
