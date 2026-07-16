from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from paperlib.models import PaperVersion, PdfCache
from paperlib.storage import (
    load_catalog,
    load_survey,
    load_watermark,
    merge_survey_values,
    merge_survey_rows,
    write_survey,
    write_catalog,
    write_state,
)


def make_paper() -> PaperVersion:
    return PaperVersion(
        arxiv_id="2401.12345",
        version=2,
        title="Title",
        abstract="Abstract",
        authors=("Ada",),
        categories=("cs.AR",),
        primary_category="cs.AR",
        published_at="2024-01-01T00:00:00Z",
        updated_at="2024-02-01T00:00:00Z",
        abs_url="https://arxiv.org/abs/2401.12345v2",
        pdf_url="https://arxiv.org/pdf/2401.12345v2",
        doi=None,
        journal_ref=None,
        license_url="https://creativecommons.org/licenses/by/4.0/",
        query_ids=("query-v1",),
        retrieved_at="2026-07-16T00:00:00Z",
        cache=PdfCache(
            filename="2401.12345v2.pdf",
            sha256="abc123",
            byte_count=42,
            downloaded_at="2026-07-16T00:01:00Z",
        ),
    )


class StorageTests(unittest.TestCase):
    def test_merge_adds_missing_rows_without_erasing_notes(self) -> None:
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
            self.assertEqual(rows["2401.12345"]["quantization"], "int8")
            self.assertEqual(rows["2501.00001"]["review_status"], "")

    def test_watermark_write_is_replace_not_append(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            write_state(path, "2026-07-16T03:17:00Z")
            write_state(path, "2026-07-17T03:17:00Z")

            self.assertEqual(load_watermark(path), "2026-07-17T03:17:00Z")
            self.assertFalse((Path(directory) / ".state.json.tmp").exists())

    def test_catalog_round_trip_preserves_cache_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            paper = make_paper()

            write_catalog(path, "query-v1", {paper.key: paper})

            self.assertEqual(load_catalog(path), {paper.key: paper})

    def test_pure_survey_merge_can_be_written_after_other_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "survey.csv"
            original = {
                "2401.12345": {
                    "arxiv_id": "2401.12345",
                    "review_status": "reviewed",
                    "quantization": "int8",
                    "architecture": "",
                    "fpga_device": "",
                    "model": "",
                    "toolflow": "",
                    "evidence_pages": "",
                    "notes": "preserve",
                }
            }

            merged = merge_survey_values(original, ["2401.12345", "2501.00001"])
            write_survey(path, merged)

            self.assertEqual(original, {"2401.12345": original["2401.12345"]})
            self.assertEqual(load_survey(path)["2401.12345"]["notes"], "preserve")
            self.assertEqual(load_survey(path)["2501.00001"]["quantization"], "")


if __name__ == "__main__":
    unittest.main()
