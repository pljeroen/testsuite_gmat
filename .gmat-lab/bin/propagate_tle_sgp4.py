from __future__ import annotations

import argparse
import csv
from datetime import timedelta
from pathlib import Path

from sgp4.api import Satrec, jday
from sgp4.conveniences import sat_epoch_datetime

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / ".gmat-lab" / "outputs"


def _read_tles(path: Path, max_sats: int = 25):
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    sats = []
    i = 0
    while i + 2 < len(lines) and len(sats) < max_sats:
        name, l1, l2 = lines[i], lines[i + 1], lines[i + 2]
        if l1.startswith("1 ") and l2.startswith("2 "):
            sats.append((name, Satrec.twoline2rv(l1, l2)))
            i += 3
        else:
            i += 1
    return sats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--hours", type=int, default=24)
    parser.add_argument("--step-min", type=int, default=10)
    args = parser.parse_args()

    tle_path = Path(args.input)
    sats = _read_tles(tle_path)
    if not sats:
        raise SystemExit("No satellites parsed from TLE file")

    OUT.mkdir(parents=True, exist_ok=True)
    out_csv = OUT / "sgp4_propagation.csv"

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sat", "minutes", "x_km", "y_km", "z_km", "vx_kms", "vy_kms", "vz_kms", "err"])

        max_minutes = args.hours * 60
        for name, sat in sats:
            epoch_dt = sat_epoch_datetime(sat)
            for minutes in range(0, max_minutes + 1, args.step_min):
                dt = epoch_dt + timedelta(minutes=minutes)
                jd, fr = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second + dt.microsecond / 1e6)
                err, r, v = sat.sgp4(jd, fr)
                w.writerow([name, minutes, r[0], r[1], r[2], v[0], v[1], v[2], err])

    print(f"saved={out_csv} sats={len(sats)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
