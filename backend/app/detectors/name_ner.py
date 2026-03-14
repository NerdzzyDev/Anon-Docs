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
        patterns: list[tuple[re.Pattern[str], int]] = [
            # ИП / Индивидуальный предприниматель + ФИО (берем только ФИО)
            (re.compile(r"\b(?:ИП|ИНДИВИДУАЛЬНЫЙ\s+ПРЕДПРИНИМАТЕЛЬ)\s+([А-ЯЁ]{2,}\s+[А-ЯЁ]{2,}\s+[А-ЯЁ]{2,})\b", re.IGNORECASE), 1),
            (re.compile(r"\b(?:ИП|ИНДИВИДУАЛЬНЫЙ\s+ПРЕДПРИНИМАТЕЛЬ)\s+([А-ЯЁ]{2,}\s+[А-ЯЁ]{2,})\b", re.IGNORECASE), 1),
            # ФИО в верхнем регистре
            (re.compile(r"\b[А-ЯЁ]{2,}\s+[А-ЯЁ]{2,}\s+[А-ЯЁ]{2,}\b"), 0),
            (re.compile(r"\b[А-ЯЁ]{2,}\s+[А-ЯЁ]{2,}\b"), 0),
            # Иванов Иван Иванович
            (re.compile(r"\b[А-ЯЁ][а-яё-]{2,}\s+[А-ЯЁ][а-яё-]{2,}\s+[А-ЯЁ][а-яё-]{2,}\b"), 0),
            # Иванов Иван
            (re.compile(r"\b[А-ЯЁ][а-яё-]{2,}\s+[А-ЯЁ][а-яё-]{2,}\b"), 0),
            # Иван Иванович (имя + отчество с типичным окончанием)
            (re.compile(r"\b[А-ЯЁ][а-яё-]{2,}\s+[А-ЯЁ][а-яё-]{2,}(?:вич|вна)\b"), 0),
            # Имя Отчество (широкое правило)
            (re.compile(r"\b[А-ЯЁ][а-яё-]{2,}\s+[А-ЯЁ][а-яё-]{3,}\b"), 0),
            # Иванов И.В. / Иванов И. В. / Иванов И.В
            (re.compile(r"\b[А-ЯЁ][а-яё-]{2,}\s+[А-ЯЁ]\.\s*[А-ЯЁ]\.?(?![А-ЯЁ])"), 0),
            # Иванов И В
            (re.compile(r"\b[А-ЯЁ][а-яё-]{2,}\s+[А-ЯЁ]\s+[А-ЯЁ]\b"), 0),
            # Иванов И. (только если нет второго инициала)
            (re.compile(r"\b[А-ЯЁ][а-яё-]{2,}\s+[А-ЯЁ]\.(?!\s*[А-ЯЁ]\.)"), 0),
            # И.В. Иванов / И. В. Иванов
            (re.compile(r"\b[А-ЯЁ]\.\s*[А-ЯЁ]\.\s*[А-ЯЁ][а-яё-]{2,}\b"), 0),
            # И В Иванов
            (re.compile(r"\b[А-ЯЁ]\s+[А-ЯЁ]\s+[А-ЯЁ][а-яё-]{2,}\b"), 0),
            # И. Иванов (только если нет второго инициала)
            (re.compile(r"\b[А-ЯЁ]\.\s*[А-ЯЁ][а-яё-]{2,}\b"), 0),
            # ИП "Иванов И.В." или ИП Иванов И.В.
            (re.compile(r"\bИП\s+\"?[А-ЯЁ][а-яё-]{2,}\s+[А-ЯЁ]\.\s*[А-ЯЁ]\.?\"?\b"), 0),
            # ИП Иванов Иван Иванович
            (re.compile(r"\bИП\s+\"?[А-ЯЁ][а-яё-]{2,}\s+[А-ЯЁ][а-яё-]{2,}\s+[А-ЯЁ][а-яё-]{2,}\"?\b"), 0),
            # г-н / гражданин / гражданка
            (re.compile(r"\b(г-н|г-жа|гражданин|гражданка)\s+[А-ЯЁ][а-яё-]{2,}(?:\s+[А-ЯЁ][а-яё-]{2,}){0,2}\b", re.IGNORECASE), 0),
            # г-н Иванов И.И.
            (re.compile(r"\b(г-н|г-жа|гражданин|гражданка)\s+[А-ЯЁ][а-яё-]{2,}\s+[А-ЯЁ]\.\s*[А-ЯЁ]\.?\b", re.IGNORECASE), 0),
            # директор / руководитель / подписант / представитель
            (re.compile(r"\b(директор|руководитель|подписант|представитель)\s+[А-ЯЁ][а-яё-]{2,}(?:\s+[А-ЯЁ][а-яё-]{2,}){0,2}\b", re.IGNORECASE), 0),
            # директор Иванов И.И.
            (re.compile(r"\b(директор|руководитель|подписант|представитель)\s+[А-ЯЁ][а-яё-]{2,}\s+[А-ЯЁ]\.\s*[А-ЯЁ]\.?\b", re.IGNORECASE), 0),
            # в лице / действующий через
            (re.compile(r"\b(в\s+лице|действующ(?:ий|ая)\s+через)\s+[А-ЯЁ][а-яё-]{2,}(?:\s+[А-ЯЁ][а-яё-]{2,}){0,2}\b", re.IGNORECASE), 0),
            # в лице Иванов И.И.
            (re.compile(r"\b(в\s+лице|действующ(?:ий|ая)\s+через)\s+[А-ЯЁ][а-яё-]{2,}\s+[А-ЯЁ]\.\s*[А-ЯЁ]\.?\b", re.IGNORECASE), 0),
        ]

        spans: List[DetectedSpan] = []
        for pattern, group in patterns:
            for match in pattern.finditer(text):
                start, end = match.span(group)
                value = text[start:end]
                if self._is_initials_only(value):
                    continue
                if self._is_non_person_phrase(value):
                    continue
                spans.append(
                    DetectedSpan(
                        start=start,
                        end=end,
                        label="[ФИО]",
                        text=value,
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

    def _is_initials_only(self, value: str) -> bool:
        short = re.sub(r"\s+", "", value)
        return bool(re.fullmatch(r"[А-ЯЁ]\.[А-ЯЁ]\.?", short))

    def _is_non_person_phrase(self, value: str) -> bool:
        tokens = re.findall(r"[А-ЯЁа-яё]+", value)
        if not tokens:
            return False
        upper_tokens = {t.upper() for t in tokens}
        # Организационно-правовые формы и банковские/реквизитные маркеры
        stop = {
            "ПАО",
            "АО",
            "ООО",
            "ОАО",
            "ЗАО",
            "ИП",
            "НКО",
            "БАНК",
            "СБЕРБАНК",
            "ИНН",
            "ОГРН",
            "ОГРНИП",
            "КПП",
            "БИК",
            "КОРСЧЕТ",
            "КОРСЧЁТ",
            "КОРРСЧЕТ",
            "КОРРСЧЁТ",
            "СЧЕТ",
            "СЧЁТ",
            "РАСЧЕТНЫЙ",
            "РАСЧЁТНЫЙ",
            "КОРРЕСПОНДЕНТСКИЙ",
        }
        return bool(upper_tokens & stop)
