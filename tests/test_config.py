from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from paperlib.config import load_config
from paperlib.models import PaperVersion


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

    def test_paper_key_keeps_base_id_and_version(self) -> None:
        paper = PaperVersion(
            arxiv_id="2401.12345",
            version=2,
            title="Title",
            abstract="Abstract",
            authors=("Ada",),
            categories=("cs.AR",),
            primary_category="cs.AR",
            published_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-02T00:00:00Z",
            abs_url="https://arxiv.org/abs/2401.12345v2",
            pdf_url="https://arxiv.org/pdf/2401.12345v2",
            doi=None,
            journal_ref=None,
            license_url=None,
            query_ids=("llm-inference-fpga-v1",),
            retrieved_at="2026-07-16T00:00:00Z",
        )

        self.assertEqual(paper.key, "2401.12345v2")


if __name__ == "__main__":
    unittest.main()
