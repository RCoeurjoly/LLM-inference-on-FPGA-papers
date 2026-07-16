#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from paperlib.config import load_config
from paperlib.cron import build_cron_line, merge_crontab, read_crontab, remove_managed_entry, write_crontab


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview, install, or remove the daily paper collector cron job.")
    parser.add_argument("--repo-root", type=Path, default=REPOSITORY_ROOT)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--install", action="store_true")
    actions.add_argument("--remove", action="store_true")
    args = parser.parse_args()

    try:
        repo_root = args.repo_root.resolve()
        config = load_config(repo_root / "config/query.json")
        line = build_cron_line(
            repo_root, Path(sys.executable).resolve(), config.cron_hour, config.cron_minute
        )
        if not args.install and not args.remove:
            print(line)
            return 0

        existing = read_crontab()
        resulting = merge_crontab(existing, line) if args.install else remove_managed_entry(existing)
        print(resulting, end="")
        (repo_root / "state").mkdir(parents=True, exist_ok=True)
        (repo_root / "logs").mkdir(parents=True, exist_ok=True)
        write_crontab(resulting)
        return 0
    except (OSError, RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


raise SystemExit(main())
