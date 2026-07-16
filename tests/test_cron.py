from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from paperlib.cron import MANAGED_MARKER, build_cron_line, merge_crontab, remove_managed_entry


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/install_cron.py"


class CronTests(unittest.TestCase):
    def test_builds_daily_locked_absolute_command(self) -> None:
        line = build_cron_line(Path("/repo"), Path("/usr/bin/python3"), 3, 17)

        self.assertTrue(line.startswith("17 3 * * * "))
        self.assertIn("/usr/bin/flock -n /repo/state/collector.lock", line)
        self.assertIn("/usr/bin/python3 /repo/scripts/collect_arxiv.py", line)
        self.assertIn("sync --download-new", line)
        self.assertTrue(line.endswith(MANAGED_MARKER))

    def test_merge_is_idempotent_and_remove_preserves_other_jobs(self) -> None:
        original = "0 1 * * * /usr/local/bin/backup\n"
        line = "17 3 * * * run # LLM-inference-on-FPGA-papers"

        merged = merge_crontab(original, line)

        self.assertEqual(merge_crontab(merged, line), merged)
        self.assertEqual(remove_managed_entry(merged), original)

    def test_installer_help_exposes_explicit_lifecycle_flags(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--install", result.stdout)
        self.assertIn("--remove", result.stdout)


if __name__ == "__main__":
    unittest.main()
