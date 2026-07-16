from __future__ import annotations

from collections.abc import Mapping

from paperlib.models import PaperVersion


HEADER = """# LLM inference on FPGA papers

This repository is a local research survey of arXiv-hosted papers concerning
LLM inference on FPGAs. `data/catalog.json` and `data/survey.csv` are tracked;
`papers/` is an ignored local research cache and must not be re-hosted.

## Commands

```sh
python3 scripts/collect_arxiv.py bootstrap --all --download
python3 scripts/collect_arxiv.py sync --download-new
python3 scripts/collect_arxiv.py render
python3 scripts/install_cron.py --install
```

The collector serializes arXiv API calls at least three seconds apart. See the
arXiv API manual at https://info.arxiv.org/help/api/user-manual.html and the
terms of use at https://info.arxiv.org/help/api/tou.html. Public availability
does not itself grant redistribution rights for a PDF.

## Survey

| Paper | Submitted | Updated | Categories | Status | Quantization | Architecture | FPGA | Model | Toolflow | Evidence | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
"""


def _cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def _survey_value(row: Mapping[str, str] | None, field: str) -> str:
    if row is None:
        return ""
    return row.get(field, "")


def render_readme(
    papers: Mapping[str, PaperVersion], survey: Mapping[str, Mapping[str, str]]
) -> str:
    """Render a deterministic survey index without exposing local file paths."""
    rows: list[str] = []
    ordered_papers = sorted(
        papers.values(), key=lambda paper: (paper.updated_at, paper.key), reverse=True
    )
    for paper in ordered_papers:
        annotation = survey.get(paper.arxiv_id)
        paper_link = f"[{_cell(paper.title)}]({paper.abs_url}) ([PDF]({paper.pdf_url}))"
        cells = (
            paper_link,
            _cell(paper.published_at),
            _cell(paper.updated_at),
            _cell(", ".join(paper.categories)),
            _cell(_survey_value(annotation, "review_status")),
            _cell(_survey_value(annotation, "quantization")),
            _cell(_survey_value(annotation, "architecture")),
            _cell(_survey_value(annotation, "fpga_device")),
            _cell(_survey_value(annotation, "model")),
            _cell(_survey_value(annotation, "toolflow")),
            _cell(_survey_value(annotation, "evidence_pages")),
            _cell(_survey_value(annotation, "notes")),
        )
        rows.append("| " + " | ".join(cells) + " |")
    return HEADER + "\n".join(rows) + ("\n" if rows else "")
