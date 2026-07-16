# arXiv FPGA–LLM Paper Library Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Build a local, daily-synchronized arXiv paper-survey repository that tracks durable metadata and manual technical notes while caching PDFs locally without committing them to Git.

**Architecture:** A Python 3.11 standard-library package separates configuration, arXiv transport/parsing, persistence, PDF caching, collection orchestration, Markdown rendering, CLI dispatch, and crontab management. The tracked catalogue and survey are the research record; papers, state, and logs remain ignored local data.

**Tech Stack:** Python 3.11 standard library, unittest, Git, user crontab, and flock.

## Global Constraints

- Use arXiv as the only discovery and PDF source in version 1.
- Search title and abstract for LLM/large-language-model, inference, and FPGA terms.
- Serialize arXiv API traffic and wait at least three seconds between API requests.
- Bootstrap all historical results and split any 2,000-result date slice.
- Track metadata, links, and manual notes in Git; ignore PDFs, state, logs, and partial downloads.
- Do not infer redistribution rights or serve cached PDFs.
- Identify records by base arXiv ID plus version; download each valid version once.
- Preserve all non-empty manual survey cells.
- Use atomic writes; update the sync watermark only after all other writes succeed.
- Keep all tests offline and run python3 -m unittest discover -s tests -v.
- Commit each independently testable deliverable.

---

## File Structure

    .gitignore                         ignored local runtime data
    README.md                          generated survey index and usage
    config/query.json                  committed API/query settings
    data/catalog.json                  committed versioned metadata
    data/survey.csv                    committed human annotations
    paperlib/__init__.py
    paperlib/models.py                 typed records
    paperlib/config.py                 committed config validation
    paperlib/arxiv.py                  API URL/query/pacing/Atom parsing
    paperlib/storage.py                atomic JSON, CSV, and watermark I/O
    paperlib/cache.py                  PDF validation and cache receipts
    paperlib/collector.py              bootstrap, sync, and merge rules
    paperlib/render.py                 deterministic README rendering
    paperlib/cli.py                    collector argument dispatch
    paperlib/cron.py                   managed crontab text operations
    scripts/collect_arxiv.py           thin collector executable
    scripts/install_cron.py            explicit install/remove executable
    tests/fixtures/sample_feed.xml     saved Atom response
    tests/test_config.py
    tests/test_arxiv.py
    tests/test_storage.py
    tests/test_cache.py
    tests/test_collector.py
    tests/test_render.py
    tests/test_cli.py
    tests/test_cron.py

## Shared Interfaces

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
        authors: Sequence[str]
        categories: Sequence[str]
        primary_category: str
        published_at: str
        updated_at: str
        abs_url: str
        pdf_url: str
        doi: str | None
        journal_ref: str | None
        license_url: str | None
        query_ids: Sequence[str]
        retrieved_at: str
        cache: PdfCache | None = None

        @property
        def key(self) -> str:
            return f"{self.arxiv_id}v{self.version}"

    @dataclass(frozen=True)
    class FeedPage:
        total_results: int
        papers: Sequence[PaperVersion]

The persistent functions are:

    load_config(path: Path) -> QueryConfig
    build_search_query(base_query: str, date_field: str | None,
                       start: datetime | None, end: datetime | None) -> str
    parse_feed(xml_bytes: bytes, query_id: str, retrieved_at: str) -> FeedPage
    load_catalog(path: Path) -> dict[str, PaperVersion]
    write_catalog(path: Path, query_id: str,
                  papers: Mapping[str, PaperVersion]) -> None
    load_survey(path: Path) -> dict[str, dict[str, str]]
    merge_survey_rows(path: Path, arxiv_ids: Iterable[str]) -> dict[str, dict[str, str]]
    load_watermark(path: Path) -> str | None
    write_state(path: Path, watermark: str) -> None
    cache_pdf(paper: PaperVersion, cache_dir: Path,
              fetch: Callable[[str], bytes], now: Callable[[], str]) -> PaperVersion
    bootstrap_all(repo_root: Path, download: bool, now: datetime,
                  client: ArxivClient) -> dict[str, PaperVersion]
    sync_recent(repo_root: Path, download_new: bool, now: datetime,
                client: ArxivClient) -> dict[str, PaperVersion]

---

### Task 1: Establish repository configuration and typed records

