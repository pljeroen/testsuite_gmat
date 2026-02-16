from pathlib import Path

from gmat_tests.adapters.subprocess_runner import SubprocessGmatRunner, prepare_script_in_workdir
from gmat_tests.config import resolve_compat_lib_dir, resolve_gmat_bin, resolve_test_sandbox
from gmat_tests.domain.models import GmatExecutionRequest


def run_script(script_path: Path) -> int:
    runner = SubprocessGmatRunner(
        gmat_bin=resolve_gmat_bin(),
        compat_lib_dir=resolve_compat_lib_dir(),
    )
    sandbox = runner.create_contained_workdir(resolve_test_sandbox())
    staged_script = prepare_script_in_workdir(script_path, sandbox)
    result = runner.run(GmatExecutionRequest(script_path=staged_script, work_dir=sandbox))
    return result.returncode
