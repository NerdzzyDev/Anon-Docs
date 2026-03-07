from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Tuple
import uuid

from fastapi import HTTPException, UploadFile


def save_result_text(text: str, results_dir: Path) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = results_dir / f"anonymized_{ts}.txt"
    path.write_text(text, encoding="utf-8")
    return str(path)


def save_uploaded_file(upload: UploadFile, uploads_dir: Path, max_upload_size_mb: int) -> Path:
    suffix = Path(upload.filename or "upload.bin").suffix
    name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{suffix}"
    target = uploads_dir / name
    size = 0
    with target.open("wb") as f:
        while True:
            chunk = upload.file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > max_upload_size_mb * 1024 * 1024:
                f.close()
                target.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail=f"Файл слишком большой (> {max_upload_size_mb} MB)")
            f.write(chunk)
    return target


def build_output_name(original_name: str) -> Tuple[str, str]:
    stem = Path(original_name).stem or "document"
    out_base = f"{stem}_anon_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    suffix = Path(original_name).suffix.lower()
    return out_base, suffix
