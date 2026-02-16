from __future__ import annotations

import argparse
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / ".gmat-lab" / "cache"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", default="active")
    args = parser.parse_args()

    CACHE.mkdir(parents=True, exist_ok=True)
    url = f"https://celestrak.org/NORAD/elements/gp.php?GROUP={args.group.upper()}&FORMAT=tle"
    out = CACHE / f"celestrak_{args.group.lower()}.tle"

    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    out.write_text(resp.text, encoding="utf-8")
    print(f"saved={out} bytes={out.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
