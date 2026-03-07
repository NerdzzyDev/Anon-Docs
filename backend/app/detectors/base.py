from __future__ import annotations

from dataclasses import dataclass
from typing import List, Protocol


@dataclass(frozen=True)
class DetectedSpan:
    start: int
    end: int
    label: str
    text: str


class BaseDetector(Protocol):
    name: str
    supported_labels: List[str]

    def detect(self, text: str) -> List[DetectedSpan]: ...
