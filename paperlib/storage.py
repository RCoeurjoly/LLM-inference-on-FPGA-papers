from __future__ import annotations

import csv
import json
from collections.abc import Iterable, Mapping
from pathlib import Path

from paperlib.models import PaperVersion, PdfCache


SURVEY_FIELDS = (
    "arxiv_id",
    "review_status",
    "quantization",
    "architecture",
    "fpga_device",
    "model",
    "toolflow",
    "evidence_pages",
    "notes",
)


def atomic_write_text(path: Path, content: str) -> None:
    """Replace a text file only after its complete new contents are written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(content, encoding="utf-8", newline="")
    temporary.replace(path)


def _cache_to_data(cache: PdfCache | None) -> dict[str, object] | None:
    if cache is None:
        return None
    return {
        "filename": cache.filename,
        "sha256": cache.sha256,
        "byte_count": cache.byte_count,
        "downloaded_at": cache.downloaded_at,
    }


def _paper_to_data(paper: PaperVersion) -> dict[str, object]:
    return {
        "arxiv_id": paper.arxiv_id,
        "version": paper.version,
        "title": paper.title,
        "abstract": paper.abstract,
        "authors": list(paper.authors),
        "categories": list(paper.categories),
        "primary_category": paper.primary_category,
        "published_at": paper.published_at,
        "updated_at": paper.updated_at,
        "abs_url": paper.abs_url,
        "pdf_url": paper.pdf_url,
        "doi": paper.doi,
        "journal_ref": paper.journal_ref,
        "license_url": paper.license_url,
        "query_ids": list(paper.query_ids),
        "retrieved_at": paper.retrieved_at,
        "cache": _cache_to_data(paper.cache),
    }


def _paper_from_data(data: Mapping[str, object]) -> PaperVersion:
    cache_data = data.get("cache")
    cache = None
    if isinstance(cache_data, Mapping):
        cache = PdfCache(
            filename=str(cache_data["filename"]),
            sha256=str(cache_data["sha256"]),
            byte_count=int(cache_data["byte_count"]),
            downloaded_at=str(cache_data["downloaded_at"]),
        )
    return PaperVersion(
        arxiv_id=str(data["arxiv_id"]),
        version=int(data["version"]),
        title=str(data["title"]),
        abstract=str(data["abstract"]),
        authors=tuple(str(item) for item in data["authors"]),
        categories=tuple(str(item) for item in data["categories"]),
        primary_category=str(data["primary_category"]),
        published_at=str(data["published_at"]),
        updated_at=str(data["updated_at"]),
        abs_url=str(data["abs_url"]),
        pdf_url=str(data["pdf_url"]),
        doi=None if data["doi"] is None else str(data["doi"]),
        journal_ref=None if data["journal_ref"] is None else str(data["journal_ref"]),
        license_url=None if data["license_url"] is None else str(data["license_url"]),
        query_ids=tuple(str(item) for item in data["query_ids"]),
        retrieved_at=str(data["retrieved_at"]),
        cache=cache,
    )


def load_catalog(path: Path) -> dict[str, PaperVersion]:
    """Load schema version 1 catalogue records keyed by versioned arXiv ID."""
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("catalog schema_version must be 1")
    papers_data = data.get("papers")
    if not isinstance(papers_data, dict):
        raise ValueError("catalog papers must be an object")
    papers = {key: _paper_from_data(value) for key, value in papers_data.items()}
    if any(key != paper.key for key, paper in papers.items()):
        raise ValueError("catalog key does not match paper version")
    return papers


def write_catalog(
    path: Path, query_id: str, papers: Mapping[str, PaperVersion]
) -> None:
    """Atomically write a deterministic schema version 1 catalogue."""
    ordered = sorted(
        papers.items(), key=lambda item: (item[1].updated_at, item[0]), reverse=True
    )
    data = {
        "schema_version": 1,
        "query_id": query_id,
        "papers": {key: _paper_to_data(paper) for key, paper in ordered},
    }
    atomic_write_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def load_survey(path: Path) -> dict[str, dict[str, str]]:
    """Load human survey annotations keyed by base arXiv ID."""
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(SURVEY_FIELDS):
            raise ValueError("survey CSV header is invalid")
        rows: dict[str, dict[str, str]] = {}
        for source_row in reader:
            row = {field: source_row.get(field, "") or "" for field in SURVEY_FIELDS}
            if not row["arxiv_id"]:
                raise ValueError("survey row is missing arxiv_id")
            rows[row["arxiv_id"]] = row
    return rows


def write_survey(path: Path, rows: Mapping[str, Mapping[str, str]]) -> None:
    """Atomically write complete survey rows in stable base-ID order."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SURVEY_FIELDS)
        writer.writeheader()
        for arxiv_id in sorted(rows):
            writer.writerow({field: rows[arxiv_id].get(field, "") for field in SURVEY_FIELDS})
    temporary.replace(path)


def merge_survey_values(
    rows: Mapping[str, Mapping[str, str]], arxiv_ids: Iterable[str]
) -> dict[str, dict[str, str]]:
    """Return a copy of survey rows with blank values for unseen base IDs."""
    merged = {
        arxiv_id: {field: row.get(field, "") for field in SURVEY_FIELDS}
        for arxiv_id, row in rows.items()
    }
    for arxiv_id in arxiv_ids:
        merged.setdefault(arxiv_id, {field: "" for field in SURVEY_FIELDS})
        merged[arxiv_id]["arxiv_id"] = arxiv_id
    return merged


def merge_survey_rows(path: Path, arxiv_ids: Iterable[str]) -> dict[str, dict[str, str]]:
    """Add blank annotations for unseen base IDs without altering existing cells."""
    rows = merge_survey_values(load_survey(path), arxiv_ids)
    write_survey(path, rows)
    return rows


def load_watermark(path: Path) -> str | None:
    """Return the most recent successful update timestamp, if one exists."""
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("state schema_version must be 1")
    watermark = data.get("last_successful_updated_at")
    if not isinstance(watermark, str):
        raise ValueError("state watermark must be a string")
    return watermark


def write_state(path: Path, watermark: str) -> None:
    """Atomically replace the successful-update watermark."""
    data = {"schema_version": 1, "last_successful_updated_at": watermark}
    atomic_write_text(path, json.dumps(data, sort_keys=True) + "\n")