**Files:**
- Create: .gitignore
- Create: config/query.json
- Create: data/catalog.json
- Create: data/survey.csv
- Create: paperlib/__init__.py
- Create: paperlib/models.py
- Create: paperlib/config.py
- Create: tests/test_config.py

**Consumes:** Approved design specification.

**Produces:** Validated QueryConfig and stable data-file skeletons.

- [ ] **Step 1: Write the failing configuration tests**

    from __future__ import annotations

    import json
    import tempfile
    import unittest
    from pathlib import Path

    from paperlib.config import load_config


    class ConfigTests(unittest.TestCase):
        def test_loads_committed_config(self) -> None:
            config = load_config(Path("config/query.json"))
            self.assertEqual(config.schema_version, 1)
            self.assertEqual(config.query_id, "llm-inference-fpga-v1")
            self.assertEqual(config.page_size, 100)
            self.assertEqual(config.min_api_interval_seconds, 3.0)
            self.assertIn("ti:LLM", config.base_query)

        def test_rejects_missing_required_keys(self) -> None:
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "query.json"
                path.write_text(json.dumps({"schema_version": 1}), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "missing required keys"):
                    load_config(path)


    if __name__ == "__main__":
        unittest.main()

- [ ] **Step 2: Run the test to verify it fails**

Run: python3 -m unittest discover -s tests -p 'test_config.py' -v

Expected: FAIL because paperlib.config does not exist.

- [ ] **Step 3: Add exact configuration and model implementation**

Use this .gitignore content:

    /papers/
    /state/
    /logs/
    *.part
    __pycache__/
    *.py[cod]
    .venv/

Use this config/query.json content:

    {
      "schema_version": 1,
      "query_id": "llm-inference-fpga-v1",
      "api_url": "https://export.arxiv.org/api/query",
      "base_query": "(ti:LLM OR abs:LLM OR ti:LLMs OR abs:LLMs OR ti:\"large language model\" OR abs:\"large language model\" OR ti:\"large language models\" OR abs:\"large language models\") AND (ti:inference OR abs:inference) AND (ti:FPGA OR abs:FPGA)",
      "page_size": 100,
      "min_api_interval_seconds": 3.0,
      "daily_overlap_hours": 72,
      "cron_hour": 3,
      "cron_minute": 17,
      "user_agent": "LLM-inference-on-FPGA-papers/1.0 (local research collector)"
    }

Use this data/catalog.json content:

    {"schema_version": 1, "query_id": "llm-inference-fpga-v1", "papers": {}}

Use this data/survey.csv header:

    arxiv_id,review_status,quantization,architecture,fpga_device,model,toolflow,evidence_pages,notes

Implement the three dataclasses from Shared Interfaces in paperlib/models.py. Implement load_config in paperlib/config.py by parsing JSON, checking every QueryConfig field is present, rejecting schema_version other than 1, rejecting page_size outside 1 through 100, rejecting a minimum interval below 3.0, rejecting a cron hour outside 0 through 23, and rejecting a cron minute outside 0 through 59. Return QueryConfig with the exact field values.

- [ ] **Step 4: Run focused verification**

Run: python3 -m unittest discover -s tests -p 'test_config.py' -v

Expected: PASS with two tests.

Run: git check-ignore -v papers/example.pdf state/run.json logs/cron.log example.part

Expected: each argument is ignored by .gitignore.

- [ ] **Step 5: Commit**

    git add .gitignore config/query.json data/catalog.json data/survey.csv paperlib tests/test_config.py
    git commit -m "feat: add paper-library configuration"

---

### Task 2: Parse and pace arXiv API requests

**Files:**
- Create: paperlib/arxiv.py
- Create: tests/fixtures/sample_feed.xml
- Create: tests/test_arxiv.py

**Consumes:** QueryConfig, PaperVersion, and FeedPage.

**Produces:** Exact query strings, one-at-a-time API requests, and normalized Atom records.

