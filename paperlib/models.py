from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QueryConfig:
    schema_version: int
    query_id: str
    api_url: str
    base_query: str
    page_size: int
    min_api_interval_seconds: float
    daily_overlap_hours: int
    cron_hour: int
    cron_minute: int
    user_agent: str


@dataclass(frozen=True)
class PdfCache:
    filename: str
    sha256: str
    byte_count: int
    downloaded_at: str


@dataclass(frozen=True)
class PaperVersion:
    arxiv_id: str
    version: int
    title: str
    abstract: str
    authors: tuple[str, ...]
    categories: tuple[str, ...]
    primary_category: str
    published_at: str
    updated_at: str
    abs_url: str
    pdf_url: str
    doi: str | None
    journal_ref: str | None
    license_url: str | None
    query_ids: tuple[str, ...]
    retrieved_at: str
    cache: PdfCache | None = None

    @property
    def key(self) -> str:
        return f"{self.arxiv_id}v{self.version}"


@dataclass(frozen=True)
class FeedPage:
    total_results: int
    papers: tuple[PaperVersion, ...]
