# Changelog

## 0.1.0 - 2026-02-16

- Scaffolded Python project for GMAT-focused test execution.
- Added contained execution adapter for running GMAT in isolated temp dirs.
- Added tests for config resolution, contained runtime behavior, and linker dependency checks.
- Excluded local GMAT binaries/artifacts from git tracking.
- Added repository bootstrap script (`scripts/bootstrap.sh`) for one-step environment setup.
- Added unified test runner script (`scripts/run-tests.sh`) for unit, integration, and lab tiers.
- Added GitHub Actions CI workflow for unit/non-integration checks.
- Switched repository license to MIT.
