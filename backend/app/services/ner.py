from __future__ import annotations

from dataclasses import dataclass
from typing import List

from natasha import Doc, MorphVocab, NewsEmbedding, NewsNERTagger, Segmenter


@dataclass(frozen=True)
class DetectedSpan:
    start: int
    end: int
    label: str
    text: str


class NatashaNER:
    def __init__(self) -> None:
        self.segmenter = Segmenter()
        self.morph_vocab = MorphVocab()
        self.emb = NewsEmbedding()
        self.ner_tagger = NewsNERTagger(self.emb)

    def extract(self, text: str) -> List[DetectedSpan]:
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
        return entities
