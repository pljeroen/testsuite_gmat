from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class GmatExecutionRequest:
    script_path: Path
    work_dir: Path
    env_overrides: Mapping[str, str] | None = None


@dataclass(frozen=True)
class GmatExecutionResult:
    returncode: int
    stdout: str
    stderr: str
