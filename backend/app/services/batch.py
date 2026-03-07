from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class BatchItem:
    filename: str
    result: Optional[dict] = None
    error: Optional[str] = None


@dataclass
class BatchJob:
    job_id: str
    total: int
    processed: int = 0
    status: str = "processing"
    items: List[BatchItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "status": self.status,
            "total": self.total,
            "processed": self.processed,
            "progress": int((self.processed / self.total) * 100) if self.total else 0,
            "items": [
                {
                    "filename": item.filename,
                    "result": item.result,
                    "error": item.error,
                }
                for item in self.items
            ],
        }


class BatchStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: Dict[str, BatchJob] = {}

    def create(self, job: BatchJob) -> None:
        with self._lock:
            self._jobs[job.job_id] = job

    def get(self, job_id: str) -> Optional[BatchJob]:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, **kwargs) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            for key, value in kwargs.items():
                setattr(job, key, value)

    def append_item(self, job_id: str, item: BatchItem) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            job.items.append(item)

    def increment_processed(self, job_id: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            job.processed += 1


batch_store = BatchStore()
