from pathlib import Path
from typing import Protocol

from gmat_tests.domain.models import GmatExecutionRequest, GmatExecutionResult


class GmatRunner(Protocol):
    def run(self, request: GmatExecutionRequest) -> GmatExecutionResult:
        ...

    def create_contained_workdir(self, base_dir: Path | None = None) -> Path:
        ...
