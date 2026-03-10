from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List

from natasha import Doc, MorphVocab, NewsEmbedding, NewsNERTagger, Segmenter

from app.detectors.base import DetectedSpan


class NameDetector:
    name = "natasha_per"
    supported_labels = ["[ФИО]"]

    def __init__(self) -> None:
        self.segmenter = Segmenter()
        self.morph_vocab = MorphVocab()
        self.emb = NewsEmbedding()
        self.ner_tagger = NewsNERTagger(self.emb)

    def detect(self, text: str) -> List[DetectedSpan]:
        doc = Doc(text)
        doc.segment(self.segmenter)
        doc.tag_ner(self.ner_tagger)

        entities: List[DetectedSpan] = []
        for span in doc.spans:
            span.normalize(self.morph_vocab)
            if span.type == "PER":
                entities.append(
                    DetectedSpan(
                        start=span.start,
                        end=span.stop,
                        label="[ФИО]",
                        text=text[span.start:span.stop],
                    )
                )

        entities.extend(self._regex_spans(text))
        return self._dedupe(entities)

    def _regex_spans(self, text: str) -> List[DetectedSpan]:
        patterns: list[re.Pattern[str]] = [
            # Иванов Иван Иванович
            re.compile(r"\b[А-ЯЁ][а-яё-]{2,}\s+[А-ЯЁ][а-яё-]{2,}\s+[А-ЯЁ][а-яё-]{2,}\b"),
            # Иванов Иван
            re.compile(r"\b[А-ЯЁ][а-яё-]{2,}\s+[А-ЯЁ][а-яё-]{2,}\b"),
            # Иван Иванович (имя + отчество с типичным окончанием)
            re.compile(r"\b[А-ЯЁ][а-яё-]{2,}\s+[А-ЯЁ][а-яё-]{2,}(?:вич|вна)\b"),
            # Имя Отчество (более широкое правило, чтобы ловить редкие окончания)
            re.compile(r"\b[А-ЯЁ][а-яё-]{2,}\s+[А-ЯЁ][а-яё-]{3,}\b"),
            # Иванов И.В. / Иванов И. В.
            re.compile(r"\b[А-ЯЁ][а-яё-]{2,}\s+[А-ЯЁ]\.\s*[А-ЯЁ]\.\b"),
            # Иванов И. / Иванов И
            re.compile(r"\b[А-ЯЁ][а-яё-]{2,}\s+[А-ЯЁ]\.?\b"),
            # И.В. Иванов / И. В. Иванов
            re.compile(r"\b[А-ЯЁ]\.\s*[А-ЯЁ]\.\s*[А-ЯЁ][а-яё-]{2,}\b"),
            # И. Иванов
            re.compile(r"\b[А-ЯЁ]\.\s*[А-ЯЁ][а-яё-]{2,}\b"),
            # ИП \"Иванов И.В.\" или ИП Иванов И.В.
            re.compile(r"\bИП\s+\"?[А-ЯЁ][а-яё-]{2,}\s+[А-ЯЁ]\.\s*[А-ЯЁ]\.?\"?\b"),
            # ИП Иванов Иван Иванович
            re.compile(r"\bИП\s+\"?[А-ЯЁ][а-яё-]{2,}\s+[А-ЯЁ][а-яё-]{2,}\s+[А-ЯЁ][а-яё-]{2,}\"?\b"),
            # г-н / гражданин / гражданка
            re.compile(r"\b(г-н|г-жа|гражданин|гражданка)\s+[А-ЯЁ][а-яё-]{2,}(?:\s+[А-ЯЁ][а-яё-]{2,}){0,2}\b", re.IGNORECASE),
            # менеджер / директор / подписант
            re.compile(r"\b(директор|руководитель|подписант|представитель)\s+[А-ЯЁ][а-яё-]{2,}(?:\s+[А-ЯЁ][а-яё-]{2,}){0,2}\b", re.IGNORECASE),
            # в лице / действующий через
            re.compile(r"\b(в\s+лице|действующ(?:ий|ая)\s+через)\s+[А-ЯЁ][а-яё-]{2,}(?:\s+[А-ЯЁ][а-яё-]{2,}){0,2}\b", re.IGNORECASE),
        ]

        spans: List[DetectedSpan] = []
        for pattern in patterns:
            for match in pattern.finditer(text):
                spans.append(
                    DetectedSpan(
                        start=match.start(),
                        end=match.end(),
                        label="[ФИО]",
                        text=text[match.start() : match.end()],
                    )
                )
        return spans

    def _dedupe(self, spans: Iterable[DetectedSpan]) -> List[DetectedSpan]:
        seen: set[tuple[int, int]] = set()
        unique: List[DetectedSpan] = []
        for span in spans:
            key = (span.start, span.end)
            if key in seen:
                continue
            seen.add(key)
            unique.append(span)
        return unique
