from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Tuple

from app.detectors.base import DetectedSpan


@dataclass(frozen=True)
class ValidatorRule:
    regex: re.Pattern
    label: str
    group: int = 0


class ValidatorDetector:
    name = "validators"
    supported_labels = ["[ПАСПОРТ]", "[ДАТА РОЖДЕНИЯ]", "[СНИЛС/ИНН]", "[ТЕЛЕФОН]", "[СЧЕТ/РЕКВИЗИТЫ]"]

    def __init__(self) -> None:
        self.rules: List[ValidatorRule] = [
            # Паспорт
            ValidatorRule(re.compile(r"\bпаспорт(?:ные\s+данные)?\s*(?:рф)?\s*[:№]?\s*(\d{4}\s?\d{6})\b", re.IGNORECASE), "[ПАСПОРТ]", 1),
            ValidatorRule(re.compile(r"\b\d{4}\s\d{6}\b"), "[ПАСПОРТ]", 0),
            # Дата рождения (только в контексте)
            ValidatorRule(re.compile(r"\bдата\s+рождения\s*[:\-]?\s*(\d{1,2}[./-]\d{1,2}[./-]\d{4})\b", re.IGNORECASE), "[ДАТА РОЖДЕНИЯ]", 1),
            ValidatorRule(re.compile(r"\bдата\s+рождения\s*[:\-]?\s*(\d{1,2}\s+(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+\d{4})\b", re.IGNORECASE), "[ДАТА РОЖДЕНИЯ]", 1),
            ValidatorRule(re.compile(r"\b(?:родился|родилась)\s*[:\-]?\s*(\d{1,2}[./-]\d{1,2}[./-]\d{4})\b", re.IGNORECASE), "[ДАТА РОЖДЕНИЯ]", 1),
            ValidatorRule(re.compile(r"\b(?:родился|родилась)\s*[:\-]?\s*(\d{1,2}\s+(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+\d{4})\b", re.IGNORECASE), "[ДАТА РОЖДЕНИЯ]", 1),
            ValidatorRule(re.compile(r"\bд/р\s*[:\-]?\s*(\d{1,2}[./-]\d{1,2}[./-]\d{4})\b", re.IGNORECASE), "[ДАТА РОЖДЕНИЯ]", 1),
            ValidatorRule(re.compile(r"\bдата\s+рождения\s*[:\-]?\s*(\d{4}-\d{2}-\d{2})\b", re.IGNORECASE), "[ДАТА РОЖДЕНИЯ]", 1),
            # СНИЛС / ИНН
            ValidatorRule(re.compile(r"\bснилс\s*[:№]?\s*(\d{3}-\d{3}-\d{3}\s?\d{2})\b", re.IGNORECASE), "[СНИЛС/ИНН]", 1),
            ValidatorRule(re.compile(r"\b\d{3}-\d{3}-\d{3}\s?\d{2}\b"), "[СНИЛС/ИНН]", 0),
            ValidatorRule(re.compile(r"\bинн(?:\s+(?:банка|организации|юр\.?\s*лица|юридического\s+лица))?\s*[:№]?\s*(\d{10,12})\b", re.IGNORECASE), "[СНИЛС/ИНН]", 1),
            ValidatorRule(re.compile(r"\bинн\s*[:№]?\s*(\d{2}[- ]?\d{2}[- ]?\d{2}[- ]?\d{2}[- ]?\d{2}[- ]?\d{2})\b", re.IGNORECASE), "[СНИЛС/ИНН]", 1),
            ValidatorRule(re.compile(r"\bснилс\s*[:№]?\s*(\d{11})\b", re.IGNORECASE), "[СНИЛС/ИНН]", 1),
            # ОГРН / ОГРНИП
            ValidatorRule(re.compile(r"\bогрнип\s*[:№]?\s*(\d{15})\b", re.IGNORECASE), "[СНИЛС/ИНН]", 1),
            ValidatorRule(re.compile(r"\bогрн\s*[:№]?\s*(\d{13})\b", re.IGNORECASE), "[СНИЛС/ИНН]", 1),
            # КПП
            ValidatorRule(re.compile(r"\bкпп(?:\s+банка)?\s*[:№]?\s*(\d{9})\b", re.IGNORECASE), "[СЧЕТ/РЕКВИЗИТЫ]", 1),
            # Телефон
            ValidatorRule(re.compile(r"(?<!\d)(?:\+7|7|8)[\s-]?\(?\d{3}\)?\s?\d{3}[-\s]?\d{2}[-\s]?\d{2}(?!\d)"), "[ТЕЛЕФОН]", 0),
            # Счета/реквизиты
            ValidatorRule(re.compile(r"\b(?:р/с|расч[её]тный\s+сч[её]т)\s*[:№]?\s*(\d{20})\b", re.IGNORECASE), "[СЧЕТ/РЕКВИЗИТЫ]", 1),
            ValidatorRule(re.compile(r"\b(?:к/с|корр(?:еспондентский)?\s+сч[её]т)\s*[:№]?\s*(\d{20})\b", re.IGNORECASE), "[СЧЕТ/РЕКВИЗИТЫ]", 1),
            ValidatorRule(re.compile(r"\b(?:корсч[её]т|кор\.?\s*сч[её]т)\s*[:№]?\s*(\d{20})\b", re.IGNORECASE), "[СЧЕТ/РЕКВИЗИТЫ]", 1),
            ValidatorRule(re.compile(r"\bсч[её]т\s*[:№]?\s*(\d{20})\b", re.IGNORECASE), "[СЧЕТ/РЕКВИЗИТЫ]", 1),
            ValidatorRule(re.compile(r"\bБИК(?:\s+банка)?\s*[:№]?\s*(\d{9})\b", re.IGNORECASE), "[СЧЕТ/РЕКВИЗИТЫ]", 1),
            ValidatorRule(re.compile(r"\b([A-Z]{2}\d{2}[A-Z0-9]{10,30})\b"), "[СЧЕТ/РЕКВИЗИТЫ]", 1),
            ValidatorRule(re.compile(r"\b(\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4})\b"), "[СЧЕТ/РЕКВИЗИТЫ]", 1),
        ]

    def detect(self, text: str) -> List[DetectedSpan]:
        spans: List[DetectedSpan] = []
        for rule in self.rules:
            for m in rule.regex.finditer(text):
                start, end = m.span(rule.group)
                if start == end:
                    continue
                spans.append(DetectedSpan(start=start, end=end, label=rule.label, text=text[start:end]))
        return spans
