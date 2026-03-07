from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DomainError(Exception):
    message: str
    status_code: int = 400
    details: str | None = None

    def to_dict(self) -> dict:
        payload = {"detail": self.message}
        if self.details:
            payload["details"] = self.details
        return payload
