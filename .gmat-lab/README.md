# GMAT Local Lab

This directory contains reproducible local orchestration assets that are tracked
in git. Runtime artifacts are excluded by `.gitignore`.

## Scope

- Tier 1: Native GMAT test cases (no paid services)
- Tier 2: Free public-data extensions (CelesTrak + SGP4)
- Tier 3: Deferred unless explicit validation need is requested

## Quick start

```bash
cd /home/jeroen/gmat
source venv/bin/activate
python3 .gmat-lab/bin/list_cases.py
python3 .gmat-lab/bin/run_case.py --case basic_leo_two_body
```

Run all Tier 1 cases:

```bash
python3 .gmat-lab/bin/run_case.py --tier tier1
```

Tier 2 setup (free data only):

```bash
pip install -r .gmat-lab/requirements.txt
python3 .gmat-lab/bin/fetch_celestrak.py --group active
python3 .gmat-lab/bin/propagate_tle_sgp4.py --input .gmat-lab/cache/celestrak_active.tle --hours 24
```

Outputs and logs are written under `.gmat-lab/outputs/`.
