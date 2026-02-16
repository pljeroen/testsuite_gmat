from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path



def _dist(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--threshold-km", type=float, default=5.0)
    args = parser.parse_args()

    input_path = Path(args.input)
    by_minute: dict[int, list[tuple[str, tuple[float, float, float]]]] = defaultdict(list)

    with input_path.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            if int(row["err"]) != 0:
                continue
            minute = int(row["minutes"])
            sat = row["sat"]
            pos = (float(row["x_km"]), float(row["y_km"]), float(row["z_km"]))
            by_minute[minute].append((sat, pos))

    out_path = Path(".gmat-lab/outputs/conjunction_flags.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["minutes", "sat_a", "sat_b", "distance_km"])
        for minute, entries in sorted(by_minute.items()):
            for i in range(len(entries)):
                for j in range(i + 1, len(entries)):
                    sa, pa = entries[i]
                    sb, pb = entries[j]
                    d = _dist(pa, pb)
                    if d <= args.threshold_km:
                        w.writerow([minute, sa, sb, f"{d:.6f}"])

    print(f"saved={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
