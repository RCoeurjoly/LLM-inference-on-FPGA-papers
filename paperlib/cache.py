from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from paperlib.models import PaperVersion, PdfCache


def cache_filename(paper: PaperVersion) -> str:
    """Return a filesystem-safe name for one immutable arXiv version."""
    return f"{paper.arxiv_id.replace('/', '_')}v{paper.version}.pdf"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _has_verified_receipt(paper: PaperVersion, cache_dir: Path) -> bool:
    if paper.cache is None:
        return False
    if paper.cache.filename != cache_filename(paper):
        return False
    path = cache_dir / paper.cache.filename
    if not path.is_file():
        return False
    payload = path.read_bytes()
    return len(payload) == paper.cache.byte_count and _sha256(payload) == paper.cache.sha256


def cache_pdf(
    paper: PaperVersion,
    cache_dir: Path,
    fetch: Callable[[str], bytes],
    now: Callable[[], str],
) -> PaperVersion:
    """Fetch a PDF once, validate it, and atomically store a cache receipt."""
    if _has_verified_receipt(paper, cache_dir):
        return paper

    cache_dir.mkdir(parents=True, exist_ok=True)
    filename = cache_filename(paper)
    final_path = cache_dir / filename
    temporary_path = cache_dir / f"{filename}.part"

    try:
        payload = fetch(paper.pdf_url)
        if not payload:
            raise ValueError("PDF response is empty")
        if b"%PDF-" not in payload[:1024]:
            raise ValueError("PDF response is missing a PDF signature")
        temporary_path.write_bytes(payload)
        receipt = PdfCache(
            filename=filename,
            sha256=_sha256(payload),
            byte_count=len(payload),
            downloaded_at=now(),
        )
        temporary_path.replace(final_path)
        return replace(paper, cache=receipt)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