- [ ] **Step 1: Write failing parser and pacing tests**

    from __future__ import annotations

    import unittest
    from datetime import UTC, datetime
    from pathlib import Path
    from unittest.mock import Mock

    from paperlib.arxiv import ArxivClient, build_search_query, parse_feed


    class ArxivTests(unittest.TestCase):
        def test_builds_date_range_query(self) -> None:
            value = build_search_query(
                "all:FPGA",
                "lastUpdatedDate",
                datetime(2026, 7, 13, tzinfo=UTC),
                datetime(2026, 7, 16, tzinfo=UTC),
            )
            self.assertIn("all:FPGA", value)
            self.assertIn("lastUpdatedDate:[202607130000+TO+202607160000]", value)

        def test_parses_versioned_entry(self) -> None:
            xml = Path("tests/fixtures/sample_feed.xml").read_bytes()
            page = parse_feed(xml, "q1", "2026-07-16T03:17:00Z")
            self.assertEqual(page.total_results, 1)
            paper = page.papers[0]
            self.assertEqual(paper.key, "2401.12345v2")
            self.assertEqual(paper.authors, ("Ada Lovelace", "Grace Hopper"))
            self.assertEqual(paper.pdf_url, "https://arxiv.org/pdf/2401.12345v2")
            self.assertEqual(paper.license_url, "http://creativecommons.org/licenses/by/4.0/")

        def test_waits_for_second_request(self) -> None:
            xml = Path("tests/fixtures/sample_feed.xml").read_bytes()
            opener = Mock(return_value=xml)
            clock = Mock(side_effect=[0.0, 0.0, 0.0, 3.0])
            sleeper = Mock()
            client = ArxivClient("https://example.invalid/api", "agent", 3.0, opener, clock, sleeper)
            client.fetch_page("all:FPGA", 0, 100, "submittedDate", "descending")
            client.fetch_page("all:FPGA", 100, 100, "submittedDate", "descending")
            sleeper.assert_called_once_with(3.0)


    if __name__ == "__main__":
        unittest.main()

Create a valid Atom fixture with namespaces:
- Atom: http://www.w3.org/2005/Atom
- OpenSearch: http://a9.com/-/spec/opensearch/1.1/
- arXiv: http://arxiv.org/schemas/atom

It must contain totalResults 1, ID http://arxiv.org/abs/2401.12345v2, title, summary, two author names, categories, primary category, published and updated timestamps, DOI, journal reference, license URL, and a PDF link.

- [ ] **Step 2: Run the test to verify it fails**

Run: python3 -m unittest discover -s tests -p 'test_arxiv.py' -v

Expected: FAIL because paperlib.arxiv does not exist.

- [ ] **Step 3: Implement the transport and parser**

Implement build_search_query as follows:

    def build_search_query(base_query, date_field=None, start=None, end=None):
        if date_field is None:
            return base_query
        if start is None or end is None:
            raise ValueError("date ranges require start and end")
        stamp = lambda item: item.astimezone(UTC).strftime("%Y%m%d%H%M")
        return f"({base_query}) AND {date_field}:[{stamp(start)}+TO+{stamp(end)}]"

Implement ArxivClient with injected opener, monotonic clock, and sleeper. fetch_page must:
1. reject max_results outside 1 through 100;
2. sleep for max(0, minimum_interval minus elapsed monotonic time);
3. URL-encode search_query, start, max_results, sortBy, and sortOrder;
4. send one blocking request with User-Agent;
5. record the monotonic request-start time;
6. parse the bytes with parse_feed using a UTC RFC 3339 retrieval time.

parse_feed must:
1. parse XML with ElementTree;
2. read opensearch:totalResults;
3. normalize whitespace in title and summary;
4. derive base ID and positive version from the final vN suffix in each Atom ID;
5. extract ordered author names, categories, primary category, DOI, journal reference, arxiv license, published, updated, and canonical abstract link;
6. make the canonical PDF URL https://arxiv.org/pdf/{base_id}v{version};
7. set query_ids to a one-element tuple containing the supplied query ID;
8. return FeedPage with papers in feed order.

- [ ] **Step 4: Run focused verification**

Run: python3 -m unittest discover -s tests -p 'test_arxiv.py' -v

Expected: PASS with three tests.

Run: python3 -m py_compile paperlib/arxiv.py

Expected: exit code 0.

- [ ] **Step 5: Commit**

    git add paperlib/arxiv.py tests/fixtures/sample_feed.xml tests/test_arxiv.py
    git commit -m "feat: parse paced arxiv feeds"

---

### Task 3: Atomically persist catalogue, survey, and watermark state

**Files:**
- Create: paperlib/storage.py
- Create: tests/test_storage.py

**Consumes:** PaperVersion and PdfCache.

**Produces:** Deterministic persistent research data with manual-cell preservation.

