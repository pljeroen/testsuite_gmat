# GMAT Test Suite

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)

Python test suite for validating local NASA GMAT behavior in reproducible, headless runs.

## Scope

- Keeps GMAT binaries/data local and out of git.
- Runs tests against the local GMAT binary in a contained temp workspace.
- Uses a hexagonal layout (`domain`, `ports`, `adapters`) for test execution flow.

## Local Layout Assumptions

- GMAT is extracted under `./GMAT/R2025a`.
- Headless binary is `./GMAT/R2025a/bin/GmatConsole`.

These files are intentionally excluded from version control.

## Quick Start

```bash
git clone git@github.com:pljeroen/testsuite_gmat.git
cd testsuite_gmat
./scripts/bootstrap.sh
./scripts/run-tests.sh --all
```

What `bootstrap.sh` does:

- Creates `venv/`
- Installs Python dependencies
- Downloads/extracts GMAT R2025a if missing
- Applies local GMAT compatibility setup used by this repo

Run unit-only checks (same scope as CI):

```bash
./scripts/run-tests.sh --unit-only
```

## Configuration

- `GMAT_BIN`: Path to GMAT executable (default: `GMAT/R2025a/bin/GmatConsole`)
- `GMAT_COMPAT_LIB_DIR`: Optional path with compatibility libs (`libtiff.so.5` symlink etc.)
- `GMAT_TEST_SANDBOX`: Optional base directory for test runtime workspaces

## Scenario Suite

Scenario scripts are in `scenarios/` and are executed headlessly with `GmatConsole`:

- `basic_leo_two_body.script`
- `advanced_j2_raan_drift.script`
- `advanced_oumuamua_hyperbolic.script`

The test harness generates a contained startup file per run, redirects GMAT
output into the sandbox directory, and validates results from GMAT `ReportFile`
artifacts.

Run only scenario integrations:

```bash
./scripts/run-tests.sh --integration
```

## Local Run Archives

Local orchestration in `.gmat-lab/` can archive run outputs to `docs/test-runs/` using:

```bash
source venv/bin/activate
python3 .gmat-lab/bin/run_case.py --tier tier1
python3 .gmat-lab/bin/run_case.py --tier tier2
```

Each run snapshot includes:

- Incrementing run number
- Git commit short hash
- Dirty/clean workspace state
- Per-case stdout/stderr/log/report artifacts

## Test Rundown (Latest Clean Run)

Reference run: `docs/test-runs/run-0008-3b5fc7b-clean/manifest.json` (commit `3b5fc7b`, `failures=0`).

### Tier 1 GMAT-Native Cases

1. `basic_leo_two_body` (`scenarios/basic_leo_two_body.script`)
   - Why selected: baseline sanity check for two-body propagation and conserved orbital elements.
   - Expected baseline: elapsed `5400 s`; near-conservation of SMA/ECC (`|dSMA| < 1e-2 km`, `|dECC| < 1e-8`).
   - GMAT output: elapsed `5400.000000314321 s`; `dSMA=-2.200977e-10 km`; `dECC=+7.020426e-15`.
   - Notes on differences: tiny non-zero drift is numerical precision noise and is far below thresholds.

2. `advanced_j2_raan_drift` (`scenarios/advanced_j2_raan_drift.script`)
   - Why selected: validates secular J2 behavior (RAAN precession) in a realistic LEO-like regime.
   - Expected baseline: elapsed `7 days`; measurable but bounded RAAN drift (`0.01 < drift < 30 deg`); inclination stable (`|dINC| < 0.2 deg`); ECC remains bound (`0 <= ECC < 1`).
   - GMAT output: RAAN `20.000000 -> 26.805481 deg` (`drift=6.805481 deg`), INC `97.8 -> 97.820236 deg` (`dINC=0.020236 deg`), ECC `0.001000000 -> 0.001578224`.
   - Notes on differences: drift magnitude depends on force model and step-size/integrator behavior; values are in expected physical range.

3. `advanced_oumuamua_hyperbolic` (`scenarios/advanced_oumuamua_hyperbolic.script`)
   - Why selected: stress case for hyperbolic/interstellar regime (eccentricity remains > 1).
   - Expected baseline: elapsed `120 days`; start/end `ECC > 1`; valid inclinations (`0..180 deg`); radius magnitude changes materially.
   - GMAT output: ECC `5.338e6 -> 7.665e6`; INC `33.819743 -> 19.075089 deg`; RMAG `2.980e7 -> 1.044e9 km` (`+1.014678e9 km`).
   - Notes on differences: this is a regime-classification test, not an external-observation fit; large values are consistent with hyperbolic state representation.

4. `sample_hohmann_transfer` (`GMAT/R2025a/samples/Ex_HohmannTransfer.script`)
   - Why selected: uses an official GMAT sample mission for maneuver/targeting execution.
   - Expected baseline: successful mission completion (official sample behavior).
   - GMAT output: `stdout` contains `Mission run completed.` and `GMAT Integration test (Console version) successful`.
   - Notes on differences: no numeric golden file is asserted for this sample; pass criterion is clean completion.

5. `headless_eclipse_locator` (`scenarios/headless_eclipse_locator.script`)
   - Why selected: validates event-location pipeline and eclipse report generation in headless mode.
   - Expected baseline: successful run and non-empty `EclipseLocator1.txt`.
   - GMAT output: report generated with `22` numeric event lines.
   - Notes on differences: event counts can vary with epoch/step/event-locator tolerances; this test currently checks operational validity.

6. `sample_contact_locator` (`GMAT/R2025a/samples/Ex_R2015a_StationContactLocator.script`)
   - Why selected: validates access/contact window analysis against GMAT sample tooling.
   - Expected baseline: successful run and non-empty `ContactLocator1.txt`.
   - GMAT output: report generated with `26` numeric event lines.
   - Notes on differences: exact windows depend on geometry, timing setup, and event tolerances.

7. `headless_oem_ephemeris_propagation` (`scenarios/headless_oem_ephemeris.script`)
   - Why selected: validates OEM ingest + propagation + report generation using bundled local sample data.
   - Expected baseline: successful run and full `KeplerianElements.txt` output for 2 days at 1-minute cadence.
   - GMAT output: `2880` data rows. First row (`01 Jan 2000 12:00:00.000`): SMA `7191.901567 km`, ECC `0.024514413`, INC `12.849589 deg`. Last row (`03 Jan 2000 11:59:00.000`): SMA `7191.961229 km`, ECC `0.025007723`, INC `12.845997 deg`.
   - Notes on differences: small element evolution is expected from numerical propagation and the loaded ephemeris/force assumptions.

### Tier 2 (Free Public Data Extensions)

- Tier 2 cases are cataloged in `.gmat-lab/cases/tier2/catalog.json`:
  - `celestrak_fetch_active_tle`
  - `sgp4_propagation_active`
  - `conjunction_screening_heuristic`
- Why included: these cover free-data acquisition and downstream screening workflows without paid accounts.
- Why not treated as GMAT golden-standard assertions: they rely on live external catalogs and heuristic thresholds, so outputs are intentionally time-variant and should be validated per run context.

## Notes

- MATLAB plugin is disabled in local GMAT startup file to avoid startup noise unless MATLAB is installed.
