from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import date
from typing import Dict

from app.core.config import settings


@dataclass
class DailyCount:
    day: date
    count: int


class SessionLimiter:
    def __init__(self, max_per_day: int = 10) -> None:
        self.max_per_day = max_per_day
        self._lock = threading.Lock()
        self._counts: Dict[str, DailyCount] = {}

    def check_and_increment(self, session_id: str, increment: int) -> bool:
        today = date.today()
        with self._lock:
            record = self._counts.get(session_id)
            if record is None or record.day != today:
                record = DailyCount(day=today, count=0)
                self._counts[session_id] = record
            if record.count + increment > self.max_per_day:
                return False
            record.count += increment
            return True

    def remaining(self, session_id: str) -> int:
        today = date.today()
        with self._lock:
            record = self._counts.get(session_id)
            if record is None or record.day != today:
                return self.max_per_day
            return max(0, self.max_per_day - record.count)


session_limiter = SessionLimiter(max_per_day=10)


def is_unlimited(request) -> bool:
    token = settings.desktop_unlimited_token
    if not token:
        return False
    header = request.headers.get("X-Desktop-Token")
    return bool(header and header == token)