- [ ] **Step 1: Write failing storage tests**

    from __future__ import annotations

    import tempfile
    import unittest
    from pathlib import Path

    from paperlib.storage import load_survey, load_watermark, merge_survey_rows, write_state


    class StorageTests(unittest.TestCase):
        def test_merge_keeps_manual_values_and_adds_new_base_id(self) -> None:
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "survey.csv"
                path.write_text(
                    "arxiv_id,review_status,quantization,architecture,fpga_device,model,toolflow,evidence_pages,notes\n"
                    "2401.12345,reviewed,int8,systolic,U250,GPT-2,Vitis,4,keep this\n",
                    encoding="utf-8",
                )
                merge_survey_rows(path, ["2401.12345", "2501.00001"])
                rows = load_survey(path)
                self.assertEqual(rows["2401.12345"]["notes"], "keep this")
                self.assertEqual(rows["2501.00001"]["review_status"], "")

        def test_watermark_replaces_the_previous_value(self) -> None:
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "state.json"
                write_state(path, "2026-07-16T03:17:00Z")
                write_state(path, "2026-07-17T03:17:00Z")
                self.assertEqual(load_watermark(path), "2026-07-17T03:17:00Z")
                self.assertFalse((Path(directory) / ".state.json.tmp").exists())


    if __name__ == "__main__":
        unittest.main()

- [ ] **Step 2: Run the tests to verify they fail**

Run: python3 -m unittest discover -s tests -p 'test_storage.py' -v

Expected: FAIL because paperlib.storage does not exist.

- [ ] **Step 3: Implement all persistence rules**

Define SURVEY_FIELDS in this exact order:

    (
        "arxiv_id", "review_status", "quantization", "architecture",
        "fpga_device", "model", "toolflow", "evidence_pages", "notes",
    )

Implement atomic_write_text by creating the parent directory, writing to a sibling named .{filename}.tmp with UTF-8/newline="", then calling Path.replace on the final path.

write_catalog must emit schema_version 1, query_id, and a papers object keyed by PaperVersion.key. Serialize nested PdfCache with fields filename, sha256, byte_count, and downloaded_at. Sort records descending by updated_at then key and format JSON with sort_keys=True and indent=2. load_catalog must validate schema_version 1 and reconstruct exact dataclasses.

merge_survey_rows must read rows by arxiv_id, retain each existing value, add a blank row for each unseen base ID, sort by arxiv_id, and atomically rewrite the entire CSV with SURVEY_FIELDS. load_survey returns the keyed rows.

write_state must atomically write exactly:

    {"schema_version": 1, "last_successful_updated_at": "RFC3339-UTC"}

load_watermark returns None for a missing state file and the stored string otherwise.

- [ ] **Step 4: Run persistence verification**

Run: python3 -m unittest discover -s tests -p 'test_storage.py' -v

Expected: PASS with two tests.

Run: python3 -m unittest discover -s tests -p 'test_config.py' -v

Expected: PASS.

- [ ] **Step 5: Commit**

    git add paperlib/storage.py tests/test_storage.py
    git commit -m "feat: persist paper catalog and survey"

---

### Task 4: Cache PDF versions safely and idempotently

**Files:**
- Create: paperlib/cache.py
- Create: tests/test_cache.py

**Consumes:** PaperVersion, PdfCache, and ignored papers directory.

**Produces:** Valid local PDF receipts with no repeat download of a verified version.

- [ ] **Step 1: Write failing cache tests**

    from __future__ import annotations

    import tempfile
    import unittest
    from pathlib import Path

    from paperlib.cache import cache_pdf
    from paperlib.models import PaperVersion


    def make_paper() -> PaperVersion:
        return PaperVersion(
            arxiv_id="2401.12345", version=2, title="Title", abstract="Abstract",
            authors=(), categories=(), primary_category="cs.AR",
            published_at="2024-01-01T00:00:00Z", updated_at="2024-02-01T00:00:00Z",
            abs_url="https://arxiv.org/abs/2401.12345v2",
            pdf_url="https://arxiv.org/pdf/2401.12345v2", doi=None, journal_ref=None,
            license_url=None, query_ids=("q1",), retrieved_at="2026-07-16T00:00:00Z",
        )


    class CacheTests(unittest.TestCase):
        def test_downloads_once_and_records_receipt(self) -> None:
            with tempfile.TemporaryDirectory() as directory:
                calls = []
                def fetch(url: str) -> bytes:
                    calls.append(url)
                    return b"%PDF-1.7\nbody"
                first = cache_pdf(make_paper(), Path(directory), fetch, lambda: "2026-07-16T03:17:00Z")
                second = cache_pdf(first, Path(directory), fetch, lambda: "2026-07-16T03:18:00Z")
                self.assertEqual(calls, [make_paper().pdf_url])
                self.assertEqual(first.cache, second.cache)
                self.assertEqual(first.cache.filename, "2401.12345v2.pdf")

        def test_rejects_non_pdf_and_leaves_no_final_file(self) -> None:
            with tempfile.TemporaryDirectory() as directory:
                with self.assertRaisesRegex(ValueError, "PDF signature"):
                    cache_pdf(make_paper(), Path(directory), lambda url: b"<html>error</html>", lambda: "now")
                self.assertFalse((Path(directory) / "2401.12345v2.pdf").exists())


    if __name__ == "__main__":
        unittest.main()

