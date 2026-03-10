from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from app.core.config import RESULTS_DIR, UPLOADS_DIR, settings
from app.schemas.files import BatchJobCreateResponse, BatchJobStatusResponse, FileAnonymizeResponse, FileBatchResponse
from app.schemas.options import AnonymizeOptions
from app.services.anonymizer import anonymize_text_value, highlight_placeholders
from app.services.batch import BatchItem, BatchJob, batch_store
from app.services.limits import is_unlimited, session_limiter
from app.services.office import process_docx_file, process_xlsx_file
from app.services.pdf import safe_redact_pdf
from app.utils.io import build_output_name, save_uploaded_file

router = APIRouter()


def _parse_options_json(raw: str) -> AnonymizeOptions:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Некорректный JSON options: {exc}") from exc
    return AnonymizeOptions(**data)


def _process_text_like_file(src: Path, dst: Path, options: AnonymizeOptions) -> tuple[str, list[str]]:
    text = src.read_text(encoding="utf-8", errors="ignore")
    anonymized = anonymize_text_value(text, options, prefer_llm=False)
    dst.write_text(anonymized, encoding="utf-8")
    return anonymized[:8000], []


def _process_uploaded_file(src: Path, original_name: str, options: AnonymizeOptions) -> tuple[Path, str, list[str]]:
    out_base, suffix = build_output_name(original_name)

    if suffix in {".txt", ".csv", ".md", ".json", ".log"}:
        dst = RESULTS_DIR / f"{out_base}{suffix}"
        preview, warnings = _process_text_like_file(src, dst, options)
        return dst, preview, warnings

    if suffix == ".docx":
        dst = RESULTS_DIR / f"{out_base}.docx"
        preview, warnings = process_docx_file(src, dst, options)
        return dst, preview, warnings

    if suffix in {".xlsx", ".xlsm"}:
        dst = RESULTS_DIR / f"{out_base}{suffix}"
        preview, warnings = process_xlsx_file(src, dst, options)
        return dst, preview, warnings

    if suffix == ".pdf":
        dst = RESULTS_DIR / f"{out_base}.pdf"
        preview, warnings = safe_redact_pdf(src, dst, options)
        return dst, preview, warnings

    if suffix == ".doc":
        raise HTTPException(
            status_code=400,
            detail="Формат .doc (legacy Word) не поддерживается для сохранения форматирования. Конвертируйте в .docx.",
        )

    raise HTTPException(
        status_code=400,
        detail="Неподдерживаемый формат. Поддерживаются: txt/csv/md/json/log, docx, xlsx/xlsm, pdf.",
    )


def _build_file_response(output_path: Path, preview_text: str, warnings: list[str]) -> FileAnonymizeResponse:
    preview_html = highlight_placeholders(preview_text)
    return FileAnonymizeResponse(
        result_path=str(output_path),
        download_url=f"/api/download/{output_path.name}",
        output_filename=output_path.name,
        preview_html=preview_html,
        preview_text=preview_text,
        warnings=warnings,
    )


def _run_batch_job(job_id: str, files: list[tuple[Path, str]], options: AnonymizeOptions) -> None:
    job = batch_store.get(job_id)
    if not job:
        return
    for src_path, original_name in files:
        try:
            output_path, preview_text, warnings = _process_uploaded_file(src_path, original_name, options)
            result = _build_file_response(output_path, preview_text, warnings)
            batch_store.append_item(job_id, BatchItem(filename=original_name, result=result.model_dump()))
        except Exception as exc:
            batch_store.append_item(job_id, BatchItem(filename=original_name, error=str(exc)))
        finally:
            src_path.unlink(missing_ok=True)
        batch_store.increment_processed(job_id)
    batch_store.update(job_id, status="completed")


@router.post("/api/anonymize-file", response_model=FileAnonymizeResponse)
def anonymize_file(request: Request, file: UploadFile = File(...), options: str = Form(...)) -> FileAnonymizeResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Файл не выбран")

    session_id = getattr(request.state, "session_id", "anon")
    if not is_unlimited(request):
        if not session_limiter.check_and_increment(session_id, 1):
            raise HTTPException(status_code=429, detail="Дневной лимит 10 документов исчерпан")

    parsed_options = _parse_options_json(options)
    src_path = save_uploaded_file(file, UPLOADS_DIR, settings.max_upload_size_mb)
    try:
        output_path, preview_text, warnings = _process_uploaded_file(src_path, file.filename, parsed_options)
    finally:
        src_path.unlink(missing_ok=True)

    return _build_file_response(output_path, preview_text, warnings)


@router.post("/api/anonymize-files", response_model=FileBatchResponse)
def anonymize_files(request: Request, files: list[UploadFile] = File(...), options: str = Form(...)) -> FileBatchResponse:
    if not files:
        raise HTTPException(status_code=400, detail="Файлы не выбраны")
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="За один запрос можно обработать не более 5 файлов")

    session_id = getattr(request.state, "session_id", "anon")
    if not is_unlimited(request):
        if not session_limiter.check_and_increment(session_id, len(files)):
            raise HTTPException(status_code=429, detail="Дневной лимит 10 документов исчерпан")

    parsed_options = _parse_options_json(options)
    results: list[FileAnonymizeResponse] = []
    for file in files:
        if not file.filename:
            continue
        src_path = save_uploaded_file(file, UPLOADS_DIR, settings.max_upload_size_mb)
        try:
            output_path, preview_text, warnings = _process_uploaded_file(src_path, file.filename, parsed_options)
            results.append(_build_file_response(output_path, preview_text, warnings))
        finally:
            src_path.unlink(missing_ok=True)
    return FileBatchResponse(items=results)


@router.post("/api/anonymize-files-async", response_model=BatchJobCreateResponse)
def anonymize_files_async(
    request: Request,
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    options: str = Form(...),
) -> BatchJobCreateResponse:
    if not files:
        raise HTTPException(status_code=400, detail="Файлы не выбраны")
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="За один запрос можно обработать не более 5 файлов")

    session_id = getattr(request.state, "session_id", "anon")
    if not is_unlimited(request):
        if not session_limiter.check_and_increment(session_id, len(files)):
            raise HTTPException(status_code=429, detail="Дневной лимит 10 документов исчерпан")

    parsed_options = _parse_options_json(options)
    saved_files: list[tuple[Path, str]] = []
    for file in files:
        if not file.filename:
            continue
        src_path = save_uploaded_file(file, UPLOADS_DIR, settings.max_upload_size_mb)
        saved_files.append((src_path, file.filename))

    job = BatchJob(job_id=str(uuid4()), total=len(saved_files))
    batch_store.create(job)
    background_tasks.add_task(_run_batch_job, job.job_id, saved_files, parsed_options)
    return BatchJobCreateResponse(job_id=job.job_id, status=job.status, total=job.total)


@router.get("/api/batch/{job_id}", response_model=BatchJobStatusResponse)
def batch_status(job_id: str) -> BatchJobStatusResponse:
    job = batch_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Пакетная задача не найдена")
    return BatchJobStatusResponse(**job.to_dict())


@router.get("/api/download/{filename}")
def download_result(filename: str) -> FileResponse:
    safe_name = Path(filename).name
    path = RESULTS_DIR / safe_name
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Файл не найден")
    return FileResponse(path, filename=safe_name)
