from __future__ import annotations

from pathlib import Path

import pytest

from gmat_tests.adapters.subprocess_runner import SubprocessGmatRunner, prepare_script_in_workdir
from gmat_tests.config import resolve_compat_lib_dir, resolve_gmat_bin, resolve_test_sandbox
from gmat_tests.domain.models import GmatExecutionRequest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_numeric_row(report_path: Path, expected_values: int) -> list[float]:
    lines = [line.strip() for line in report_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    for line in reversed(lines):
        parts = line.split()
        try:
            values = [float(token) for token in parts]
        except ValueError:
            continue
        if len(values) == expected_values:
            return values
    raise AssertionError(f"No numeric row with {expected_values} values found in {report_path}")


def _run_scenario(script_name: str, report_name: str) -> list[float]:
    gmat_bin = resolve_gmat_bin()
    if not gmat_bin.exists():
        pytest.skip(f"GMAT binary not found at {gmat_bin}")

    root = _repo_root()
    script = root / "scenarios" / script_name
    runner = SubprocessGmatRunner(gmat_bin=gmat_bin, compat_lib_dir=resolve_compat_lib_dir())
    sandbox = runner.create_contained_workdir(resolve_test_sandbox())
    staged_script = prepare_script_in_workdir(script, sandbox)
    result = runner.run(GmatExecutionRequest(script_path=staged_script, work_dir=sandbox))

    assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"

    report_path = sandbox / report_name
    assert report_path.exists(), f"Expected report file missing: {report_path}"
    return _read_numeric_row(report_path, expected_values=7)


def _angular_delta_deg(start_deg: float, end_deg: float) -> float:
    return abs(((end_deg - start_deg + 180.0) % 360.0) - 180.0)


@pytest.mark.integration
def test_basic_leo_two_body_conservation():
    start_sma, start_ecc, _start_rmag, end_sma, end_ecc, _end_rmag, elapsed_secs = _run_scenario(
        "basic_leo_two_body.script",
        "basic_leo_two_body_results.txt",
    )

    assert abs(elapsed_secs - 5400.0) < 1e-6
    assert abs(end_sma - start_sma) < 1e-2
    assert abs(end_ecc - start_ecc) < 1e-8


@pytest.mark.integration
def test_advanced_j2_raan_drift_detected():
    start_raan, start_inc, start_ecc, end_raan, end_inc, end_ecc, elapsed_days = _run_scenario(
        "advanced_j2_raan_drift.script",
        "advanced_j2_raan_drift_results.txt",
    )

    drift = _angular_delta_deg(start_raan, end_raan)

    assert abs(elapsed_days - 7.0) < 1e-6
    assert drift > 0.01
    assert drift < 30.0
    assert abs(end_inc - start_inc) < 0.2
    assert 0.0 <= start_ecc < 1.0
    assert 0.0 <= end_ecc < 1.0


@pytest.mark.integration
def test_advanced_oumuamua_hyperbolic_regime():
    start_ecc, start_inc, start_rmag, end_ecc, end_inc, end_rmag, elapsed_days = _run_scenario(
        "advanced_oumuamua_hyperbolic.script",
        "advanced_oumuamua_hyperbolic_results.txt",
    )

    assert abs(elapsed_days - 120.0) < 1e-6
    assert start_ecc > 1.0
    assert end_ecc > 1.0
    assert 0.0 <= start_inc <= 180.0
    assert 0.0 <= end_inc <= 180.0
    assert start_rmag > 0.0
    assert end_rmag > 0.0
    assert abs(end_rmag - start_rmag) > 1000.0
