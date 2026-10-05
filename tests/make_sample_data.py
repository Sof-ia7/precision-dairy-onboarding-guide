#!/usr/bin/env python3
"""
Create a small SYNTHETIC dataset with the same layout the container expects.

This is not farm data. Column names follow the names the pipelines recognize
(and the thesis sample tables). The DRYCOW rows for 2025-12-16 reproduce thesis
Table 4.1 so the Chapter 4 results can be checked against Table 4.4.

Usage:
    python tests/make_sample_data.py sample_data

Creates:
    sample_data/afi/afimilk_YYYYMMDD.parquet   (one file per day)
    sample_data/allWeights.csv
    sample_data/feed-intake/feed_intake_2025-12.csv
    sample_data/nutrient-table.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
DAYS = pd.date_range("2025-11-20", "2025-12-19", freq="D")
COWS_PER_GROUP = {1: 8, 2: 8, 3: 6}

# Thesis Table 4.1 (DRYCOW, 2025-12-16). HLG is added so the batch totals match
# the thesis batch weights: call 1684 lb DM, actual 1708 lb DM.
DRYCOW_ROWS = [
    ("CORN SILAGE", 678.0, 682.0),
    ("DRY COW MIX", 23.0, 29.0),
    ("PROTEIN MIX", 75.0, 80.0),
    ("SOYBEAN MEAL", 98.0, 99.0),
    ("SOY HULLS", 268.0, 273.0),
    ("HAYLAGE", 542.0, 545.0),
]

LAC_RECIPE = [
    ("CORN SILAGE", 1800.0),
    ("HAYLAGE", 900.0),
    ("SUPER MIX", 700.0),
    ("SOYBEAN MEAL", 300.0),
    ("MOLASSES", 60.0),
]

# Thesis Table 4.2.
NUTRIENTS = [
    ("Corn Silage", "CSL", 8.00, 34.00, 37.00),
    ("Haylage", "HLG", 20.00, 42.00, 2.95),
    ("Triticale", "TCL", 12.00, 55.00, 2.50),
    ("Soybean Meal", "SBM", 53.37, 10.92, 2.17),
    ("Soy Hulls", "SOY", 12.71, 64.45, 1.02),
    ("Molasses", "MOL", 5.17, 0.00, 0.00),
    ("Super Mix", "SMX", 22.57, 14.84, 26.88),
    ("Protein Mix", "PRO", 60.58, 10.70, 2.85),
    ("Dry Cow Supplement", "LAC", 34.20, 5.70, 1.07),
    ("Drycow Mix", "DCW", 3.83, 11.26, 0.12),
]


def make_afi(out: Path, rng: np.random.Generator) -> pd.DataFrame:
    afi_dir = out / "afi"
    afi_dir.mkdir(parents=True, exist_ok=True)
    cows = []
    animal_id = 2200
    for group, n in COWS_PER_GROUP.items():
        for _ in range(n):
            animal_id += 1
            cows.append((animal_id, group, int(rng.integers(20, 300)), float(rng.normal(80, 12))))

    rows_all = []
    for i, day in enumerate(DAYS):
        rows = []
        for cow_id, group, dim0, base_yield in cows:
            yield_lb = round(max(base_yield + rng.normal(0, 4), 10.0), 1)
            rows.append(
                {
                    "farm_animal_id": cow_id,
                    "grp": group,
                    "dim": dim0 + i,
                    "daily_yield": yield_lb,
                }
            )
        df = pd.DataFrame(rows)
        df.to_parquet(afi_dir / f"afimilk_{day:%Y%m%d}.parquet", index=False)
        rows_all.append(df.assign(day=day))
    return pd.concat(rows_all, ignore_index=True)


def make_weights(out: Path, afi: pd.DataFrame, rng: np.random.Generator) -> None:
    rows = []
    for cow_id in sorted(afi["farm_animal_id"].unique()):
        for month_start in ("2025-11-25", "2025-12-15"):
            rows.append(
                {
                    "farm_animal_id": cow_id,
                    "date": month_start,
                    "weight": round(float(rng.normal(1450, 120))),
                }
            )
    pd.DataFrame(rows).to_csv(out / "allWeights.csv", index=False)


def make_feed(out: Path, rng: np.random.Generator) -> None:
    feed_dir = out / "feed-intake"
    feed_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for day in pd.date_range("2025-12-10", "2025-12-19", freq="D"):
        for ingredient, call in LAC_RECIPE:
            actual = round(call * (1 + rng.normal(0, 0.02)), 1)
            rows.append(("LAC1", "Pen 1", day, ingredient, call, actual))
        if day == pd.Timestamp("2025-12-16"):
            dry = DRYCOW_ROWS
        else:
            dry = [(ing, call, round(call * (1 + rng.normal(0, 0.03)), 1)) for ing, call, _ in DRYCOW_ROWS]
        for ingredient, call, actual in dry:
            rows.append(("DRYCOW", "Dry Pen", day, ingredient, call, actual))

    df = pd.DataFrame(
        rows,
        columns=[
            "Recipe Display Name",
            "Pen Name",
            "Feeding Date",
            "Ingredient Name",
            "Dry Call Weight",
            "Dry Actual Weight",
        ],
    )
    df["Feeding Date"] = df["Feeding Date"].dt.strftime("%Y-%m-%d")
    df.to_csv(feed_dir / "feed_intake_2025-12.csv", index=False)


def make_nutrients(out: Path) -> None:
    df = pd.DataFrame(
        NUTRIENTS,
        columns=["Ingredient", "Code", "Crude Protein (%)", "NDF (%)", "Starch (%)"],
    )
    df["Date"] = "2026-02-11"
    # An older analysis row: the pipeline must use the most recent value per code.
    old = df[df["Code"] == "CSL"].assign(**{"Crude Protein (%)": 7.0, "Date": "2025-01-01"})
    pd.concat([old, df], ignore_index=True).to_csv(out / "nutrient-table.csv", index=False)


def main(argv: list[str]) -> int:
    out = Path(argv[1] if len(argv) > 1 else "sample_data")
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    afi = make_afi(out, rng)
    make_weights(out, afi, rng)
    make_feed(out, rng)
    make_nutrients(out)
    print(f"Synthetic sample data written to {out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
