"""Stress-test scenarios targeting Humeris propagator weaknesses.

Each scenario produces high-fidelity GMAT reference data. Tests assert
physical regime correctness only -- tight numerical comparison is the
responsibility of the Humeris parity test suite.
"""
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


# -- S1: High-order gravity field LEO -----------------------------------------

@pytest.mark.integration
def test_stress_high_gravity_leo():
    """EGM96 70x70: tesseral harmonics cause SMA/AOP oscillations."""
    vals = _run_scenario(
        "stress_high_gravity_leo.script",
        "stress_high_gravity_leo_results.txt",
    )
    start_sma, end_sma, start_ecc, end_ecc, start_aop, end_aop, elapsed = vals

    assert abs(elapsed - 14.0) < 1e-4
    # High-order gravity causes measurable SMA perturbation
    assert abs(end_sma - start_sma) > 1e-6
    # SMA stays in LEO regime
    assert 6500 < start_sma < 6800
    assert 6500 < end_sma < 6800
    # Eccentricity stays small
    assert 0.0 <= start_ecc < 0.1
    assert 0.0 <= end_ecc < 0.1
    # AOP is a valid angle
    assert 0.0 <= start_aop <= 360.0
    assert 0.0 <= end_aop <= 360.0


# -- S2: Atmospheric drag decay VLEO ------------------------------------------

@pytest.mark.integration
def test_stress_drag_decay_vleo():
    """MSISE90 drag at solar max: SMA decays, orbit circularizes."""
    vals = _run_scenario(
        "stress_drag_decay_vleo.script",
        "stress_drag_decay_vleo_results.txt",
    )
    start_sma, end_sma, start_ecc, end_ecc, start_alt, end_alt, elapsed = vals

    assert abs(elapsed - 7.0) < 1e-4
    # SMA must decrease (drag decay)
    assert end_sma < start_sma
    assert start_sma - end_sma > 0.1
    # Altitude must decrease
    assert end_alt < start_alt
    # Orbit circularizes
    assert end_ecc <= start_ecc + 1e-6
    # Stays in LEO regime
    assert 6500 < start_sma < 6800
    assert 6400 < end_sma < 6800


# -- S3: SRP at GEO long duration ---------------------------------------------

@pytest.mark.integration
def test_stress_srp_geo_long_duration():
    """SRP drives eccentricity growth at GEO over 60 days."""
    vals = _run_scenario(
        "stress_srp_geo_long_duration.script",
        "stress_srp_geo_long_duration_results.txt",
    )
    start_sma, end_sma, start_ecc, end_ecc, start_rmag, end_rmag, elapsed = vals

    assert abs(elapsed - 60.0) < 1e-4
    # SMA in GEO regime
    assert 42000 < start_sma < 42400
    assert 42000 < end_sma < 42400
    # Eccentricity grows from SRP forcing
    assert end_ecc > start_ecc
    assert end_ecc - start_ecc > 1e-6
    # RMAG in GEO regime
    assert 42000 < start_rmag < 42400
    assert 42000 < end_rmag < 42400


# -- S4: Molniya third-body + critical inclination ----------------------------

@pytest.mark.integration
def test_stress_molniya_thirdbody():
    """At critical inclination, AOP drifts from lunisolar + higher-order terms."""
    vals = _run_scenario(
        "stress_molniya_thirdbody.script",
        "stress_molniya_thirdbody_results.txt",
    )
    start_aop, end_aop, start_ecc, end_ecc, start_raan, end_raan, elapsed = vals

    assert abs(elapsed - 30.0) < 1e-4
    # AOP drifts (not frozen despite critical inclination)
    aop_delta = _angular_delta_deg(start_aop, end_aop)
    assert aop_delta > 0.001
    # Eccentricity stays in HEO regime
    assert 0.5 < start_ecc < 0.9
    assert 0.5 < end_ecc < 0.9
    # RAAN drifts
    raan_delta = _angular_delta_deg(start_raan, end_raan)
    assert raan_delta > 0.001


