from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[1]
_HUMERIS_REPO = Path("/home/jeroen/dev/constellation-generator")


def test_export_humeris_compare_baseline_script():
    run_dir = _REPO_ROOT / "docs/test-runs/run-0008-3b5fc7b-clean"
    out = _REPO_ROOT / "docs/interop/humeris_compare_baseline.json"

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/export_humeris_compare_baseline.py",
            "--run-dir",
            str(run_dir),
            "--out",
            str(out),
        ],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "wrote=" in proc.stdout
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["cases"]["basic_leo_two_body"]["elapsedSecs"] > 0
    assert payload["oem_summary"]["rows"] > 1000


@pytest.mark.skipif(not _HUMERIS_REPO.exists(), reason="Local Humeris repo not present")
def test_cross_suite_link_to_humeris_parity_reports():
    latest = _HUMERIS_REPO / "docs/gmat-parity-runs/LATEST"
    assert latest.exists()
    run_id = latest.read_text(encoding="utf-8").strip()
    report = _HUMERIS_REPO / "docs/gmat-parity-runs" / run_id / "REPORT.md"
    assert report.exists()
