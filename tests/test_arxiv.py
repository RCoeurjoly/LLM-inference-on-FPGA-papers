from __future__ import annotations

import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock

from paperlib.arxiv import ArxivClient, build_search_query, parse_feed


FIXTURE = Path("tests/fixtures/sample_feed.xml").read_bytes()


class ArxivTests(unittest.TestCase):
    def test_builds_updated_date_query_with_spaces_for_url_encoding(self) -> None:
        query = build_search_query(
            "all:FPGA",
            "lastUpdatedDate",
            datetime(2026, 7, 13, tzinfo=UTC),
            datetime(2026, 7, 16, tzinfo=UTC),
        )

        self.assertIn("all:FPGA", query)
        self.assertIn("lastUpdatedDate:[202607130000 TO 202607160000]", query)
        self.assertNotIn("+TO+", query)

    def test_parses_base_id_version_metadata_and_links(self) -> None:
        page = parse_feed(FIXTURE, "query-v1", "2026-07-16T03:17:00Z")

        self.assertEqual(page.total_results, 1)
        paper = page.papers[0]
        self.assertEqual(paper.arxiv_id, "2401.12345")
        self.assertEqual(paper.version, 2)
        self.assertEqual(paper.title, "FPGA LLM Inference")
        self.assertEqual(paper.abstract, "A normalized abstract.")
        self.assertEqual(paper.authors, ("Ada Lovelace", "Grace Hopper"))
        self.assertEqual(paper.categories, ("cs.AR", "cs.LG"))
        self.assertEqual(paper.primary_category, "cs.AR")
        self.assertEqual(paper.abs_url, "https://arxiv.org/abs/2401.12345v2")
        self.assertEqual(paper.pdf_url, "https://arxiv.org/pdf/2401.12345v2")
        self.assertEqual(paper.doi, "10.1000/example")
        self.assertEqual(paper.journal_ref, "Example Journal 1 (2024)")
        self.assertEqual(paper.license_url, "http://creativecommons.org/licenses/by/4.0/")

    def test_waits_before_a_second_api_request(self) -> None:
        opener = Mock(return_value=FIXTURE)
        clock = Mock(side_effect=[0.0, 0.0, 3.0])
        sleeper = Mock()
        client = ArxivClient(
            "https://example.invalid/api",
            "agent",
            3.0,
            opener,
            clock,
            sleeper,
        )

        client.fetch_page("all:FPGA", 0, 100, "submittedDate", "descending")
        client.fetch_page("all:FPGA", 100, 100, "submittedDate", "descending")

        sleeper.assert_called_once_with(3.0)
        self.assertEqual(opener.call_count, 2)


if __name__ == "__main__":
    unittest.main()
