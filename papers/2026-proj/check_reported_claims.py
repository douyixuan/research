#!/usr/bin/env python3
import csv
from pathlib import Path

here = Path(__file__).resolve().parent
rows = list(csv.DictReader((here / "reported_means.csv").open()))

for row in rows:
    proj = float(row["proj_tokens"])
    baselines = {
        "Vulcan": float(row["vulcan_tokens"]),
        "LPR": float(row["lpr_tokens"]),
        "C-Reduce": float(row["creduce_tokens"]),
    }
    best_name, best = min(baselines.items(), key=lambda kv: kv[1])
    reduction = 100.0 * (best - proj) / best
    reported = float(row["reported_improvement_pct"])
    print(
        f'{row["suite"]}: PROJ={proj:g}, best={best_name} {best:g}, '
        f'ratio-of-means={reduction:.1f}%, paper={reported:.1f}%'
    )
    # The paper reports the mean of per-case percentage changes, while this
    # compact audit only has Table-II suite means. They should therefore be
    # close, but need not be bit-for-bit identical.
    assert abs(reduction - reported) < 0.3

print("PASS: headline effectiveness claims are consistent with Table II suite means.")
