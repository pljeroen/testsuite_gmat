import os
from pathlib import Path


def resolve_gmat_bin() -> Path:
    return Path(os.getenv("GMAT_BIN", "GMAT/R2025a/bin/GmatConsole")).resolve()


def resolve_compat_lib_dir() -> Path | None:
    value = os.getenv("GMAT_COMPAT_LIB_DIR")
    return Path(value).resolve() if value else None


def resolve_test_sandbox() -> Path:
    return Path(os.getenv("GMAT_TEST_SANDBOX", ".gmat-sandbox")).resolve()
