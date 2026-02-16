#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/venv"
GMAT_BIN_DEFAULT="$ROOT_DIR/GMAT/R2025a/bin/GmatConsole"
COMPAT_LIB_DIR="$ROOT_DIR/GMAT/compat-libs"

RUN_UNIT=1
RUN_INTEGRATION=0
RUN_TIER1=0
RUN_TIER2=0

usage() {
  cat <<USAGE
Usage: ./scripts/run-tests.sh [options]

Options:
  --unit-only       Run non-integration pytest tests only (default)
  --integration     Run pytest integration tests too
  --tier1           Run .gmat-lab Tier 1 case runner
  --tier2           Run .gmat-lab Tier 2 case runner (requires network)
  --all             Run unit + integration + tier1 + tier2
  -h, --help        Show this help
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --unit-only)
      RUN_UNIT=1
      RUN_INTEGRATION=0
      shift
      ;;
    --integration)
      RUN_INTEGRATION=1
      shift
      ;;
    --tier1)
      RUN_TIER1=1
      shift
      ;;
    --tier2)
      RUN_TIER2=1
      shift
      ;;
    --all)
      RUN_INTEGRATION=1
      RUN_TIER1=1
      RUN_TIER2=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ ! -d "$VENV_DIR" ]]; then
  echo "Missing venv. Run ./scripts/bootstrap.sh first." >&2
  exit 2
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

export GMAT_BIN="${GMAT_BIN:-$GMAT_BIN_DEFAULT}"
if [[ -d "$COMPAT_LIB_DIR" ]]; then
  export GMAT_COMPAT_LIB_DIR="${GMAT_COMPAT_LIB_DIR:-$COMPAT_LIB_DIR}"
fi

cd "$ROOT_DIR"

if [[ "$RUN_UNIT" -eq 1 ]]; then
  echo "[run-tests] pytest unit/non-integration"
  pytest -q -m "not integration"
fi

if [[ "$RUN_INTEGRATION" -eq 1 ]]; then
  echo "[run-tests] pytest integration"
  pytest -q -m integration
fi

if [[ "$RUN_TIER1" -eq 1 ]]; then
  echo "[run-tests] .gmat-lab tier1"
  python3 .gmat-lab/bin/run_case.py --tier tier1
fi

if [[ "$RUN_TIER2" -eq 1 ]]; then
  echo "[run-tests] .gmat-lab tier2"
  python3 .gmat-lab/bin/run_case.py --tier tier2
fi

