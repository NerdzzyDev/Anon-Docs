from __future__ import annotations

import ctypes
import glob
import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple

from loguru import logger

from app.core.config import settings
from app.core.errors import DomainError
from app.schemas.options import AnonymizeOptions
from app.services.anonymizer import anonymize_text_no_llm, apply_numbered_placeholders_with_state, detect_spans

try:
    import fitz  # type: ignore
except Exception:
    fitz = None  # type: ignore


def _prepare_libstdcpp_for_pymupdf() -> None:
    patterns = [
        "/nix/store/*/lib/libstdc++.so.6",
        "/nix/store/*/lib64/libstdc++.so.6",
        "/usr/lib*/libstdc++.so.6",
        "/lib*/libstdc++.so.6",
    ]
    candidates: List[str] = []
    seen: set[str] = set()
    for pattern in patterns:
        for p in glob.glob(pattern):
            if p not in seen:
                seen.add(p)
                candidates.append(p)
    for p in candidates:
        try:
            ctypes.CDLL(p, mode=getattr(ctypes, "RTLD_GLOBAL", 0))
            return
        except OSError:
            continue


_prepare_libstdcpp_for_pymupdf()
try:
    import fitz  # type: ignore
except Exception:
    fitz = None  # type: ignore


def _split_placeholder(placeholder: str) -> tuple[str, str]:
    match = re.match(r"^\[(.+?)(-\d+)?\]$", placeholder)
    if not match:
        return placeholder, ""
    base = f"[{match.group(1)}]"
    suffix = match.group(2) or ""
    return base, suffix


def _pdf_placeholder_text(placeholder: str, unicode_ok: bool) -> str:
    base, suffix = _split_placeholder(placeholder)
    return f"{base[:-1]}{suffix}]"


def _pdf_placeholder_variants(placeholder: str, unicode_ok: bool) -> List[str]:
    base, suffix = _split_placeholder(placeholder)
    compact = {
        "[ФИО]": "[ФИО]",
        "[ПАСПОРТ]": "[ПАСП.]",
        "[ДАТА РОЖДЕНИЯ]": "[ДР]",
        "[СНИЛС/ИНН]": "[ИНН/СН]",
        "[ТЕЛЕФОН]": "[ТЕЛ.]",
        "[СЧЕТ/РЕКВИЗИТЫ]": "[СЧЕТ]",
    }
    base_label = f"{base[:-1]}{suffix}]"
    alt = compact.get(base, base)
    alt = f"{alt[:-1]}{suffix}]" if suffix else alt
    return [base_label] if alt == base_label else [base_label, alt]


@dataclass(frozen=True)
class PdfPageStream:
    text: str
    words: List[tuple]
    spans: List[Tuple[int, int]]
    boxes: List[Tuple[float, float, float, float]]


def _build_pdf_word_stream(page) -> PdfPageStream:
    words = page.get_text("words") or []
    words = sorted(words, key=lambda w: (w[5], w[6], w[7], w[1], w[0]))
    text_parts: List[str] = []
    spans: List[Tuple[int, int]] = []
    boxes: List[Tuple[float, float, float, float]] = []
    cursor = 0
    for idx, w in enumerate(words):
        token = str(w[4])
        if idx:
            text_parts.append(" ")
            cursor += 1
        start = cursor
        text_parts.append(token)
        cursor += len(token)
        spans.append((start, cursor))
        boxes.append((float(w[0]), float(w[1]), float(w[2]), float(w[3])))
    return PdfPageStream("".join(text_parts), words, spans, boxes)


def _pdf_token_indexes_for_span(spans: List[Tuple[int, int]], start: int, end: int) -> List[int]:
    idxs: List[int] = []
    for i, (s, e) in enumerate(spans):
        if e <= start:
            continue
        if s >= end:
            break
        idxs.append(i)
    return idxs


def _merge_pdf_rects(words: List[tuple], boxes: List[Tuple[float, float, float, float]], indexes: List[int]) -> List[Tuple[float, float, float, float]]:
    if not indexes:
        return []
    rects: List[Tuple[float, float, float, float]] = []
    current = None
    prev_key = None
    for i in indexes:
        w = words[i]
        key = (w[5], w[6])
        x0, y0, x1, y1 = boxes[i]
        if current is None or key != prev_key:
            if current is not None:
                rects.append(current)
            current = [x0, y0, x1, y1]
            prev_key = key
        else:
            current[0] = min(current[0], x0)
            current[1] = min(current[1], y0)
            current[2] = max(current[2], x1)
            current[3] = max(current[3], y1)
    if current is not None:
        rects.append(tuple(current))
    return rects


def _pdf_placeholder_rect(rects: List[Tuple[float, float, float, float]]) -> "fitz.Rect":
    best = max(rects, key=lambda r: ((r[2] - r[0]), (r[3] - r[1])))
    return fitz.Rect(*best)


@dataclass(frozen=True)
class PdfFont:
    name: str
    file: str | None
    unicode_ok: bool


def _insert_pdf_label(
    page,
    rect,
    placeholder: str,
    font: PdfFont,
) -> Tuple[bool, bool]:
    insert_rect = fitz.Rect(rect.x0, rect.y0 - 0.5, max(rect.x1, rect.x0 + 42), rect.y1 + 0.5)
    font_sizes = [
        max(6.0, min(11.0, rect.height * 0.85)),
        max(6.0, min(10.0, rect.height * 0.70)),
        max(5.0, min(9.0, rect.height * 0.60)),
    ]
    for label in _pdf_placeholder_variants(placeholder, font.unicode_ok):
        for fs in font_sizes:
            try:
                rc = page.insert_textbox(
                    insert_rect,
                    label,
                    fontname=font.name,
                    fontfile=font.file,
                    fontsize=fs,
                    color=(0, 0, 0),
                    align=0,
                    overlay=True,
                )
                if isinstance(rc, (int, float)) and rc >= 0:
                    return True, False
            except Exception:
                break
    return False, True


