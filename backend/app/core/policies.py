from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Literal, Set

MatchType = Literal["exact", "contains", "regex"]


@dataclass(frozen=True)
class Rule:
    pattern: str
    match_type: MatchType
    labels: Set[str]
    priority: int

    def match(self, text: str) -> bool:
        if self.match_type == "exact":
            return text == self.pattern
        if self.match_type == "contains":
            return self.pattern in text
        if self.match_type == "regex":
            return re.search(self.pattern, text) is not None
        return False


WHITELIST: List[Rule] = []
BLACKLIST: List[Rule] = []


def apply_whitelist(spans, text: str):
    if not WHITELIST:
        return spans
    filtered = []
    for span in spans:
        value = text[span.start:span.end]
        if any(rule.match(value) and span.label in rule.labels for rule in WHITELIST):
            continue
        filtered.append(span)
    return filtered


def apply_blacklist(spans, text: str):
    extra = []
    if BLACKLIST:
        for rule in BLACKLIST:
            for m in re.finditer(rule.pattern, text):
                start, end = m.span(0)
                for label in rule.labels:
                    extra.append((start, end, label))
    return spans, extra
