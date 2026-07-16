from __future__ import annotations

import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as element_tree
from collections.abc import Callable, Mapping
from datetime import UTC, datetime

from paperlib.models import FeedPage, PaperVersion


ATOM = "{http://www.w3.org/2005/Atom}"
OPENSEARCH = "{http://a9.com/-/spec/opensearch/1.1/}"
ARXIV = "{http://arxiv.org/schemas/atom}"
VERSIONED_ID = re.compile(r"^(?P<base>.+)v(?P<version>[1-9][0-9]*)$")


def _rfc3339_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _normalize_text(value: str | None) -> str:
    return " ".join((value or "").split())


def _optional_text(entry: element_tree.Element, tag: str) -> str | None:
    value = _normalize_text(entry.findtext(tag))
    return value or None


def _parse_versioned_identifier(value: str) -> tuple[str, int]:
    path = urllib.parse.urlparse(value).path
    identifier = path.removeprefix("/abs/")
    match = VERSIONED_ID.fullmatch(identifier)
    if match is None:
        raise ValueError(f"arXiv entry ID is not versioned: {value}")
    return match.group("base"), int(match.group("version"))


def build_search_query(
    base_query: str,
    date_field: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> str:
    """Add an inclusive UTC date range to a configured arXiv query."""
    if date_field is None:
        return base_query
    if start is None or end is None:
        raise ValueError("date ranges require start and end")

    def stamp(value: datetime) -> str:
        return value.astimezone(UTC).strftime("%Y%m%d%H%M")

    return f"({base_query}) AND {date_field}:[{stamp(start)} TO {stamp(end)}]"


def parse_feed(xml_bytes: bytes, query_id: str, retrieved_at: str) -> FeedPage:
    """Convert an arXiv Atom response into stable, versioned paper records."""
    root = element_tree.fromstring(xml_bytes)
    total_text = root.findtext(f"{OPENSEARCH}totalResults")
    if total_text is None:
        raise ValueError("arXiv response is missing totalResults")

    try:
        total_results = int(total_text)
    except ValueError as error:
        raise ValueError("arXiv totalResults is not an integer") from error

    papers: list[PaperVersion] = []
    for entry in root.findall(f"{ATOM}entry"):
        identifier = _optional_text(entry, f"{ATOM}id")
        if identifier is None:
            raise ValueError("arXiv entry is missing an ID")
        arxiv_id, version = _parse_versioned_identifier(identifier)

        authors = tuple(
            author
            for author in (
                _normalize_text(node.findtext(f"{ATOM}name"))
                for node in entry.findall(f"{ATOM}author")
            )
            if author
        )
        categories = tuple(
            category
            for category in (
                node.attrib.get("term", "").strip()
                for node in entry.findall(f"{ATOM}category")
            )
            if category
        )
        primary_category = ""
        primary_node = entry.find(f"{ARXIV}primary_category")
        if primary_node is not None:
            primary_category = primary_node.attrib.get("term", "").strip()
        if not primary_category and categories:
            primary_category = categories[0]

        papers.append(
            PaperVersion(
                arxiv_id=arxiv_id,
                version=version,
                title=_normalize_text(entry.findtext(f"{ATOM}title")),
                abstract=_normalize_text(entry.findtext(f"{ATOM}summary")),
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published_at=_normalize_text(entry.findtext(f"{ATOM}published")),
                updated_at=_normalize_text(entry.findtext(f"{ATOM}updated")),
                abs_url=f"https://arxiv.org/abs/{arxiv_id}v{version}",
                pdf_url=f"https://arxiv.org/pdf/{arxiv_id}v{version}",
                doi=_optional_text(entry, f"{ARXIV}doi"),
                journal_ref=_optional_text(entry, f"{ARXIV}journal_ref"),
                license_url=_optional_text(entry, f"{ARXIV}license"),
                query_ids=(query_id,),
                retrieved_at=retrieved_at,
            )
        )

    return FeedPage(total_results=total_results, papers=tuple(papers))


def _default_opener(url: str, headers: Mapping[str, str]) -> bytes:
    request = urllib.request.Request(url, headers=dict(headers))
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


class ArxivClient:
    """Serialized arXiv API client that enforces a minimum request interval."""

    def __init__(
        self,
        api_url: str,
        user_agent: str,
        min_interval_seconds: float,
        opener: Callable[[str, Mapping[str, str]], bytes] = _default_opener,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.api_url = api_url
        self.user_agent = user_agent
        self.min_interval_seconds = min_interval_seconds
        self._opener = opener
        self._clock = clock
        self._sleeper = sleeper
        self._last_request_started: float | None = None

    def fetch_page(
        self,
        search_query: str,
        start: int,
        max_results: int,
        sort_by: str,
        sort_order: str,
    ) -> FeedPage:
        if start < 0:
            raise ValueError("start must be non-negative")
        if not 1 <= max_results <= 100:
            raise ValueError("max_results must be between 1 and 100")

        request_started = self._clock()
        if self._last_request_started is not None:
            remaining = self.min_interval_seconds - (
                request_started - self._last_request_started
            )
            if remaining > 0:
                self._sleeper(remaining)
                request_started = self._clock()
        self._last_request_started = request_started

        query = urllib.parse.urlencode(
            {
                "search_query": search_query,
                "start": start,
                "max_results": max_results,
                "sortBy": sort_by,
                "sortOrder": sort_order,
            }
        )
        separator = "&" if "?" in self.api_url else "?"
        url = f"{self.api_url}{separator}{query}"
        xml_bytes = self._opener(url, {"User-Agent": self.user_agent})
        return parse_feed(xml_bytes, query_id=search_query, retrieved_at=_rfc3339_now())
