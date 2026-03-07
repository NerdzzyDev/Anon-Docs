from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from openpyxl import load_workbook

from app.schemas.options import AnonymizeOptions
from app.services.anonymizer import anonymize_text_no_llm

try:
    from docx import Document  # type: ignore
except Exception:
    Document = None  # type: ignore


def _iter_docx_paragraphs(doc) -> List:
    paragraphs = list(doc.paragraphs)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                paragraphs.extend(cell.paragraphs)
    for section in getattr(doc, "sections", []):
        paragraphs.extend(section.header.paragraphs)
        paragraphs.extend(section.footer.paragraphs)
    return paragraphs


def process_docx_file(src: Path, dst: Path, options: AnonymizeOptions) -> Tuple[str, List[str]]:
    if Document is None:
        raise RuntimeError("python-docx не установлен")
    doc = Document(str(src))
    preview_parts: List[str] = []

    for paragraph in _iter_docx_paragraphs(doc):
        if not paragraph.runs:
            continue
        for run in paragraph.runs:
            if run.text:
                run.text = anonymize_text_no_llm(run.text, options)
        if paragraph.text:
            preview_parts.append(paragraph.text)

    doc.save(str(dst))
    return "\n".join(preview_parts[:20]), [
        "DOCX обработан с сохранением структуры документа. Если персональные данные разбиты по нескольким run-элементам, часть совпадений может потребовать доработки правил."
    ]


def process_xlsx_file(src: Path, dst: Path, options: AnonymizeOptions) -> Tuple[str, List[str]]:
    wb = load_workbook(str(src))
    preview_lines: List[str] = []

    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if isinstance(cell.value, str) and cell.value:
                    cell.value = anonymize_text_no_llm(cell.value, options)
                    if len(preview_lines) < 20:
                        preview_lines.append(f"[{ws.title}] {cell.coordinate}: {cell.value}")

    wb.save(str(dst))
    return "\n".join(preview_lines), []
