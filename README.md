# GMAT Test Suite

[![CI](https://github.com/pljeroen/testsuite_gmat/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/pljeroen/testsuite_gmat/actions/workflows/ci.yml)
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

## Notes

- MATLAB plugin is disabled in local GMAT startup file to avoid startup noise unless MATLAB is installed.