- [ ] **Step 2: Run the tests to verify they fail**

Run: python3 -m unittest discover -s tests -p 'test_cache.py' -v

Expected: FAIL because paperlib.cache does not exist.

- [ ] **Step 3: Implement cache validation**

Use filename f"{paper.arxiv_id.replace('/', '_')}v{paper.version}.pdf".

A verified cache hit requires paper.cache, an existing final file, a matching byte count, and a matching SHA-256. Return the original PaperVersion without calling fetch when all four conditions hold.

On a miss, create papers/ if needed, write fetch(paper.pdf_url) to {filename}.part, reject empty content, reject content without b"%PDF-" in the first 1024 bytes, hash the complete bytes using hashlib.sha256, atomically rename the part file to final filename, build PdfCache with the current timestamp, and return dataclasses.replace(paper, cache=receipt). On any exception, remove the part file if it exists and leave no final file created by that attempt.

- [ ] **Step 4: Run cache verification**

Run: python3 -m unittest discover -s tests -p 'test_cache.py' -v

Expected: PASS with two tests.

Run: git check-ignore papers/2401.12345v2.pdf

Expected: exit code 0.

- [ ] **Step 5: Commit**

    git add paperlib/cache.py tests/test_cache.py
    git commit -m "feat: cache arxiv pdfs safely"

---

### Task 5: Orchestrate full-history bootstrap and daily updates

**Files:**
- Create: paperlib/collector.py
- Create: tests/test_collector.py

**Consumes:** configuration, ArxivClient, storage, cache, and renderer interfaces.

**Produces:** Correct idempotent bootstrap and sync workflows, including revisions and safe watermark advancement.

- [ ] **Step 1: Write failing orchestration tests**

Create a FakeClient class in tests/test_collector.py with fetch_page that records search_query, start, and sort_by and returns FeedPage objects from a list.

Write these three tests:
1. bootstrap with two identical v1 responses and one v2 response yields exactly keys 2401.12345v1 and 2401.12345v2 and exactly one survey base-ID row;
2. sync with a seeded watermark 2026-07-16T03:17:00Z asks for lastUpdatedDate beginning at 2026-07-13T03:17:00Z, then advances state only after writing a successful catalogue;
3. a page whose total_results is 2000 causes two smaller submittedDate query windows and completes when both subwindows return less than 2000.

Build test records with the Task 4 make_paper pattern. Set download=False for all these tests so the fake client is the only external dependency.

Use these concrete helper definitions at the top of tests/test_collector.py:

    def paper(version: int, updated: str) -> PaperVersion:
        return PaperVersion(
            arxiv_id="2401.12345", version=version, title=f"Title v{version}",
            abstract="Abstract", authors=("Ada",), categories=("cs.AR",),
            primary_category="cs.AR", published_at="2024-01-01T00:00:00Z",
            updated_at=updated, abs_url=f"https://arxiv.org/abs/2401.12345v{version}",
            pdf_url=f"https://arxiv.org/pdf/2401.12345v{version}", doi=None,
            journal_ref=None, license_url=None, query_ids=("q1",),
            retrieved_at="2026-07-16T03:17:00Z",
        )

    class FakeClient:
        def __init__(self, pages: list[FeedPage]) -> None:
            self.pages = pages
            self.calls: list[tuple[str, int, str]] = []

        def fetch_page(self, search_query, start, max_results, sort_by, sort_order):
            self.calls.append((search_query, start, sort_by))
            if self.pages:
                return self.pages.pop(0)
            return FeedPage(total_results=0, papers=())

