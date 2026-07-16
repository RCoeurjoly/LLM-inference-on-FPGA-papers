from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts/collect_arxiv.py"


def create_repo(root: Path) -> None:
    (root / "config").mkdir(parents=True)
    (root / "data").mkdir()
    shutil.copyfile(REPO_ROOT / "config/query.json", root / "config/query.json")
    (root / "data/catalog.json").write_text(
        '{"schema_version": 1, "query_id": "llm-inference-fpga-v1", "papers": {}}\n',
        encoding="utf-8",
    )
    (root / "data/survey.csv").write_text(
        "arxiv_id,review_status,quantization,architecture,fpga_device,model,toolflow,evidence_pages,notes\n",
        encoding="utf-8",
    )


class CliTests(unittest.TestCase):
    def test_render_command_rewrites_readme(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            create_repo(root)

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--repo-root", str(root), "render"],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((root / "README.md").exists())
            self.assertIn("LLM inference on FPGA papers", (root / "README.md").read_text())

    def test_missing_repository_contract_returns_a_clear_error(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--repo-root", "/definitely/missing", "render"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("config/query.json", result.stderr)


if __name__ == "__main__":
    unittest.main()
