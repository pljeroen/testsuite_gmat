from __future__ import annotations

from common import load_catalog

for tier in ("tier1", "tier2"):
    cat = load_catalog(tier)
    print(f"\n[{tier}] {cat['description']}")
    for case in cat["cases"]:
        tags = ", ".join(case.get("tags", []))
        print(f"- {case['id']}: {tags}")
