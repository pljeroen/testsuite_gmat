from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from common import LAB, ROOT, load_catalog, make_workdir

sys.path.insert(0, str(ROOT / "src"))

from gmat_tests.adapters.subprocess_runner import SubprocessGmatRunner, prepare_script_in_workdir
from gmat_tests.config import resolve_compat_lib_dir, resolve_gmat_bin
from gmat_tests.domain.models import GmatExecutionRequest


def _git_info() -> dict[str, str]:
    def _capture(args: list[str]) -> tuple[int, str]:
        proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
        return proc.returncode, proc.stdout.strip()

    rc, inside = _capture(["git", "rev-parse", "--is-inside-work-tree"])
    if rc != 0 or inside != "true":
        return {"state": "no-repo", "commit": "none", "dirty": "unknown", "label": "norepo"}

    rc, commit = _capture(["git", "rev-parse", "--short", "HEAD"])
    commit_label = commit if rc == 0 and commit else "unborn"

    # Ignore generated run artifacts so labels reflect source/config state.
    rc, status = _capture(["git", "status", "--porcelain", "--", ".", ":(exclude)docs/test-runs"])
    dirty = "dirty" if status else "clean"

    return {"state": "repo", "commit": commit_label, "dirty": dirty, "label": f"{commit_label}-{dirty}"}


def _ensure_clean_repo_for_runs() -> None:
    info = _git_info()
    if info["dirty"] != "clean":
        print(
            "ERROR: refusing to run tests with dirty source/config state. "
            "Commit or stash changes first."
        )
        raise SystemExit(2)


def _create_run_snapshot(tier: str, case_filter: str | None) -> tuple[Path, dict]:
    docs_root = ROOT / "docs" / "test-runs"
    docs_root.mkdir(parents=True, exist_ok=True)
    index_path = docs_root / "index.json"

    if index_path.exists():
        index = json.loads(index_path.read_text(encoding="utf-8"))
    else:
        index = {"next_run": 1, "runs": []}

    run_number = int(index.get("next_run", 1))
    git = _git_info()
    run_id = f"run-{run_number:04d}-{git['label']}"
    run_dir = docs_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "run_id": run_id,
        "run_number": run_number,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "tier": tier,
        "case_filter": case_filter,
        "git": git,
        "cases": [],
    }

    index["next_run"] = run_number + 1
    index["runs"].append(
        {
            "run_id": run_id,
            "run_number": run_number,
            "timestamp_utc": meta["timestamp_utc"],
            "tier": tier,
            "case_filter": case_filter,
            "git_label": git["label"],
        }
    )
    index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    (docs_root / "LATEST").write_text(run_id + "\n", encoding="utf-8")
    return run_dir, meta


def _save_case_artifacts(
    case_id: str,
    returncode: int,
    local_out_dir: Path,
    run_dir: Path,
    run_meta: dict,
) -> None:
    run_case_dir = run_dir / "cases" / case_id
    if run_case_dir.exists():
        shutil.rmtree(run_case_dir)
    run_case_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(local_out_dir, run_case_dir)
    run_meta["cases"].append({"case": case_id, "returncode": returncode, "path": str(run_case_dir)})


def _run_gmat_case(case: dict, run_dir: Path, run_meta: dict) -> int:
    gmat_bin = resolve_gmat_bin()
    if not gmat_bin.exists():
        print(f"ERROR: GMAT binary not found: {gmat_bin}")
        return 2

    script = ROOT / case["script"]
    if not script.exists():
        print(f"ERROR: script missing: {script}")
        return 2

    workdir = make_workdir(case["id"])
    runner = SubprocessGmatRunner(gmat_bin=gmat_bin, compat_lib_dir=resolve_compat_lib_dir())
    staged = prepare_script_in_workdir(script, workdir)

    for data_file in case.get("data_files", []):
        source = ROOT / data_file
        if not source.exists():
            print(f"ERROR: data file missing: {source}")
            return 2
        shutil.copy2(source, workdir / source.name)

    result = runner.run(GmatExecutionRequest(script_path=staged, work_dir=workdir))

    out_dir = LAB / "outputs" / case["id"]
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "stdout.txt").write_text(result.stdout, encoding="utf-8")
    (out_dir / "stderr.txt").write_text(result.stderr, encoding="utf-8")
    if (workdir / "gmat.log").exists():
        shutil.copy2(workdir / "gmat.log", out_dir / "gmat.log")

    expected = case.get("expected_report")
    if expected:
        report = workdir / expected
        if report.exists():
            shutil.copy2(report, out_dir / expected)
        else:
            print(f"WARN: expected report not found: {expected}")

    _save_case_artifacts(case["id"], result.returncode, out_dir, run_dir, run_meta)
    print(f"case={case['id']} returncode={result.returncode} out={out_dir}")
    return result.returncode


def _run_py_command(case: dict, run_dir: Path, run_meta: dict) -> int:
    cmd = case["command"].split()
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)

    out_dir = LAB / "outputs" / case["id"]
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (out_dir / "stderr.txt").write_text(proc.stderr, encoding="utf-8")

    _save_case_artifacts(case["id"], proc.returncode, out_dir, run_dir, run_meta)
    print(f"case={case['id']} returncode={proc.returncode} out={out_dir}")
    return proc.returncode


def _iter_cases(tier: str, case_id: str | None):
    cat = load_catalog(tier)
    for c in cat["cases"]:
        if case_id is None or c["id"] == case_id:
            yield c


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tier", choices=["tier1", "tier2"], default="tier1")
    parser.add_argument("--case", default=None)
    args = parser.parse_args()
    _ensure_clean_repo_for_runs()
    run_dir, run_meta = _create_run_snapshot(args.tier, args.case)
    print(f"run_snapshot={run_dir}")

    failures = 0
    seen = False
    for case in _iter_cases(args.tier, args.case):
        seen = True
        if case["type"] == "gmat_script":
            rc = _run_gmat_case(case, run_dir, run_meta)
        elif case["type"] == "python_command":
            rc = _run_py_command(case, run_dir, run_meta)
        else:
            print(f"ERROR: unsupported case type {case['type']}")
            rc = 2
        if rc != 0:
            failures += 1

    if not seen:
        print("No matching case found")
        return 2

    run_meta["failures"] = failures
    (run_dir / "manifest.json").write_text(json.dumps(run_meta, indent=2) + "\n", encoding="utf-8")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
