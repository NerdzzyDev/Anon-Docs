from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Iterable, List, Tuple

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
        r"(\[(?:ФИО|ПАСПОРТ|ДАТА РОЖДЕНИЯ|СНИЛС/ИНН|ТЕЛЕФОН|СЧЕТ/РЕКВИЗИТЫ)(?:-\d+)?\])",
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


def detect_spans(text: str, options: AnonymizeOptions) -> List[SpanEntity]:
    spans = _merge_spans(_collect_ner_spans(text, options) + _collect_validator_spans(text, options))
    spans = apply_whitelist(spans, text)
    spans, extra = apply_blacklist(spans, text)
    spans = spans + [SpanEntity(start=s, end=e, label=label) for s, e, label in extra]
    return _merge_spans(spans)


def anonymize_text_no_llm(text: str, options: AnonymizeOptions) -> str:
    spans = detect_spans(text, options)
    spans = apply_numbered_placeholders(text, spans)
    return replace_spans(text, spans)


def anonymize_text_value(text: str, options: AnonymizeOptions, prefer_llm: bool = True) -> str:
    if not text:
        return text

    return anonymize_text_no_llm(text, options)


def text_response_for_ui(source_text: str, options: AnonymizeOptions) -> tuple[str, str]:
    anonymized = anonymize_text_no_llm(source_text, options)
    return anonymized, highlight_placeholders(anonymized)
