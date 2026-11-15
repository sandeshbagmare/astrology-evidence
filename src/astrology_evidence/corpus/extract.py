"""Offline extraction drafts. Never grants rights or publication approval.

PDF parsing and OCR require an operator-isolated process with OS memory, disk,
CPU and network limits. These adapters do not provide that isolation.
"""

import argparse
import csv
import io
import json
import math
import os
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_BYTES = 20_000_000
MAX_PAGES = 500
MAX_TEXT_BYTES = 10_000_000


class PageInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(max_length=100_000)
    pdf_page_index: int = Field(ge=0, strict=True)
    printed_page: str | None = Field(default=None, max_length=100)
    bounding_box: tuple[float, float, float, float] | None = None

    @field_validator("bounding_box")
    @classmethod
    def valid_box(cls, box):
        if box is not None and (
            not all(math.isfinite(v) for v in box)
            or min(box) < 0
            or box[0] > box[2]
            or box[1] > box[3]
        ):
            raise ValueError("invalid bounding box")
        return box


class PageDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pages: list[PageInput] = Field(min_length=1, max_length=MAX_PAGES)


@dataclass(frozen=True)
class Word:
    text: str
    bounding_box: tuple[int, int, int, int]
    confidence: float


@dataclass(frozen=True)
class ExtractedPage:
    text: str
    pdf_page_index: int
    printed_page: str | None
    bounding_box: tuple[float, float, float, float] | None
    extraction_method: str
    source_sha256: str
    text_sha256: str
    review_state: Literal["pending", "quarantined"]
    ocr_confidence: float | None = None
    error: str | None = None
    words: tuple[Word, ...] = ()


@dataclass(frozen=True)
class Extraction:
    source_sha256: str
    extraction_version: str
    pages: tuple[ExtractedPage, ...]


def bounded_read(path: Path, work_root: Path, max_bytes: int = MAX_BYTES) -> bytes:
    if not 1 <= max_bytes <= MAX_BYTES:
        raise ValueError("invalid byte limit")
    root = work_root.resolve(strict=True)
    resolved = path.resolve(strict=True)
    if not root.is_dir() or not resolved.is_relative_to(root):
        raise ValueError("source must remain within work root")
    if not resolved.is_file() or resolved.stat().st_size > max_bytes:
        raise ValueError("source exceeds byte limit or is not a file")
    with resolved.open("rb") as stream:
        data = stream.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError("source exceeds byte limit")
    return data


def _page(page: PageInput, method: str, source_hash: str) -> ExtractedPage:
    empty = not page.text.strip()
    return ExtractedPage(
        **page.model_dump(),
        extraction_method=method,
        source_sha256=source_hash,
        text_sha256=sha256(page.text.encode("utf-8")).hexdigest(),
        review_state="quarantined" if empty else "pending",
        error="ocr_required" if empty else None,
    )


def extract_file(
    path: Path, *, work_root: Path, max_bytes: int = MAX_BYTES, max_pages: int = MAX_PAGES
) -> Extraction:
    if not 1 <= max_pages <= MAX_PAGES:
        raise ValueError("invalid page limit")
    data = bounded_read(path, work_root, max_bytes)
    digest = sha256(data).hexdigest()
    suffix = path.suffix.lower()
    if suffix == ".json":
        inputs = PageDocument.model_validate_json(data).pages
        method = "page_json_v1"
    elif suffix == ".txt":
        texts = data.decode("utf-8").split("\f")
        if len(texts) > max_pages:
            raise ValueError("page limit exceeded")
        inputs = [PageInput(text=text, pdf_page_index=i) for i, text in enumerate(texts)]
        method = "native_text_v1"
    elif suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ValueError("PDF extraction requires the optional pypdf dependency") from exc
        reader = PdfReader(io.BytesIO(data), strict=True)
        if reader.is_encrypted:
            raise ValueError("encrypted PDFs require operator preprocessing")
        if not 1 <= len(reader.pages) <= max_pages:
            raise ValueError("page limit exceeded")
        inputs = []
        text_bytes = 0
        for index, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            text_bytes += len(text.encode("utf-8"))
            if text_bytes > MAX_TEXT_BYTES:
                raise ValueError("extracted text byte limit exceeded")
            inputs.append(PageInput(text=text, pdf_page_index=index))
        method = "pypdf_native_v1"
    else:
        raise ValueError("supported source formats are .txt, .json and .pdf")
    if not 1 <= len(inputs) <= max_pages:
        raise ValueError("page limit exceeded")
    if len({p.pdf_page_index for p in inputs}) != len(inputs):
        raise ValueError("duplicate PDF page index")
    if sum(len(p.text.encode("utf-8")) for p in inputs) > MAX_TEXT_BYTES:
        raise ValueError("extracted text byte limit exceeded")
    return Extraction(digest, "extraction-v1", tuple(_page(p, method, digest) for p in inputs))


