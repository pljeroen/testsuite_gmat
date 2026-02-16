import os
import subprocess
from pathlib import Path

import pytest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.mark.integration
def test_local_gmat_has_resolved_runtime_links():
    root = _repo_root()
    gmat_bin = root / "GMAT/R2025a/bin/GMAT-R2025a"
    compat = root / "GMAT/compat-libs"

    if not gmat_bin.exists():
        pytest.skip("Local GMAT binary not present")

    env = os.environ.copy()
    if compat.exists():
        ld_existing = env.get("LD_LIBRARY_PATH", "")
        env["LD_LIBRARY_PATH"] = f"{compat}:{ld_existing}" if ld_existing else str(compat)

    proc = subprocess.run(["ldd", str(gmat_bin)], text=True, capture_output=True, env=env, check=False)
    assert proc.returncode == 0, proc.stderr
    assert "not found" not in proc.stdout
