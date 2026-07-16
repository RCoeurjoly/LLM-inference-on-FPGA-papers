from __future__ import annotations

import shutil
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from paperlib.collector import bootstrap_all, download_missing, sync_recent
from paperlib.models import FeedPage, PaperVersion
from paperlib.storage import (
    load_catalog,
    load_survey,
    load_watermark,
    write_catalog,
    write_state,
)


def paper(version: int, updated_at: str) -> PaperVersion:
    return PaperVersion(
        arxiv_id="2401.12345",
        version=version,
        title=f"Title v{version}",
        abstract="Abstract",
        authors=("Ada",),
        categories=("cs.AR",),
        primary_category="cs.AR",
        published_at="2024-01-01T00:00:00Z",
        updated_at=updated_at,
        abs_url=f"https://arxiv.org/abs/2401.12345v{version}",
        pdf_url=f"https://arxiv.org/pdf/2401.12345v{version}",
        doi=None,
        journal_ref=None,
        license_url=None,
        query_ids=("query-v1",),
        retrieved_at="2026-07-16T03:17:00Z",
    )


class FakeClient:
    def __init__(self, pages: list[FeedPage]) -> None:
        self.pages = list(pages)
        self.calls: list[tuple[str, int, str]] = []

    def fetch_page(
        self, search_query: str, start: int, max_results: int, sort_by: str, sort_order: str
    ) -> FeedPage:
        self.calls.append((search_query, start, sort_by))
        if self.pages:
            return self.pages.pop(0)
        return FeedPage(total_results=0, papers=())


def create_repo(root: Path) -> None:
    (root / "config").mkdir(parents=True)
    (root / "data").mkdir()
    shutil.copyfile("config/query.json", root / "config/query.json")
    (root / "data/catalog.json").write_text(
        '{"schema_version": 1, "query_id": "llm-inference-fpga-v1", "papers": {}}\n',
        encoding="utf-8",
    )
    (root / "data/survey.csv").write_text(
        "arxiv_id,review_status,quantization,architecture,fpga_device,model,toolflow,evidence_pages,notes\n",
        encoding="utf-8",
    )


class CollectorTests(unittest.TestCase):
    def test_bootstrap_merges_versions_and_does_not_duplicate_exact_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            create_repo(root)
            client = FakeClient(
                [
                    FeedPage(3, (paper(1, "2024-01-01T00:00:00Z"),)),
                    FeedPage(3, (paper(1, "2024-01-01T00:00:00Z"),)),
                    FeedPage(3, (paper(2, "2024-02-01T00:00:00Z"),)),
                ]
            )

            result = bootstrap_all(
                root,
                download=False,
                now=datetime(2026, 7, 16, 3, 17, tzinfo=UTC),
                client=client,
            )

            self.assertEqual(set(result), {"2401.12345v1", "2401.12345v2"})
            self.assertEqual(set(load_catalog(root / "data/catalog.json")), set(result))
            self.assertEqual(set(load_survey(root / "data/survey.csv")), {"2401.12345"})
            self.assertTrue((root / "README.md").exists())

    def test_sync_uses_last_updated_overlap_and_advances_watermark_after_success(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            create_repo(root)
            state_path = root / "state/collector.json"
            write_state(state_path, "2026-07-16T03:17:00Z")
            client = FakeClient([FeedPage(1, (paper(1, "2026-07-16T04:00:00Z"),))])

            sync_recent(
                root,
                download_new=False,
                now=datetime(2026, 7, 16, 3, 17, tzinfo=UTC),
                client=client,
            )

            self.assertIn(
                "lastUpdatedDate:[202607130317 TO 202607160317]", client.calls[0][0]
            )
            self.assertEqual(load_watermark(state_path), "2026-07-16T04:00:00Z")

    def test_bootstrap_splits_a_result_limit_window(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            create_repo(root)
            client = FakeClient(
                [
                    FeedPage(2000, ()),
                    FeedPage(1, (paper(1, "2024-01-01T00:00:00Z"),)),
                    FeedPage(1, (paper(2, "2024-02-01T00:00:00Z"),)),
                ]
            )

            result = bootstrap_all(
                root,
                download=False,
                now=datetime(2026, 7, 16, 3, 17, tzinfo=UTC),
                client=client,
            )

            self.assertEqual(set(result), {"2401.12345v1", "2401.12345v2"})
            self.assertEqual(len(client.calls), 3)
            self.assertNotEqual(client.calls[1][0], client.calls[2][0])

    def test_sync_does_not_advance_watermark_when_rendering_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            create_repo(root)
            state_path = root / "state/collector.json"
            write_state(state_path, "2026-07-16T03:17:00Z")
            client = FakeClient([FeedPage(1, (paper(1, "2026-07-16T04:00:00Z"),))])

            with self.assertRaisesRegex(RuntimeError, "render failed"):
                sync_recent(
                    root,
                    download_new=False,
                    now=datetime(2026, 7, 16, 3, 17, tzinfo=UTC),
                    client=client,
                    renderer=lambda papers, survey: (_ for _ in ()).throw(
                        RuntimeError("render failed")
                    ),
                )

            self.assertEqual(load_watermark(state_path), "2026-07-16T03:17:00Z")

    def test_download_missing_uses_catalog_without_discovery(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            create_repo(root)
            source = paper(1, "2024-01-01T00:00:00Z")
            write_catalog(root / "data/catalog.json", "query-v1", {source.key: source})
            calls: list[str] = []

            result = download_missing(
                root,
                pdf_fetcher=lambda url: calls.append(url) or b"%PDF-1.7\nbody",
                now=datetime(2026, 7, 16, 3, 17, tzinfo=UTC),
            )

            self.assertEqual(calls, [source.pdf_url])
            self.assertIsNotNone(result[source.key].cache)
            self.assertFalse((root / "state/collector.json").exists())


if __name__ == "__main__":
    unittest.main()
