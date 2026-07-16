from __future__ import annotations

import unittest

from paperlib.models import PaperVersion
from paperlib.render import render_readme


def make_paper(arxiv_id: str, version: int, updated_at: str, title: str) -> PaperVersion:
    return PaperVersion(
        arxiv_id=arxiv_id,
        version=version,
        title=title,
        abstract="Abstract",
        authors=("Ada",),
        categories=("cs.AR",),
        primary_category="cs.AR",
        published_at="2024-01-01T00:00:00Z",
        updated_at=updated_at,
        abs_url=f"https://arxiv.org/abs/{arxiv_id}v{version}",
        pdf_url=f"https://arxiv.org/pdf/{arxiv_id}v{version}",
        doi=None,
        journal_ref=None,
        license_url=None,
        query_ids=("query-v1",),
        retrieved_at="2026-07-16T00:00:00Z",
    )


class RenderTests(unittest.TestCase):
    def test_renders_links_survey_fields_and_no_local_pdf_path(self) -> None:
        newer = make_paper("2401.12345", 2, "2024-02-01T00:00:00Z", "Newer")
        older = make_paper("2401.00001", 1, "2024-01-01T00:00:00Z", "Older")
        survey = {
            newer.arxiv_id: {
                "arxiv_id": newer.arxiv_id,
                "review_status": "reviewed",
                "quantization": "int8",
                "architecture": "systolic",
                "fpga_device": "U250",
                "model": "GPT-2",
                "toolflow": "Vitis",
                "evidence_pages": "4",
                "notes": "checked",
            }
        }

        rendered = render_readme({older.key: older, newer.key: newer}, survey)

        self.assertIn("https://arxiv.org/abs/2401.12345v2", rendered)
        self.assertIn("https://arxiv.org/pdf/2401.12345v2", rendered)
        self.assertIn("int8", rendered)
        self.assertIn("U250", rendered)
        self.assertNotIn("papers/2401.12345v2.pdf", rendered)
        self.assertLess(rendered.index("Newer"), rendered.index("Older"))


if __name__ == "__main__":
    unittest.main()
