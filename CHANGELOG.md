# Changelog

## 0.2.0 - 2026-02-17

- Added comparative baseline exporter: `scripts/export_humeris_compare_baseline.py`.
- Added cross-suite tests for baseline export and Humeris parity artifact linkage.
- Added expanded GMAT integration tests for:
  - `Ex_HohmannTransfer.script` mission completion
  - `headless_oem_ephemeris.script` report row generation
  - `headless_eclipse_locator.script` event report generation
- Bumped project version to `0.2.0`.

## 0.1.0 - 2026-02-16

- Scaffolded Python project for GMAT-focused test execution.
- Added contained execution adapter for running GMAT in isolated temp dirs.
- Added tests for config resolution, contained runtime behavior, and linker dependency checks.
- Excluded local GMAT binaries/artifacts from git tracking.
- Added repository bootstrap script (`scripts/bootstrap.sh`) for one-step environment setup.
- Added unified test runner script (`scripts/run-tests.sh`) for unit, integration, and lab tiers.
- Added GitHub Actions CI workflow for unit/non-integration checks.
- Switched repository license to MIT.