For the duplicate/version test, give FakeClient these pages in order:

    [
        FeedPage(3, (paper(1, "2024-01-01T00:00:00Z"),)),
        FeedPage(3, (paper(1, "2024-01-01T00:00:00Z"),)),
        FeedPage(3, (paper(2, "2024-02-01T00:00:00Z"),)),
        FeedPage(3, ()),
    ]

- [ ] **Step 2: Run the tests to verify they fail**

Run: python3 -m unittest discover -s tests -p 'test_collector.py' -v

Expected: FAIL because paperlib.collector does not exist.

- [ ] **Step 3: Implement merging, recursive windows, and write order**

Implement merge_papers(existing, incoming):
- key by PaperVersion.key;
- for an existing exact-version key, preserve a verified existing cache receipt when incoming.cache is None;
- union query_ids in sorted order;
- retain metadata from the PaperVersion with later retrieved_at;
- for a new version, retain both versions.

bootstrap_all must:
1. load config, catalogue, and survey;
2. query submittedDate from 2007-01-01T00:00:00Z to supplied now;
3. page every range in configured page_size increments;
4. when a first page reports total_results at least 2000, split its time range at the UTC midpoint and recurse;
5. raise ValueError when a one-minute-or-smaller range still reports 2000 results;
6. merge all records, add survey rows, optionally cache every missing version, write catalogue, write survey, render/write README, and return the catalogue;
7. not write a daily watermark during bootstrap.

sync_recent must:
1. load config and state;
2. choose start as stored watermark minus daily_overlap_hours, or now minus daily_overlap_hours when state is absent;
3. query lastUpdatedDate from start through now;
4. merge records, add survey rows, optionally cache missing versions, write catalogue, write survey, and render/write README;
5. write state using the newest processed updated_at or now only after all prior writes succeed;
6. leave the pre-existing watermark untouched if a fetch, parse, cache, catalogue, survey, or render operation raises.

- [ ] **Step 4: Run orchestration tests**

Run: python3 -m unittest discover -s tests -p 'test_collector.py' -v

Expected: PASS with three tests.

Run: python3 -m unittest discover -s tests -p 'test_arxiv.py' -v

Expected: PASS.

- [ ] **Step 5: Commit**

    git add paperlib/collector.py tests/test_collector.py
    git commit -m "feat: sync arxiv paper catalog"

---

### Task 6: Render the survey and add collector CLI commands

**Files:**
- Create: paperlib/render.py
- Create: paperlib/cli.py
- Create: scripts/collect_arxiv.py
- Create: tests/test_render.py
- Create: tests/test_cli.py

**Consumes:** Persistent catalogue/survey and collector functions.

**Produces:** Deterministic README output plus bootstrap, sync, download, and render commands.

- [ ] **Step 1: Write failing render and CLI tests**

The render test must assert all of these:
- a versioned arXiv abstract URL is present;
- the official PDF URL is present;
- manual quantization and FPGA values are present;
- no papers/{id}.pdf cache path is present;
- rows sort by updated_at descending then PaperVersion.key.

The CLI test must use subprocess with sys.executable and:

    python3 scripts/collect_arxiv.py --repo-root TEMP_ROOT render

Seed TEMP_ROOT/data/catalog.json and TEMP_ROOT/data/survey.csv with their Task 1 empty contents. Assert return code 0 and TEMP_ROOT/README.md exists. Add a second test that a nonexistent repo root returns a nonzero code and reports config/query.json in stderr.

Use this exact render assertion after creating a PaperVersion with updated_at
2024-02-01T00:00:00Z and survey fields quantization=int8 and fpga_device=U250:

    rendered = render_readme({paper.key: paper}, {paper.arxiv_id: survey_row})
    self.assertIn("https://arxiv.org/abs/2401.12345v2", rendered)
    self.assertIn("https://arxiv.org/pdf/2401.12345v2", rendered)
    self.assertIn("int8", rendered)
    self.assertIn("U250", rendered)
    self.assertNotIn("papers/2401.12345v2.pdf", rendered)

- [ ] **Step 2: Run the tests to verify they fail**

Run: python3 -m unittest discover -s tests -p 'test_render.py' -v

Expected: FAIL because paperlib.render does not exist.

Run: python3 -m unittest discover -s tests -p 'test_cli.py' -v

Expected: FAIL because scripts/collect_arxiv.py does not exist.

- [ ] **Step 3: Implement deterministic rendering and argument dispatch**

