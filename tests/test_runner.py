from pathlib import Path

from gmat_tests.adapters.subprocess_runner import SubprocessGmatRunner, prepare_script_in_workdir
from gmat_tests.domain.models import GmatExecutionRequest


FAKE_GMAT = """#!/usr/bin/env bash
set -euo pipefail
echo "cwd=$(pwd)"
echo "script=$1"
exit 0
"""


def test_runner_uses_contained_workdir(tmp_path):
    fake_bin = tmp_path / "GMAT-R2025a"
    fake_bin.write_text(FAKE_GMAT)
    fake_bin.chmod(0o755)

    script = tmp_path / "sample.script"
    script.write_text("Create Spacecraft Sat;\n")

    runner = SubprocessGmatRunner(gmat_bin=fake_bin)
    sandbox = runner.create_contained_workdir(tmp_path)
    staged = prepare_script_in_workdir(script, sandbox)

    result = runner.run(GmatExecutionRequest(script_path=staged, work_dir=sandbox))

    assert result.returncode == 0
    assert f"cwd={sandbox}" in result.stdout
    assert f"script={staged}" in result.stdout


def test_missing_script_fails_fast(tmp_path):
    fake_bin = tmp_path / "GMAT-R2025a"
    fake_bin.write_text(FAKE_GMAT)
    fake_bin.chmod(0o755)

    runner = SubprocessGmatRunner(gmat_bin=fake_bin)
    missing_script = tmp_path / "missing.script"

    try:
        runner.run(GmatExecutionRequest(script_path=missing_script, work_dir=tmp_path))
        raise AssertionError("Expected FileNotFoundError")
    except FileNotFoundError as exc:
        assert "script" in str(exc)
