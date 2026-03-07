from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from app.detectors.base import DetectedSpan


@dataclass(frozen=True)
class ContextRule:
    name: str
    pattern: re.Pattern


ADDRESS_RULES: List[ContextRule] = [
    ContextRule(
        name="street_context",
        pattern=re.compile(r"\b(улица|ул\.|проспект|пр-т|бульвар|бул\.|площадь|пл\.|проезд|пер\.|шоссе)\s+[А-ЯЁ][а-яё]+\b", re.IGNORECASE),
    ),
    ContextRule(
        name="on_street",
        pattern=re.compile(r"\bна\s+[А-ЯЁ][а-яё]+\s+(улице|проспекте|бульваре|площади)\b", re.IGNORECASE),
    ),
    ContextRule(
        name="address_house",
        pattern=re.compile(r"\b(дом|д\.|кв\.|квартира|офис|оф\.)\s*\d+\b", re.IGNORECASE),
    ),
]


def is_address_context(text: str, span: DetectedSpan, window: int = 50) -> bool:
    start = max(span.start - window, 0)
    end = min(span.end + window, len(text))
    context = text[start:end]
    return any(rule.pattern.search(context) for rule in ADDRESS_RULES)
