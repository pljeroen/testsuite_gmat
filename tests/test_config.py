from pathlib import Path

from gmat_tests.config import resolve_compat_lib_dir, resolve_gmat_bin, resolve_test_sandbox


def test_default_gmat_bin_path(monkeypatch):
    monkeypatch.delenv("GMAT_BIN", raising=False)
    path = resolve_gmat_bin()
    assert str(path).endswith("GMAT/R2025a/bin/GmatConsole-R2025a")


def test_custom_paths(monkeypatch, tmp_path):
    fake_bin = tmp_path / "bin" / "GMAT"
    fake_lib = tmp_path / "libs"
    fake_sandbox = tmp_path / "sandbox"

    monkeypatch.setenv("GMAT_BIN", str(fake_bin))
    monkeypatch.setenv("GMAT_COMPAT_LIB_DIR", str(fake_lib))
    monkeypatch.setenv("GMAT_TEST_SANDBOX", str(fake_sandbox))

    assert resolve_gmat_bin() == fake_bin.resolve()
    assert resolve_compat_lib_dir() == fake_lib.resolve()
    assert resolve_test_sandbox() == fake_sandbox.resolve()