render_readme must generate:
1. a fixed local-research/cache-and-rights header;
2. a Markdown table with columns Paper, Submitted, Updated, Categories, Status, Quantization, Architecture, FPGA, Model, Toolflow, Evidence, Notes;
3. a title linked to abs_url and a separate official PDF link;
4. escaped vertical bars and newlines in all user/content cells;
5. no local cache filename or absolute local path.

paperlib.cli must define parser subcommands:
- bootstrap with required --all and optional --download;
- sync with optional --download-new;
- download with no network discovery;
- render with no network.

All commands accept --repo-root defaulting to the project root. Validate config/query.json, data/catalog.json, and data/survey.csv before dispatch. download must iterate only versions without a verified cache receipt. scripts/collect_arxiv.py must insert the repository root at sys.path[0], import paperlib.cli.main, and call raise SystemExit(main()).

- [ ] **Step 4: Run CLI and full offline tests**

Run: python3 -m unittest discover -s tests -p 'test_render.py' -v

Expected: PASS.

Run: python3 -m unittest discover -s tests -p 'test_cli.py' -v

Expected: PASS.

Run: python3 -m unittest discover -s tests -v

Expected: PASS without live network access.

- [ ] **Step 5: Commit**

    git add paperlib/render.py paperlib/cli.py scripts/collect_arxiv.py tests/test_render.py tests/test_cli.py
    git commit -m "feat: add paper collection cli"

---

### Task 7: Add explicit managed user-cron installation and removal

**Files:**
- Create: paperlib/cron.py
- Create: scripts/install_cron.py
- Create: tests/test_cron.py

**Consumes:** QueryConfig cron time and collector CLI path.

**Produces:** Previewable, idempotent, non-overlapping daily cron management.

- [ ] **Step 1: Write failing crontab text tests**

    import unittest
    from pathlib import Path

    from paperlib.cron import MANAGED_MARKER, build_cron_line, merge_crontab, remove_managed_entry


    class CronTests(unittest.TestCase):
        def test_builds_locked_daily_command(self) -> None:
            line = build_cron_line(Path("/repo"), Path("/usr/bin/python3"), 3, 17)
            self.assertTrue(line.startswith("17 3 * * * "))
            self.assertIn("/usr/bin/flock -n /repo/state/collector.lock", line)
            self.assertIn("/usr/bin/python3 /repo/scripts/collect_arxiv.py", line)
            self.assertIn("sync --download-new", line)
            self.assertTrue(line.endswith(MANAGED_MARKER))

        def test_merge_and_remove_preserve_other_entries(self) -> None:
            original = "0 1 * * * /usr/local/bin/backup\n"
            line = "17 3 * * * run # LLM-inference-on-FPGA-papers"
            merged = merge_crontab(original, line)
            self.assertEqual(merge_crontab(merged, line), merged)
            self.assertEqual(remove_managed_entry(merged), original)


    if __name__ == "__main__":
        unittest.main()

- [ ] **Step 2: Run the test to verify it fails**

Run: python3 -m unittest discover -s tests -p 'test_cron.py' -v

Expected: FAIL because paperlib.cron does not exist.

- [ ] **Step 3: Implement exact cron handling**

Set:

    MANAGED_MARKER = "# LLM-inference-on-FPGA-papers"

build_cron_line must return one line in this exact form:

    {minute} {hour} * * * /usr/bin/flock -n {repo}/state/collector.lock {python} {repo}/scripts/collect_arxiv.py --repo-root {repo} sync --download-new >> {repo}/logs/cron.log 2>&1 # LLM-inference-on-FPGA-papers

merge_crontab must remove all prior lines containing MANAGED_MARKER, preserve all other lines byte-for-byte, append exactly one managed line and a trailing newline. remove_managed_entry must remove only marker-bearing lines and retain a single trailing newline when any unmarked line remains.

scripts/install_cron.py must:
1. accept --repo-root, --install, and --remove, with --install and --remove mutually exclusive;
2. print the proposed managed line without changing crontab when neither flag is provided;
3. run crontab -l and treat exit code 1 with empty stdout as an empty crontab;
4. surface any other failing crontab command as stderr/nonzero;
5. on --install or --remove, print the resulting crontab text, create state and logs directories, then send that text to crontab -;
6. resolve sys.executable to a real absolute Python path;
7. never invoke the collector while changing crontab.

- [ ] **Step 4: Run cron verification**

Run: python3 -m unittest discover -s tests -p 'test_cron.py' -v

Expected: PASS with two tests.

Run: python3 scripts/install_cron.py --help

