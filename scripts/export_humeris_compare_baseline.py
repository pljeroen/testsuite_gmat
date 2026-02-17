#!/usr/bin/env python3
"""Export normalized GMAT baseline payload for cross-suite comparison."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _read_last_numeric_row(path: Path, expected_values: int) -> list[float]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    for line in reversed(lines):
        parts = line.split()
        try:
            values = [float(token) for token in parts]
        except ValueError:
            continue
        if len(values) == expected_values:
            return values
    raise ValueError(f"No numeric row with {expected_values} values in {path}")


def export_baseline(run_dir: Path, out_path: Path) -> Path:
    cases = run_dir / "cases"
    basic = _read_last_numeric_row(cases / "basic_leo_two_body" / "basic_leo_two_body_results.txt", 7)
    j2 = _read_last_numeric_row(cases / "advanced_j2_raan_drift" / "advanced_j2_raan_drift_results.txt", 7)
    hyp = _read_last_numeric_row(cases / "advanced_oumuamua_hyperbolic" / "advanced_oumuamua_hyperbolic_results.txt", 7)

    kepler_path = cases / "headless_oem_ephemeris_propagation" / "KeplerianElements.txt"
    rows = [ln.strip() for ln in kepler_path.read_text(encoding="utf-8").splitlines() if ln.strip()]

    payload = {
        "run_id": run_dir.name,
        "cases": {
            "basic_leo_two_body": {
                "startSMA": basic[0],
                "startECC": basic[1],
                "startRMAG": basic[2],
                "endSMA": basic[3],
                "endECC": basic[4],
                "endRMAG": basic[5],
                "elapsedSecs": basic[6],
            },
            "advanced_j2_raan_drift": {
                "startRAAN": j2[0],
                "startINC": j2[1],
                "startECC": j2[2],
                "endRAAN": j2[3],
                "endINC": j2[4],
                "endECC": j2[5],
                "elapsedDays": j2[6],
            },
            "advanced_oumuamua_hyperbolic": {
                "startECC": hyp[0],
                "startINC": hyp[1],
                "startRMAG": hyp[2],
                "endECC": hyp[3],
                "endINC": hyp[4],
                "endRMAG": hyp[5],
                "elapsedDays": hyp[6],
            },
        },
        "oem_summary": {
            "rows": max(0, len(rows) - 1),
            "first": rows[1] if len(rows) > 1 else "",
            "last": rows[-1] if len(rows) > 1 else "",
        },
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return out_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--out", default="docs/interop/humeris_compare_baseline.json")
    args = ap.parse_args()

    out = export_baseline(Path(args.run_dir), Path(args.out))
    print(f"wrote={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