def _resolve_pdf_font(page) -> PdfFont:
    font_candidates = ([settings.pdf_font_path] if settings.pdf_font_path else []) + [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "/run/current-system/sw/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/run/current-system/sw/share/X11/fonts/DejaVuSans.ttf",
    ]
    for fp in font_candidates:
        if Path(fp).exists():
            try:
                fitz.Font(fontfile=fp)
                page.insert_font(fontname="AnonDocsUnicode", fontfile=fp)
                return PdfFont(name="AnonDocsUnicode", file=fp, unicode_ok=True)
            except Exception:
                continue
    return PdfFont(name="helv", file=None, unicode_ok=False)


@dataclass(frozen=True)
class PdfMatch:
    rects: List[Tuple[float, float, float, float]]
    placeholder: str
    start: int
    end: int


def _detect_pdf_page_matches(
    page,
    options: AnonymizeOptions,
    counters: dict[str, int],
    keys: dict[tuple[str, str], int],
) -> List[PdfMatch]:
    page_stream = _build_pdf_word_stream(page)
    if not page_stream.text or not page_stream.words:
        return []

    matches: List[PdfMatch] = []
    page_text = page.get_text("text") or ""
    numbered_spans = apply_numbered_placeholders_with_state(page_text, detect_spans(page_text, options), counters, keys)
    for ent in numbered_spans:
        value = page_text[ent.start:ent.end]
        for start, end in _find_occurrences(page_stream.text, value):
            token_indexes = _pdf_token_indexes_for_span(page_stream.spans, start, end)
            if not token_indexes:
                continue
            rects = _merge_pdf_rects(page_stream.words, page_stream.boxes, token_indexes)
            if rects:
                matches.append(PdfMatch(rects, ent.label, start, end))

    # LLM candidates disabled

    matches.sort(key=lambda item: (item.start, item.end))
    accepted: List[PdfMatch] = []
    occupied: List[Tuple[int, int]] = []
    for item in matches:
        s, e = item.start, item.end
        if any(not (e <= os_ or s >= oe) for os_, oe in occupied):
            continue
        occupied.append((s, e))
        accepted.append(item)

    return [PdfMatch(item.rects, item.placeholder.strip(), item.start, item.end) for item in accepted]


def _find_occurrences(text: str, value: str) -> List[Tuple[int, int]]:
    if not value:
        return []
    ranges = [(m.start(), m.end()) for m in re.finditer(re.escape(value), text)]
    if ranges:
        return ranges
    return [(m.start(), m.end()) for m in re.finditer(re.escape(value), text, flags=re.IGNORECASE)]


class PdfRedactor:
    def __init__(self, options: AnonymizeOptions) -> None:
        self.options = options
        self.preview_parts: List[str] = []
        self.warnings: List[str] = []
        self.font_insert_fallback_used = False
        self.unicode_font_used = False
        self.unicode_font_path: str | None = None
        self._counters: dict[str, int] = {}
        self._keys: dict[tuple[str, str], int] = {}

    def redact(self, src: Path, dst: Path) -> Tuple[str, List[str]]:
        if fitz is None:
            raise DomainError("PyMuPDF не установлен", status_code=500)

        doc = fitz.open(str(src))
        try:
            for page in doc:
                self._handle_page(page)
            doc.save(str(dst), garbage=3, deflate=True)
        finally:
            doc.close()

        self._finalize_warnings()
        return "\n".join(self.preview_parts[:20]), self.warnings

    def _handle_page(self, page) -> None:
        page_text = page.get_text("text") or ""
        if page_text and len(self.preview_parts) < 20:
            self.preview_parts.append(anonymize_text_no_llm(page_text, self.options)[:400])

        matches = _detect_pdf_page_matches(page, self.options, self._counters, self._keys)
        if not matches:
            return

        font = _resolve_pdf_font(page)
        if font.unicode_ok:
            self.unicode_font_used = True
            self.unicode_font_path = self.unicode_font_path or font.file

        insert_jobs: List[Tuple[List[Tuple[float, float, float, float]], str]] = []
        for match in matches:
            for rect_tuple in match.rects:
                rect = fitz.Rect(*rect_tuple)
                page.add_redact_annot(rect, fill=(1, 1, 1))
            insert_jobs.append((match.rects, match.placeholder))

        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)

        for rects, placeholder in insert_jobs:
            rect = _pdf_placeholder_rect(rects)
            inserted, used_ascii_fallback = _insert_pdf_label(page, rect, placeholder, font)
            if used_ascii_fallback or not inserted:
                self.font_insert_fallback_used = True

    def _finalize_warnings(self) -> None:
        if self.font_insert_fallback_used:
            self.warnings.append(
                "Часть PDF-плейсхолдеров вставлена ASCII-метками ([NAME]/[PHONE]/...) из-за ошибки загрузки TTF в PyMuPDF. Макет страницы сохранен."
            )
        # warnings suppressed by request


def redact_pdf_in_place(src: Path, dst: Path, options: AnonymizeOptions) -> Tuple[str, List[str]]:
    return PdfRedactor(options).redact(src, dst)


def safe_redact_pdf(src: Path, dst: Path, options: AnonymizeOptions) -> Tuple[str, List[str]]:
    try:
        return redact_pdf_in_place(src, dst, options)
    except Exception as exc:
        logger.exception("PDF redaction failed")
        raise DomainError("Ошибка обработки PDF", status_code=500, details=str(exc)) from exc
