# arXiv FPGA–LLM Paper Library Design

## Status and objective

**Status:** approved design.

Create a local Git repository at
`~/LLM-inference-on-FPGA-papers` for a durable survey of arXiv-hosted papers
about LLM inference on FPGAs. Its purpose is to make practical comparisons
quick: quantization methods, architectures, FPGA devices, models, and tool
flows.

The repository tracks reproducible discovery metadata and human research
notes. It keeps downloaded PDFs in an ignored local cache so they are
available for reading without making the repository large or re-serving papers
to others.

## Scope and boundaries

The first version has exactly one discovery source: the arXiv API. The query
matches LLM (including “large language model”), inference, and FPGA in a
paper's title or abstract. The initial bootstrap searches the full matching
history; the daily update searches for newly submitted or updated matching
records.

The versioned default query is:

```text
(ti:LLM OR abs:LLM OR ti:LLMs OR abs:LLMs
 OR ti:"large language model" OR abs:"large language model"
 OR ti:"large language models" OR abs:"large language models")
AND (ti:inference OR abs:inference)
AND (ti:FPGA OR abs:FPGA)
```

The collector URL-encodes this expression rather than embedding a hand-built
request URL. A future query change receives a stable query identifier in the
catalogue, so the provenance of every discovered record remains visible.

“Open access” in this project means a PDF is publicly available from arXiv for
local research use. The collector must not infer a redistribution licence from
that availability, publish cached PDFs, or serve them over HTTP. It records an
explicit licence URL when arXiv provides one and otherwise preserves only the
official arXiv links and local-cache status.

Non-goals for version 1:

- publisher-site scraping or downloading;
- OpenAlex, CORE, Semantic Scholar, or other discovery sources;
- automatic claims about a paper's quantization, architecture, or device;
- a web application, database server, or hosted PDF library.

## Repository layout

```text
LLM-inference-on-FPGA-papers/
  README.md                         generated human-readable index
  config/query.json                 versioned search and operational settings
  scripts/collect_arxiv.py          collector CLI, Python standard library only
  scripts/install_cron.py           explicit user-crontab installer/remover
  data/catalog.json                 versioned canonical arXiv metadata
  data/survey.csv                   versioned human-curated technical findings
  papers/                           ignored local PDF cache
  state/                            ignored watermarks, lock, and run records
  logs/                             ignored cron logs
  tests/                            offline unittest fixtures and tests
  docs/superpowers/specs/           design and later implementation plan
```

`.gitignore` excludes `papers/`, `state/`, `logs/`, temporary downloads, Python
bytecode, and local virtual environments. It does **not** exclude the catalogue
or survey, which are the useful, shareable research record.

## Data model

`data/catalog.json` is the source of truth for machine-collected metadata. Each
versioned arXiv manifestation records at least:

- base arXiv ID and version;
- title, abstract, ordered authors, categories, and primary category;
- submitted and last-updated timestamps;
- arXiv abstract URL, versioned official PDF URL, DOI, journal reference, and
  arXiv licence URL when supplied;
- source query identifiers and retrieval time;
- local PDF cache state, filename, SHA-256, byte count, and download time.

The identity key is `(base_arxiv_id, version)`. The base ID groups revisions;
two fetches of the same version are one record. A new revision is distinct
content and may be cached as a separate file, for example
`papers/2401.12345v2.pdf`.

`data/survey.csv` has one row per base arXiv ID and retains manual findings
across collector runs. Its columns are:

```text
arxiv_id,review_status,quantization,architecture,fpga_device,model,toolflow,
evidence_pages,notes
```

The collector may add a blank row for an unseen ID, but it must never overwrite
non-empty survey fields. `README.md` joins catalogue metadata with this CSV to
provide a sortable, readable survey table and direct arXiv links.

## Collector commands and data flow

The Python CLI uses only the standard library (`argparse`, `urllib`,
`xml.etree.ElementTree`, `json`, `csv`, `hashlib`, and `pathlib`). This avoids
introducing a network or XML dependency into the new repository.

`bootstrap --all --download` is a deliberate, manual first-run command:

1. Query arXiv in pages of at most 100, ordered by submitted date.
2. Pace every API call by at least three seconds and use one connection at a
   time.
3. Continue through all matching history. If a query window reaches arXiv's
   2,000-result slice limit, split the date range and continue recursively so
   “all history” remains complete.
4. Normalize and upsert every returned version, add missing blank survey rows,
   download uncached PDF versions, and atomically write the catalogue/index.

`sync --download-new` is the daily cron target. It searches by last-updated
date from the last successful watermark, with a 72-hour overlap, so delayed
indexing and revisions are not lost. It is safe to run repeatedly: the identity
key, valid cache file, and SHA-256 prevent repeat downloads of an already
cached version.

`render` regenerates `README.md` after manual edits to the survey. `download`
is available for on-demand cache filling without calling the discovery API.

## Scheduling and run safety

`scripts/install_cron.py` installs a single user-crontab entry for a daily
local-time run (default: 03:17). It uses absolute repository paths, the Python
interpreter selected during installation, and a non-blocking `flock` lock. The
entry invokes `sync --download-new` and appends output to `logs/cron.log`.

The installer previews the exact crontab line and requires an explicit
`--install` flag; it does not modify a crontab during repository setup. It also
supports `--remove` for the exact managed entry, preserving unrelated cron
jobs.

API and download failures use bounded retry with backoff. The collector never
advances the successful watermark until catalogue, survey rows, and rendered
index have been written successfully. It writes a failed-run record under
`state/` for inspection. A PDF download is written as `*.part`, checked for a
PDF signature and non-empty content, hashed, then atomically renamed. Failed or
partial files never count as cached.

## Testing and acceptance criteria

Tests run with:

```sh
python3 -m unittest discover -s tests -v
```

They use saved Atom XML fixtures and temporary directories rather than live
arXiv calls. Required coverage includes query construction, Atom normalization,
page handling, exact-version deduplication, revision recognition, 2,000-result
window splitting, cache hit/miss behavior, partial-download recovery, atomic
state updates, survey-row preservation, deterministic README rendering, and
cron-line generation/removal.

The implementation is acceptable when a full-history bootstrap produces a
tracked catalogue and blank survey rows, a repeated run downloads no duplicate
PDF versions, a new arXiv revision downloads once as its new version, and the
daily cron command is idempotent and cannot overlap itself.

## Operational reference

The collector follows arXiv's API guidance to make no more than one request
every three seconds and to serialize connections. The repository README links
to the arXiv API manual and terms of use, explains the local-research-only PDF
cache, and gives the bootstrap, sync, render, and cron-install commands.