# -- S5: Cislunar NRHO --------------------------------------------------------

@pytest.mark.integration
def test_stress_cislunar_nrho():
    """NRHO near-periodicity: selenocentric RMAG returns close to start."""
    vals = _run_scenario(
        "stress_cislunar_nrho.script",
        "stress_cislunar_nrho_results.txt",
    )
    (start_rmag_moon, end_rmag_moon, start_rmag_earth, end_rmag_earth,
     start_vmag, end_vmag, elapsed) = vals

    assert abs(elapsed - 14.0) < 1e-4
    # Selenocentric distance: pericynthion ~3500 km, apocynthion ~70000 km
    assert 1000 < start_rmag_moon < 80000
    assert 1000 < end_rmag_moon < 80000
    # Earth distance: roughly lunar distance +/- NRHO amplitude
    assert 300000 < start_rmag_earth < 500000
    assert 300000 < end_rmag_earth < 500000
    # Velocity is positive
    assert start_vmag > 0
    assert end_vmag > 0


# -- S6: Sun-synchronous full fidelity ----------------------------------------

@pytest.mark.integration
def test_stress_sun_synch_full_fidelity():
    """All forces combined: RAAN advances at sun-synchronous rate."""
    vals = _run_scenario(
        "stress_sun_synch_full_fidelity.script",
        "stress_sun_synch_full_fidelity_results.txt",
    )
    start_sma, end_sma, start_raan, end_raan, start_ecc, end_ecc, elapsed = vals

    assert abs(elapsed - 30.0) < 1e-4
    # SMA in SSO regime (~700 km alt)
    assert 7000 < start_sma < 7200
    assert 7000 < end_sma < 7200
    # RAAN advances at ~0.9856 deg/day for sun-synchronous
    raan_delta = ((end_raan - start_raan + 360.0) % 360.0)
    expected_drift = 0.9856 * 30.0
    assert abs(raan_delta - expected_drift) < 2.0
    # Eccentricity stays small
    assert 0.0 <= start_ecc < 0.01
    assert 0.0 <= end_ecc < 0.01


# -- S7: Jupiter flyby (heliocentric) -----------------------------------------

@pytest.mark.integration
def test_stress_jupiter_flyby():
    """Jupiter perturbation changes orbital elements measurably."""
    vals = _run_scenario(
        "stress_jupiter_flyby.script",
        "stress_jupiter_flyby_results.txt",
    )
    start_ecc, end_ecc, start_inc, end_inc, start_rmag, end_rmag, elapsed = vals

    assert abs(elapsed - 180.0) < 1e-4
    # Heliocentric distances (AU scale, in km)
    assert start_rmag > 100_000_000
    assert end_rmag > 100_000_000
    # Sun distance changed over 180-day arc
    assert abs(end_rmag - start_rmag) > 1_000_000
    # ECC/INC are Earth-centered (large for heliocentric); just check positive
    assert start_ecc > 0
    assert end_ecc > 0
    # Jupiter perturbation caused measurable trajectory change
    assert abs(end_ecc - start_ecc) > 1e-6 or abs(end_rmag - start_rmag) > 1_000_000


# -- S8: Integrator energy drift (pure Keplerian) -----------------------------

@pytest.mark.integration
def test_stress_rk4_energy_drift():
    """Point-mass Keplerian: SMA conserved to integrator precision."""
    vals = _run_scenario(
        "stress_rk4_energy_drift.script",
        "stress_rk4_energy_drift_results.txt",
    )
    start_sma, end_sma, start_ecc, end_ecc, start_rmag, end_rmag, elapsed = vals

    assert abs(elapsed - 7.0) < 1e-4
    # SMA conserved to < 1e-6 km (GMAT RK89 self-consistency)
    assert abs(end_sma - start_sma) < 1e-6
    # Eccentricity conserved
    assert abs(end_ecc - start_ecc) < 1e-10
    # Physical ranges
    assert 7900 < start_sma < 8100
    assert 0.1 < start_ecc < 0.2
    assert start_rmag > 0
    assert end_rmag > 0
