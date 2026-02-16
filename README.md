# gmat

Python test harness for validating a local NASA GMAT installation.

## Scope

- Keeps GMAT binaries/data local and out of git.
- Runs tests against the local GMAT binary in a contained temp workspace.
- Uses a hexagonal layout (`domain`, `ports`, `adapters`) for test execution flow.

## Local layout assumptions

- GMAT is extracted under `./GMAT/R2025a`.
- Main binary is `./GMAT/R2025a/bin/GMAT-R2025a`.

These files are intentionally excluded from version control.

## Quick start

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .[test]
pytest -q
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
pytest -q -m integration
```

## Notes

- MATLAB plugin is disabled in local GMAT startup file to avoid startup noise unless MATLAB is installed.