Expected: exit code 0 and --install plus --remove in help text.

- [ ] **Step 5: Commit**

    git add paperlib/cron.py scripts/install_cron.py tests/test_cron.py
    git commit -m "feat: add daily paper collector cron installer"

---

### Task 8: Document use, rights boundary, and full verification

**Files:**
- Create/Modify: README.md
- Modify: tests/test_cli.py
- Modify: docs/superpowers/specs/2026-07-16-arxiv-paper-library-design.md only for an implementation-discovered factual correction

**Consumes:** The complete collector.

**Produces:** Reproducible onboarding and final implementation evidence.

- [ ] **Step 1: Write failing README requirements test**

Add a test to tests/test_cli.py asserting README.md contains:
- python3 scripts/collect_arxiv.py bootstrap --all --download
- python3 scripts/collect_arxiv.py sync --download-new
- python3 scripts/collect_arxiv.py render
- python3 scripts/install_cron.py --install
- the phrase local research cache
- https://info.arxiv.org/help/api/user-manual.html
- https://info.arxiv.org/help/api/tou.html

Use this complete assertion body:

    def test_readme_documents_required_workflow(self) -> None:
        text = Path("README.md").read_text(encoding="utf-8")
        self.assertIn("bootstrap --all --download", text)
        self.assertIn("sync --download-new", text)
        self.assertIn("python3 scripts/install_cron.py --install", text)
        self.assertIn("local research cache", text)
        self.assertIn("https://info.arxiv.org/help/api/user-manual.html", text)
        self.assertIn("https://info.arxiv.org/help/api/tou.html", text)

- [ ] **Step 2: Run the test to verify it fails**

Run: python3 -m unittest discover -s tests -p 'test_cli.py' -v

Expected: FAIL until the static header is added to README rendering.

- [ ] **Step 3: Add exact user documentation**

Ensure the generated README begins with:

    # LLM inference on FPGA papers

    This repository is a local research survey of arXiv-hosted papers concerning
    LLM inference on FPGAs. data/catalog.json and data/survey.csv are tracked;
    papers/ is an ignored local research cache and must not be re-hosted.

    ## Commands

        python3 scripts/collect_arxiv.py bootstrap --all --download
        python3 scripts/collect_arxiv.py sync --download-new
        python3 scripts/collect_arxiv.py render
        python3 scripts/install_cron.py --install

    The collector serializes arXiv API calls at least three seconds apart. See
    the arXiv API manual at https://info.arxiv.org/help/api/user-manual.html and
    the terms of use at https://info.arxiv.org/help/api/tou.html. Public
    availability does not itself grant redistribution rights for a PDF.

Run render against the checked-in empty catalogue; it must succeed without a network request.

- [ ] **Step 4: Run final verification**

Run: python3 -m unittest discover -s tests -v

Expected: PASS with no live API access.

Run: python3 -m py_compile paperlib/*.py scripts/*.py

Expected: exit code 0.

Run: git diff --check

Expected: no whitespace errors.

Run: git status --short

Expected: no papers, state, logs, or .part files are tracked.

- [ ] **Step 5: Commit**

    git add README.md tests/test_cli.py
    git commit -m "docs: explain paper library workflow"

---

## Plan Self-Review

### Spec coverage

- Separate repository, ignored local PDF cache, tracked catalogue and survey: Tasks 1 and 3.
- arXiv-only query and three-second serialized request limit: Task 2.
- Full-history bootstrap, 2,000-result splitting, and update overlap: Task 5.
- Exact-version deduplication, revision retention, PDF validation, hashing, and no repeat downloads: Tasks 4 and 5.
- Manual fields for quantization, architecture, FPGA device, model, toolflow, evidence, and notes: Tasks 3 and 6.
- Daily locked user cron with preview, install, and remove: Task 7.
- Atomic write/error behavior, offline tests, and legal/local-cache documentation: Tasks 3 through 8.

### Placeholder scan

Every task identifies exact paths, named interfaces, commands, test behavior, error conditions, and commit messages. The plan contains no deferred implementation markers; test fixture records in Task 5 must be concrete PaperVersion instances following the fully specified Task 4 constructor.

### Type consistency

All layers use QueryConfig, PaperVersion, PdfCache, FeedPage, PaperVersion.key, a version-keyed catalogue, and a base-ID-keyed survey. The CLI and cron installer target the same scripts/collect_arxiv.py command and the same repository-root argument.
