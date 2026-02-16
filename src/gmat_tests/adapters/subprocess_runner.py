import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from gmat_tests.domain.models import GmatExecutionRequest, GmatExecutionResult
from gmat_tests.ports.gmat_runner import GmatRunner


class SubprocessGmatRunner(GmatRunner):
    def __init__(self, gmat_bin: Path, compat_lib_dir: Path | None = None) -> None:
        self._gmat_bin = gmat_bin
        self._compat_lib_dir = compat_lib_dir

    def create_contained_workdir(self, base_dir: Path | None = None) -> Path:
        root = Path(base_dir) if base_dir else Path(tempfile.gettempdir())
        root.mkdir(parents=True, exist_ok=True)
        return Path(tempfile.mkdtemp(prefix="gmat-run-", dir=root))

    def run(self, request: GmatExecutionRequest) -> GmatExecutionResult:
        if not self._gmat_bin.exists():
            raise FileNotFoundError(f"GMAT binary not found: {self._gmat_bin}")
        if not request.script_path.exists():
            raise FileNotFoundError(f"GMAT script not found: {request.script_path}")

        env = os.environ.copy()
        if self._compat_lib_dir:
            existing = env.get("LD_LIBRARY_PATH", "")
            env["LD_LIBRARY_PATH"] = f"{self._compat_lib_dir}:{existing}" if existing else str(self._compat_lib_dir)
        if request.env_overrides:
            env.update(request.env_overrides)

        cmd = self._build_command(request.work_dir, request.script_path)
        proc = subprocess.run(
            cmd,
            cwd=request.work_dir,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        return GmatExecutionResult(returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)

    def _build_command(self, work_dir: Path, script_path: Path) -> list[str]:
        binary_name = self._gmat_bin.name.lower()
        if "gmatconsole" not in binary_name:
            return [str(self._gmat_bin), str(script_path)]

        startup_file = self._build_contained_startup_file(work_dir)
        return [
            str(self._gmat_bin),
            "--startup_file",
            str(startup_file),
            "--logfile",
            str(work_dir / "gmat.log"),
            "--run",
            str(script_path),
            "--exit",
        ]

    def _build_contained_startup_file(self, work_dir: Path) -> Path:
        default_startup = self._gmat_bin.parent / "gmat_startup_file.txt"
        if not default_startup.exists():
            raise FileNotFoundError(f"GMAT startup file not found: {default_startup}")

        text = default_startup.read_text(encoding="utf-8")
        root_path = self._gmat_bin.parent.parent.resolve()
        output_path = work_dir.resolve()
        text = re.sub(
            r"^ROOT_PATH\s*=.*$",
            lambda _: f"ROOT_PATH                = {root_path}",
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r"^OUTPUT_PATH\s*=.*$",
            lambda _: f"OUTPUT_PATH              = {output_path}/",
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(r"^LOG_FILE\s*=.*$", "LOG_FILE                 = OUTPUT_PATH/GmatLog.txt", text, flags=re.MULTILINE)

        # Resolve plugin libraries to absolute paths so contained startup files
        # do not depend on cwd-relative lookup behavior.
        rewritten_lines: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("PLUGIN") and "=" in line:
                lhs, rhs = line.split("=", 1)
                plugin_value = rhs.strip()
                if plugin_value.startswith("../plugins/"):
                    plugin_abs = root_path / plugin_value.removeprefix("../")
                    line = f"{lhs}= {plugin_abs}"
            rewritten_lines.append(line)
        text = "\n".join(rewritten_lines) + "\n"

        startup_target = work_dir / "gmat_startup_file.txt"
        startup_target.write_text(text, encoding="utf-8")
        return startup_target


def prepare_script_in_workdir(source_script: Path, work_dir: Path) -> Path:
    work_dir.mkdir(parents=True, exist_ok=True)
    target = work_dir / source_script.name
    shutil.copy2(source_script, target)
    return target
