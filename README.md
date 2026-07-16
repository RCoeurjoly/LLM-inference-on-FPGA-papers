# LLM inference on FPGA papers

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
