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
        return []

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
            "НАИМЕНОВАНИЕ",
            "ИНДИВИДУАЛЬНЫЙ",
            "ПРЕДПРИНИМАТЕЛЬ",
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
