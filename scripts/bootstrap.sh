#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/venv"
GMAT_DIR="$ROOT_DIR/GMAT/R2025a"
GMAT_BIN="$GMAT_DIR/bin/GmatConsole"
GMAT_TARBALL="$ROOT_DIR/gmat-ubuntu-x64-R2025a.tar.gz"
GMAT_URL="https://sourceforge.net/projects/gmat/files/GMAT/GMAT-R2025a/gmat-ubuntu-x64-R2025a.tar.gz/download"

log() {
  printf "[bootstrap] %s\n" "$*"
}

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

need_cmd python3
need_cmd tar

log "Repository root: $ROOT_DIR"

if [[ ! -d "$VENV_DIR" ]]; then
  log "Creating virtual environment"
  python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

log "Installing Python dependencies"
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e "$ROOT_DIR[test]"
python -m pip install -r "$ROOT_DIR/.gmat-lab/requirements.txt"

if [[ ! -x "$GMAT_BIN" ]]; then
  log "GMAT not found, downloading R2025a"
  if command -v wget >/dev/null 2>&1; then
    wget -O "$GMAT_TARBALL" "$GMAT_URL"
  elif command -v curl >/dev/null 2>&1; then
    curl -L "$GMAT_URL" -o "$GMAT_TARBALL"
  else
    echo "Need either wget or curl to download GMAT" >&2
    exit 1
  fi

  log "Extracting GMAT tarball"
  tar -xzf "$GMAT_TARBALL" -C "$ROOT_DIR"
fi

if [[ ! -x "$GMAT_BIN" ]]; then
  echo "GMAT install failed: missing $GMAT_BIN" >&2
  exit 1
fi

STARTUP_FILE="$GMAT_DIR/bin/gmat_startup_file.txt"
if [[ -f "$STARTUP_FILE" ]]; then
  log "Disabling MATLAB plugin line in startup file"
  sed -i 's#^PLUGIN\s*=\s*../plugins/libMatlabInterface#\# PLUGIN                  = ../plugins/libMatlabInterface#' "$STARTUP_FILE"
fi

COMPAT_DIR="$ROOT_DIR/GMAT/compat-libs"
mkdir -p "$COMPAT_DIR"
if [[ -e /usr/lib/x86_64-linux-gnu/libtiff.so.6 ]]; then
  ln -sfn /usr/lib/x86_64-linux-gnu/libtiff.so.6 "$COMPAT_DIR/libtiff.so.5"
fi

if ldd "$GMAT_BIN" | grep -q "not found"; then
  log "WARNING: unresolved GMAT shared libraries detected"
  ldd "$GMAT_BIN" | grep "not found" || true
  log "You may need to install system packages with apt."
else
  log "GMAT runtime dependencies look resolved"
fi

cat <<MSG

Bootstrap complete.

Next steps:
  source venv/bin/activate
  ./scripts/run-tests.sh --all

MSG
