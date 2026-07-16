from __future__ import annotations

import shlex
import subprocess
from collections.abc import Callable
from pathlib import Path


MANAGED_MARKER = "# LLM-inference-on-FPGA-papers"


def build_cron_line(repo_root: Path, python: Path, hour: int, minute: int) -> str:
    """Build the one daily, non-overlapping collector invocation."""
    quote = lambda value: shlex.quote(str(value))
    return (
        f"{minute} {hour} * * * /usr/bin/flock -n "
        f"{quote(repo_root / 'state/collector.lock')} {quote(python)} "
        f"{quote(repo_root / 'scripts/collect_arxiv.py')} --repo-root {quote(repo_root)} "
        f"sync --download-new >> {quote(repo_root / 'logs/cron.log')} 2>&1 {MANAGED_MARKER}"
    )


def merge_crontab(existing: str, line: str) -> str:
    """Replace only this project's old managed entries with one current line."""
    kept = [row for row in existing.splitlines() if MANAGED_MARKER not in row]
    return "\n".join([*kept, line, ""])


def remove_managed_entry(existing: str) -> str:
    """Remove only this project's managed cron lines."""
    kept = [row for row in existing.splitlines() if MANAGED_MARKER not in row]
    return "\n".join(kept) + ("\n" if kept else "")


def read_crontab(
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> str:
    """Read the user's crontab; an absent crontab is an empty one."""
    result = runner(["crontab", "-l"], text=True, capture_output=True, check=False)
    if result.returncode == 0:
        return result.stdout
    if result.returncode == 1 and not result.stdout:
        return ""
    detail = result.stderr.strip() or f"exit code {result.returncode}"
    raise RuntimeError(f"could not read crontab: {detail}")


def write_crontab(
    content: str,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> None:
    """Replace the user's crontab with exactly the supplied complete text."""
    result = runner(
        ["crontab", "-"],
        input=content,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or f"exit code {result.returncode}"
        raise RuntimeError(f"could not write crontab: {detail}")