def ocr_image(
    path: Path,
    *,
    work_root: Path,
    executable: Path,
    pdf_page_index: int = 0,
    printed_page: str | None = None,
    timeout: int = 30,
) -> ExtractedPage:
    """Operator-only adapter; caller must supply OS isolation, no public route."""
    if not executable.is_absolute() or not executable.is_file():
        raise ValueError("an absolute operator-provided executable is required")
    if executable.suffix.lower() in {".bat", ".cmd", ".ps1"}:
        raise ValueError("executable must be a binary, not a shell script")
    if type(timeout) is not int or not 1 <= timeout <= 120:
        raise ValueError("timeout must be between 1 and 120 seconds")
    PageInput(text="", pdf_page_index=pdf_page_index, printed_page=printed_page)
    if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
        raise ValueError("OCR requires an operator-rendered page image")
    image = bounded_read(path, work_root)
    digest = sha256(image).hexdigest()
    with tempfile.TemporaryDirectory(prefix="ocr-", dir=work_root.resolve()) as temporary:
        directory = Path(temporary)
        local_image = directory / ("page" + path.suffix.lower())
        local_image.write_bytes(image)
        output = directory / "result"
        # No credentials, proxy configuration or user-controlled CLI flags are inherited.
        environment = {
            key: os.environ[key] for key in ("SYSTEMROOT", "WINDIR") if key in os.environ
        }
        environment.update({"OMP_THREAD_LIMIT": "1", "TEMP": temporary, "TMP": temporary})
        try:
            subprocess.run(
                [
                    str(executable.resolve()),
                    str(local_image),
                    str(output),
                    "-l",
                    "eng",
                    "--psm",
                    "3",
                    "tsv",
                ],
                cwd=directory,
                env=environment,
                shell=False,
                check=True,
                timeout=timeout,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
            )
            tsv = bounded_read(output.with_suffix(".tsv"), directory, 2_000_000)
        except (subprocess.SubprocessError, OSError) as exc:
            raise ValueError("OCR failed or timed out; page remains unreviewed") from exc
    words = []
    for row in csv.DictReader(io.StringIO(tsv.decode("utf-8")), delimiter="\t"):
        if row.get("level") != "5":
            continue
        try:
            confidence = float(row["conf"]) / 100
            left, top, width, height = (int(row[key]) for key in ("left", "top", "width", "height"))
            text = row["text"]
            if not math.isfinite(confidence) or not 0 <= confidence <= 1:
                raise ValueError("invalid OCR confidence")
            if min(left, top, width, height) < 0 or not text:
                raise ValueError("invalid OCR word")
            words.append(Word(text, (left, top, left + width, top + height), confidence))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid OCR TSV output") from exc
    text = " ".join(w.text for w in words)
    confidence = min((w.confidence for w in words), default=0.0)
    page = PageInput(text=text, pdf_page_index=pdf_page_index, printed_page=printed_page)
    return ExtractedPage(
        **page.model_dump(),
        extraction_method="tesseract_tsv_v1",
        source_sha256=digest,
        text_sha256=sha256(text.encode("utf-8")).hexdigest(),
        ocr_confidence=confidence,
        review_state="pending" if words and confidence >= 0.9 else "quarantined",
        error=None if words and confidence >= 0.9 else "ocr_quality_review_required",
        words=tuple(words),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--work-root", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = extract_file(args.source, work_root=args.work_root)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(asdict(result), ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
