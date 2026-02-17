from __future__ import annotations

from pathlib import Path

import pytest

from gmat_tests.adapters.subprocess_runner import SubprocessGmatRunner, prepare_script_in_workdir
from gmat_tests.config import resolve_compat_lib_dir, resolve_gmat_bin, resolve_test_sandbox
from gmat_tests.domain.models import GmatExecutionRequest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _run_script(script_path: Path) -> tuple[str, str, Path]:
    gmat_bin = resolve_gmat_bin()
    if not gmat_bin.exists():
        pytest.skip(f"GMAT binary not found at {gmat_bin}")

    runner = SubprocessGmatRunner(gmat_bin=gmat_bin, compat_lib_dir=resolve_compat_lib_dir())
    sandbox = runner.create_contained_workdir(resolve_test_sandbox())
    staged = prepare_script_in_workdir(script_path, sandbox)
    result = runner.run(GmatExecutionRequest(script_path=staged, work_dir=sandbox))
    assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    return result.stdout, result.stderr, sandbox


@pytest.mark.integration
def test_sample_hohmann_transfer_completes():
    script = _repo_root() / "GMAT/R2025a/samples/Ex_HohmannTransfer.script"
    stdout, _stderr, _sandbox = _run_script(script)
    assert "Mission run completed" in stdout


@pytest.mark.integration
def test_headless_oem_ephemeris_generates_report_rows():
    script = _repo_root() / "scenarios/headless_oem_ephemeris.script"
    _stdout, _stderr, sandbox = _run_script(script)
    report = sandbox / "KeplerianElements.txt"
    assert report.exists()
    lines = [ln for ln in report.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) > 1000


@pytest.mark.integration
def test_event_locator_reports_nonempty():
    script = _repo_root() / "scenarios/headless_eclipse_locator.script"
    _stdout, _stderr, sandbox = _run_script(script)
    report = sandbox / "EclipseLocator1.txt"
    assert report.exists()
    lines = [ln for ln in report.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) > 5
