from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from paperlib.cache import cache_pdf
from paperlib.models import PaperVersion


def make_paper() -> PaperVersion:
    return PaperVersion(
        arxiv_id="2401.12345",
        version=2,
        title="Title",
        abstract="Abstract",
        authors=(),
        categories=(),
        primary_category="cs.AR",
        published_at="2024-01-01T00:00:00Z",
        updated_at="2024-02-01T00:00:00Z",
        abs_url="https://arxiv.org/abs/2401.12345v2",
        pdf_url="https://arxiv.org/pdf/2401.12345v2",
        doi=None,
        journal_ref=None,
        license_url=None,
        query_ids=("q",),
        retrieved_at="2026-07-16T00:00:00Z",
    )


class CacheTests(unittest.TestCase):
    def test_downloads_once_and_records_a_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            calls: list[str] = []

            def fetch(url: str) -> bytes:
                calls.append(url)
                return b"%PDF-1.7\nbody"

            cached = cache_pdf(
                make_paper(), Path(directory), fetch, lambda: "2026-07-16T03:17:00Z"
            )
            repeated = cache_pdf(
                cached, Path(directory), fetch, lambda: "2026-07-16T03:18:00Z"
            )

            self.assertEqual(calls, [make_paper().pdf_url])
            self.assertEqual(cached.cache, repeated.cache)
            self.assertEqual(cached.cache.filename, "2401.12345v2.pdf")
            self.assertEqual(cached.cache.byte_count, len(b"%PDF-1.7\nbody"))

    def test_rejects_non_pdf_and_leaves_no_final_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cache_dir = Path(directory)

            with self.assertRaisesRegex(ValueError, "PDF signature"):
                cache_pdf(
                    make_paper(),
                    cache_dir,
                    lambda url: b"<html>error</html>",
                    lambda: "now",
                )

            self.assertFalse((cache_dir / "2401.12345v2.pdf").exists())
            self.assertFalse((cache_dir / "2401.12345v2.pdf.part").exists())


if __name__ == "__main__":
    unittest.main()
