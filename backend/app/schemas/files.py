from __future__ import annotations

from typing import List

from pydantic import BaseModel


class FileAnonymizeResponse(BaseModel):
    result_path: str
    download_url: str
    output_filename: str
    preview_html: str
    preview_text: str
    warnings: List[str] = []


class FileBatchResponse(BaseModel):
    items: List[FileAnonymizeResponse]


class BatchItem(BaseModel):
    filename: str
    result: FileAnonymizeResponse | None = None
    error: str | None = None


class BatchJobCreateResponse(BaseModel):
    job_id: str
    status: str
    total: int


class BatchJobStatusResponse(BaseModel):
    job_id: str
    status: str
    total: int
    processed: int
    progress: int
    items: List[BatchItem]
