"""
End-to-end tests on synthetic data (no cluster, no database needed).

Run from the repository root:
    pip install -r requirements.txt pytest
    pytest -q
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(ROOT / "tests"))

import chapter4_feed_pipeline as ch4  # noqa: E402
import load_chapter_outputs_to_postgres as loader  # noqa: E402
import make_sample_data  # noqa: E402

CHAPTER3_FILES = [
    "table_3_1_yield_and_dim.csv",
    "table_3_2_dim_weights_merged.csv",
    "table_3_3_yield_group_day.csv",
    "table_3_4_yield_group_month.csv",
    "table_3_5_weight_group.csv",
    "per_cow_daily_yield_summary.csv",
    "animal_month_yield.csv",
    "cow_month_weight.csv",
]
CHAPTER4_FILES = [
    "filtered_feed_intake.csv",
    "dry_weight_participation.csv",
    "weight_difference_ing.csv",
    "error_by_weight.csv",
    "nutrient_delivery_by_ingredient.csv",
    "nutrient_error_by_formula.csv",
]


@pytest.fixture(scope="module")
def outputs(tmp_path_factory) -> Path:
    base = tmp_path_factory.mktemp("run")
    data = base / "data"
    out = base / "outputs"
    make_sample_data.main(["make_sample_data.py", str(data)])
    result = subprocess.run(
        [
            sys.executable,
            str(SRC / "run_all.py"),
            "--afi-dir", str(data / "afi"),
            "--weights-csv", str(data / "allWeights.csv"),
            "--feed-intake-dir", str(data / "feed-intake"),
            "--nutrient-table", str(data / "nutrient-table.csv"),
            "--chapter3-output-dir", str(out / "chapter3"),
            "--chapter4-output-dir", str(out / "chapter4"),
            "--skip-postgres",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return out


def test_all_output_files_exist(outputs: Path) -> None:
    for name in CHAPTER3_FILES:
        assert (outputs / "chapter3" / name).is_file(), name
    for name in CHAPTER4_FILES:
        assert (outputs / "chapter4" / name).is_file(), name


# --- Chapter 4: values from thesis Tables 4.1, 4.3 and 4.4 -------------------

def _drycow(outputs: Path, name: str) -> pd.DataFrame:
    df = pd.read_csv(outputs / "chapter4" / name)
    return df[(df["feeding_date"] == "2025-12-16") & (df["recipe_display_name"] == "DRYCOW")]


def test_batch_weight_error_matches_thesis_table_4_4(outputs: Path) -> None:
    row = _drycow(outputs, "error_by_weight.csv").iloc[0]
    assert row["dry_actual_weight_sum"] == 1708
    assert row["dry_call_weight_sum"] == 1684
    assert round(row["error_by_weight_pct"], 2) == 1.43


def test_ingredient_participation_matches_thesis_table_4_3(outputs: Path) -> None:
    df = _drycow(outputs, "dry_weight_participation.csv").set_index("ingredient_code")
    expected = {"CSL": (40.26, 39.93), "DCW": (1.37, 1.70), "PRO": (4.45, 4.68), "SBM": (5.82, 5.80), "SOY": (15.91, 15.98)}
    for code, (call_pct, actual_pct) in expected.items():
        assert round(df.loc[code, "call_pct_participation"], 2) == call_pct, code
        assert round(df.loc[code, "actual_pct_participation"], 2) == actual_pct, code


def test_soybean_meal_is_not_confused_with_soy_hulls() -> None:
    assert ch4.standardize_ingredient_code("SOYBEAN MEAL") == "SBM"
    assert ch4.standardize_ingredient_code("SOY HULLS") == "SOY"
    assert ch4.standardize_ingredient_code("CORN SILAGE") == "CSL"
    assert ch4.standardize_ingredient_code("CSL") == "CSL"


def test_most_recent_nutrient_value_is_used(outputs: Path) -> None:
    df = _drycow(outputs, "nutrient_delivery_by_ingredient.csv")
    csl = df[df["ingredient_code"] == "CSL"].iloc[0]
    assert csl["protein_pct"] == 8.0  # 2026 analysis, not the older 7.0 row


def test_formula_nutrient_error_follows_equations_4_7_to_4_9(outputs: Path) -> None:
    ing = _drycow(outputs, "nutrient_delivery_by_ingredient.csv")
    formula = _drycow(outputs, "nutrient_error_by_formula.csv").iloc[0]
    call_c = (ing["dry_call_weight"] * ing["protein_pct"] / 100).sum() / ing["dry_call_weight"].sum() * 100
    act_c = (ing["dry_actual_weight"] * ing["protein_pct"] / 100).sum() / ing["dry_actual_weight"].sum() * 100
    assert formula["total_protein_error_pct"] == pytest.approx((act_c - call_c) / call_c * 100)


# --- Chapter 3: statistics framework (equations 3.2-3.5) ---------------------

def test_daily_group_summary_and_80pct_ci(outputs: Path) -> None:
    raw = pd.read_csv(outputs / "chapter3" / "table_3_1_yield_and_dim.csv")
    summary = pd.read_csv(outputs / "chapter3" / "table_3_3_yield_group_day.csv")
    row = summary.iloc[0]
    sub = raw[(raw["Date"] == row["Day"]) & (raw["Grp"] == row["Group"])]["Yield"]
    n = len(sub)
    se = sub.std(ddof=1) / np.sqrt(n)
    t = stats.t.ppf(1 - 0.20 / 2, n - 1)
    assert row["N Animals"] == n
    assert row["Avg Daily Yield"] == pytest.approx(sub.mean())
    assert row["CI Lower"] == pytest.approx(sub.mean() - t * se)
    assert row["CI Upper"] == pytest.approx(sub.mean() + t * se)


def test_weights_are_monthly_not_interpolated(outputs: Path) -> None:
    merged = pd.read_csv(outputs / "chapter3" / "table_3_2_dim_weights_merged.csv")
    per_cow_month = merged.assign(month=merged["File Date"].str[:7]).groupby(["Farm Animal ID", "month"])["Weight"].nunique()
    assert (per_cow_month <= 1).all()


# --- PostgreSQL loader naming (Grafana queries depend on these) --------------

def test_table_names_are_stable() -> None:
    assert loader.clean_table_name("table_3_3_yield_group_day", prefix="chapter3") == "chapter3_yield_group_day"
    assert loader.clean_table_name("per_cow_daily_yield_summary", prefix="chapter3") == "chapter3_yield_per_cow"
    assert loader.clean_table_name("error_by_weight", prefix="chapter4") == "chapter4_error_by_weight"


def test_column_names_are_snake_case() -> None:
    assert loader.clean_column_name("Avg Daily Yield") == "avg_daily_yield"
    assert loader.clean_column_name("Farm Animal ID") == "farm_animal_id"
    assert loader.clean_column_name("CI Lower") == "ci_lower"
