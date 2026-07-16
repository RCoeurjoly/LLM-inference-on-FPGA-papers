from __future__ import annotations

import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

from paperlib.arxiv import ArxivClient, build_search_query
from paperlib.cache import cache_pdf
from paperlib.config import load_config
from paperlib.models import PaperVersion, QueryConfig
from paperlib.render import render_readme
from paperlib.storage import (
    atomic_write_text,
    load_catalog,
    load_survey,
    load_watermark,
    merge_survey_values,
    write_catalog,
    write_state,
    write_survey,
)


ARXIV_START = datetime(2007, 1, 1, tzinfo=UTC)
SLICE_LIMIT = 2000
MINIMUM_SPLIT_WINDOW = timedelta(minutes=1)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware")
    return value.astimezone(UTC)


def _rfc3339(value: datetime) -> str:
    return _as_utc(value).isoformat().replace("+00:00", "Z")


def _parse_rfc3339(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def _fetch_pdf(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "LLM-inference-on-FPGA-papers/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def merge_papers(
    existing: Mapping[str, PaperVersion], incoming: Mapping[str, PaperVersion]
) -> dict[str, PaperVersion]:
    """Merge arXiv manifestations, preserving cache receipts across metadata refreshes."""
    merged = dict(existing)
    for key, candidate in incoming.items():
        current = merged.get(key)
        if current is None:
            merged[key] = candidate
            continue
        chosen = candidate if candidate.retrieved_at >= current.retrieved_at else current
        cache = chosen.cache or current.cache or candidate.cache
        merged[key] = replace(
            chosen,
            query_ids=tuple(sorted(set(current.query_ids).union(candidate.query_ids))),
            cache=cache,
        )
    return merged


def _fetch_window(
    client: ArxivClient,
    config: QueryConfig,
    date_field: str,
    start_at: datetime,
    end_at: datetime,
    sort_by: str,
) -> list[PaperVersion]:
    query = build_search_query(config.base_query, date_field, start_at, end_at)
    first = client.fetch_page(query, 0, config.page_size, sort_by, "ascending")
    if first.total_results >= SLICE_LIMIT:
        if end_at - start_at <= MINIMUM_SPLIT_WINDOW:
            raise ValueError("arXiv date window remains at the 2000-result limit")
        midpoint = start_at + (end_at - start_at) / 2
        return _fetch_window(
            client, config, date_field, start_at, midpoint, sort_by
        ) + _fetch_window(client, config, date_field, midpoint, end_at, sort_by)

    papers = list(first.papers)
    offset = len(papers)
    while offset < first.total_results:
        page = client.fetch_page(query, offset, config.page_size, sort_by, "ascending")
        if not page.papers:
            raise ValueError("arXiv returned an empty page before its declared result count")
        papers.extend(page.papers)
        offset += len(page.papers)
    return [replace(paper, query_ids=(config.query_id,)) for paper in papers]


def _write_outputs(
    repo_root: Path,
    config: QueryConfig,
    papers: Mapping[str, PaperVersion],
    survey: Mapping[str, Mapping[str, str]],
    renderer: Callable[[Mapping[str, PaperVersion], Mapping[str, Mapping[str, str]]], str],
) -> None:
    write_catalog(repo_root / "data/catalog.json", config.query_id, papers)
    write_survey(repo_root / "data/survey.csv", survey)
    atomic_write_text(repo_root / "README.md", renderer(papers, survey))


def _cache_records(
    papers: Mapping[str, PaperVersion],
    repo_root: Path,
    fetch_pdf: Callable[[str], bytes],
    timestamp: str,
) -> dict[str, PaperVersion]:
    cached = dict(papers)
    for key in sorted(cached):
        cached[key] = cache_pdf(
            cached[key], repo_root / "papers", fetch_pdf, lambda: timestamp
        )
    return cached


def bootstrap_all(
    repo_root: Path,
    download: bool,
    now: datetime,
    client: ArxivClient,
    pdf_fetcher: Callable[[str], bytes] = _fetch_pdf,
    renderer: Callable[[Mapping[str, PaperVersion], Mapping[str, Mapping[str, str]]], str] = render_readme,
) -> dict[str, PaperVersion]:
    """Discover every matching submission from arXiv's historical range."""
    now = _as_utc(now)
    config = load_config(repo_root / "config/query.json")
    incoming = _fetch_window(
        client, config, "submittedDate", ARXIV_START, now, "submittedDate"
    )
    merged = merge_papers(load_catalog(repo_root / "data/catalog.json"), {
        paper.key: paper for paper in incoming
    })
    if download:
        merged = _cache_records(merged, repo_root, pdf_fetcher, _rfc3339(now))
    survey = merge_survey_values(
        load_survey(repo_root / "data/survey.csv"),
        (paper.arxiv_id for paper in merged.values()),
    )
    _write_outputs(repo_root, config, merged, survey, renderer)
    return merged


def sync_recent(
    repo_root: Path,
    download_new: bool,
    now: datetime,
    client: ArxivClient,
    pdf_fetcher: Callable[[str], bytes] = _fetch_pdf,
    renderer: Callable[[Mapping[str, PaperVersion], Mapping[str, Mapping[str, str]]], str] = render_readme,
) -> dict[str, PaperVersion]:
    """Refresh recent updates and move the watermark only after a full success."""
    now = _as_utc(now)
    config = load_config(repo_root / "config/query.json")
    state_path = repo_root / "state/collector.json"
    watermark = load_watermark(state_path)
    start_at = (
        _parse_rfc3339(watermark) if watermark is not None else now
    ) - timedelta(hours=config.daily_overlap_hours)
    incoming = _fetch_window(
        client, config, "lastUpdatedDate", start_at, now, "lastUpdatedDate"
    )
    merged = merge_papers(load_catalog(repo_root / "data/catalog.json"), {
        paper.key: paper for paper in incoming
    })
    if download_new:
        merged = _cache_records(merged, repo_root, pdf_fetcher, _rfc3339(now))
    survey = merge_survey_values(
        load_survey(repo_root / "data/survey.csv"),
        (paper.arxiv_id for paper in merged.values()),
    )
    _write_outputs(repo_root, config, merged, survey, renderer)
    newest_update = max((paper.updated_at for paper in incoming), default=_rfc3339(now))
    write_state(state_path, newest_update)
    return merged


def download_missing(
    repo_root: Path,
    pdf_fetcher: Callable[[str], bytes] = _fetch_pdf,
    now: datetime | None = None,
) -> dict[str, PaperVersion]:
    """Fill missing local PDF cache entries without performing API discovery."""
    timestamp = _as_utc(now or datetime.now(UTC))
    config = load_config(repo_root / "config/query.json")
    papers = load_catalog(repo_root / "data/catalog.json")
    cached = _cache_records(papers, repo_root, pdf_fetcher, _rfc3339(timestamp))
    write_catalog(repo_root / "data/catalog.json", config.query_id, cached)
    return cached
