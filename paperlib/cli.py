from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence

from paperlib.arxiv import ArxivClient
from paperlib.collector import bootstrap_all, download_missing, sync_recent
from paperlib.config import load_config
from paperlib.render import render_readme
from paperlib.storage import atomic_write_text, load_catalog, load_survey


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _validate_repo_root(repo_root: Path) -> None:
    for relative_path in ("config/query.json", "data/catalog.json", "data/survey.csv"):
        required_path = repo_root / relative_path
        if not required_path.is_file():
            raise ValueError(f"repository is missing required file: {required_path}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Maintain the local arXiv paper survey.")
    parser.add_argument("--repo-root", type=Path, default=_default_repo_root())
    commands = parser.add_subparsers(dest="command", required=True)

    bootstrap = commands.add_parser("bootstrap", help="collect all matching arXiv history")
    bootstrap.add_argument("--all", action="store_true", required=True)
    bootstrap.add_argument("--download", action="store_true")

    sync = commands.add_parser("sync", help="collect recent matching arXiv updates")
    sync.add_argument("--download-new", action="store_true")

    commands.add_parser("download", help="cache missing PDFs from the local catalogue")
    commands.add_parser("render", help="regenerate README.md without network access")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()

    try:
        _validate_repo_root(repo_root)
        if args.command == "render":
            rendered = render_readme(
                load_catalog(repo_root / "data/catalog.json"),
                load_survey(repo_root / "data/survey.csv"),
            )
            atomic_write_text(repo_root / "README.md", rendered)
            return 0

        if args.command == "download":
            download_missing(repo_root)
            return 0

        config = load_config(repo_root / "config/query.json")
        client = ArxivClient(
            config.api_url,
            config.user_agent,
            config.min_api_interval_seconds,
        )
        now = datetime.now(UTC)
        if args.command == "bootstrap":
            bootstrap_all(repo_root, args.download, now, client)
            return 0
        if args.command == "sync":
            sync_recent(repo_root, args.download_new, now, client)
            return 0
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    raise AssertionError(f"unhandled command: {args.command}")
