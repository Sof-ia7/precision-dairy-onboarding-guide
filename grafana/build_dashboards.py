#!/usr/bin/env python3
"""
Generate the four Grafana dashboards (thesis Section 5.5) as provisioning JSON.

The original dashboards were built by hand in the cluster's Grafana and were never
exported, so these are reconstructions from the thesis descriptions. Edit this
script (not the JSON) and re-run it:

    python grafana/build_dashboards.py

Tables live in the PostgreSQL schema "dairy" and use snake_case column names
(see src/load_chapter_outputs_to_postgres.py). "group" is a reserved SQL word,
so it is always quoted.
"""

from __future__ import annotations

import json
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent / "dashboards"
DS = {"type": "grafana-postgresql-datasource", "uid": "dairy-pg"}
SCHEMA = "dairy"

# Placeholder: replace with the real ThingsBoard weather dashboard URL.
WEATHER_URL = "https://REPLACE-WITH-THINGSBOARD-WEATHER-DASHBOARD-URL"


def query_var(name: str, label: str, sql: str) -> dict:
    return {
        "name": name,
        "label": label,
        "type": "query",
        "datasource": DS,
        "query": sql,
        "definition": sql,
        "refresh": 1,
        "sort": 3,
        "includeAll": False,
        "multi": False,
    }


GROUP_VAR = query_var("group", "Group", f'SELECT DISTINCT "group" FROM {SCHEMA}.chapter3_yield_group_day ORDER BY 1')
ANIMAL_VAR = query_var("animal", "Farm animal ID", f"SELECT DISTINCT farm_animal_id FROM {SCHEMA}.chapter3_yield_and_dim ORDER BY 1")
RECIPE_VAR = query_var("recipe", "Recipe", f"SELECT DISTINCT recipe_display_name FROM {SCHEMA}.chapter4_error_by_weight ORDER BY 1")


def target(sql: str, fmt: str = "time_series", ref: str = "A") -> dict:
    return {"refId": ref, "datasource": DS, "format": fmt, "rawQuery": True, "editorMode": "code", "rawSql": sql}


def panel(pid: int, title: str, ptype: str, sql: str, grid: tuple[int, int, int, int], *,
          fmt: str = "time_series", unit: str = "", description: str = "",
          options: dict | None = None, overrides: list | None = None, custom: dict | None = None) -> dict:
    x, y, w, h = grid
    return {
        "id": pid,
        "title": title,
        "description": description,
        "type": ptype,
        "datasource": DS,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "targets": [target(sql, fmt)],
        "fieldConfig": {"defaults": {"unit": unit, "custom": custom or {}}, "overrides": overrides or []},
        "options": options or {},
    }


def dashboard(uid: str, title: str, variables: list[dict], panels: list[dict], time_from: str = "now-90d", links: list | None = None) -> dict:
    return {
        "uid": uid,
        "title": title,
        "tags": ["precision-dairy"],
        "editable": True,
        "schemaVersion": 39,
        "time": {"from": time_from, "to": "now"},
        "refresh": "",
        "templating": {"list": variables},
        "links": links or [],
        "panels": panels,
    }


# CI band: fill the area between "CI upper" and "CI lower".
CI_BAND_OVERRIDES = [
    {"matcher": {"id": "byName", "options": "CI upper"},
     "properties": [{"id": "custom.fillBelowTo", "value": "CI lower"}, {"id": "custom.lineWidth", "value": 0},
                    {"id": "color", "value": {"mode": "fixed", "fixedColor": "blue"}}, {"id": "custom.fillOpacity", "value": 20}]},
    {"matcher": {"id": "byName", "options": "CI lower"},
     "properties": [{"id": "custom.lineWidth", "value": 0}, {"id": "color", "value": {"mode": "fixed", "fixedColor": "blue"}}]},
]

AVG_YIELD_SQL = f"""SELECT day AS time, avg_daily_yield AS "Avg milk yield", ci_lower AS "CI lower", ci_upper AS "CI upper"
FROM {SCHEMA}.chapter3_yield_group_day
WHERE "group"::text = '$group' AND $__timeFilter(day)
ORDER BY 1"""

NUTRIENT_SQL = f"""SELECT feeding_date AS time,
  total_protein_error_pct AS "Crude protein",
  total_andfom_error_pct AS "NDF",
  total_starch_error_pct AS "Starch"
FROM {SCHEMA}.chapter4_nutrient_error_by_formula
WHERE recipe_display_name = '$recipe' AND $__timeFilter(feeding_date)
ORDER BY 1"""


def group_traits() -> dict:
    return dashboard("dairy-group-traits", "Animal Group Traits", [GROUP_VAR], [
        panel(1, "Average milk yield (80% CI)", "timeseries", AVG_YIELD_SQL, (0, 0, 12, 9), unit="lb/day",
              description="Daily mean milk yield of the selected group. Shaded band = 80% t confidence interval (n >= 2).",
              overrides=CI_BAND_OVERRIDES),
        panel(2, "Average days in milk", "timeseries",
              f"""SELECT day AS time, avg_dim AS "Avg DIM" FROM {SCHEMA}.chapter3_yield_group_day
WHERE "group"::text = '$group' AND $__timeFilter(day) ORDER BY 1""", (12, 0, 12, 9), unit="d"),
        panel(3, "Cattle per pen", "timeseries",
              f"""SELECT day AS time, n_animals AS "Animals" FROM {SCHEMA}.chapter3_yield_group_day
WHERE "group"::text = '$group' AND $__timeFilter(day) ORDER BY 1""", (0, 9, 12, 9),
              description="Number of animals contributing records each day. Sudden changes affect the averages."),
        panel(4, "Average body weight (monthly)", "timeseries",
              # Grafana macros split their argument on commas, so build the month
              # date in a subquery and filter on the plain column.
              f"""SELECT month_start AS time, avg_weight AS "Avg weight"
FROM (
  SELECT make_date(year::int, month_num::int, 1)::timestamp AS month_start, avg_weight, "group"
  FROM {SCHEMA}.chapter3_weight_group
) w
WHERE "group"::text = '$group' AND $__timeFilter(month_start) ORDER BY 1""",
              (12, 9, 12, 9), unit="lb", custom={"drawStyle": "line", "showPoints": "always"},
              description="Monthly group mean body weight (PCDart). Less frequent than milk yield."),
    ])


def individual_traits() -> dict:
    trend_opts = {"xField": "DIM"}
    return dashboard("dairy-individual-traits", "Individual Animal Traits", [ANIMAL_VAR], [
        panel(1, "Milk yield over days in milk", "trend",
              f"""SELECT dim AS "DIM", yield AS "Milk yield" FROM {SCHEMA}.chapter3_yield_and_dim
WHERE farm_animal_id::text = '$animal' AND $__timeFilter(date) AND dim IS NOT NULL ORDER BY dim""",
              (0, 0, 24, 10), fmt="table", unit="lb/day", options=trend_opts),
        panel(2, "Body weight over days in milk", "trend",
              f"""SELECT dim AS "DIM", weight AS "Body weight" FROM {SCHEMA}.chapter3_dim_weights_merged
WHERE farm_animal_id::text = '$animal' AND $__timeFilter(file_date) AND dim IS NOT NULL AND weight IS NOT NULL ORDER BY dim""",
              (0, 10, 24, 10), fmt="table", unit="lb", options=trend_opts),
    ])


def feeding_accuracy() -> dict:
    return dashboard("dairy-feeding-accuracy", "Feeding Accuracy", [RECIPE_VAR], [
        panel(1, "Ingredient-level difference (%)", "timeseries",
              f"""SELECT feeding_date AS time, ingredient_code AS metric, participation_difference_pct AS value
FROM {SCHEMA}.chapter4_weight_difference_ing
WHERE recipe_display_name = '$recipe' AND $__timeFilter(feeding_date) ORDER BY 1""",
              (0, 0, 12, 9), unit="percent",
              description="Eq. 4.3: (actual share - called share) / called share x 100. Positive = over-delivered."),
        panel(2, "Nutrient variation (%)", "timeseries", NUTRIENT_SQL, (12, 0, 12, 9), unit="percent",
              description="Eq. 4.9: error in ration nutrient concentration (crude protein, NDF, starch)."),
        panel(3, "Total batch weight variation (%)", "timeseries",
              f"""SELECT feeding_date AS time, error_by_weight_pct AS "Batch weight error"
FROM {SCHEMA}.chapter4_error_by_weight
WHERE recipe_display_name = '$recipe' AND $__timeFilter(feeding_date) ORDER BY 1""",
              (0, 9, 12, 9), unit="percent", description="Eq. 4.4: (actual batch DM - called batch DM) / called x 100."),
        panel(4, "Average delivered percentages", "piechart",
              f"""SELECT ingredient_code AS "Ingredient", AVG(actual_pct_participation) AS "Avg delivered %"
FROM {SCHEMA}.chapter4_dry_weight_participation
WHERE recipe_display_name = '$recipe' AND $__timeFilter(feeding_date)
GROUP BY 1 ORDER BY 2 DESC""",
              (12, 9, 12, 9), fmt="table", unit="percent",
              options={"reduceOptions": {"values": True, "calcs": [], "fields": ""}, "pieType": "pie",
                       "legend": {"displayMode": "table", "placement": "right", "values": ["value"]}}),
    ])


def combined() -> dict:
    links = [{"title": "Weather (ThingsBoard)", "type": "link", "url": WEATHER_URL, "targetBlank": True, "icon": "external link"}]
    return dashboard("dairy-yield-nutrient-weather", "Milk Yield, Nutrient Variation and Temperature", [GROUP_VAR, RECIPE_VAR], [
        panel(1, "Average milk yield (80% CI)", "timeseries", AVG_YIELD_SQL, (0, 0, 24, 9), unit="lb/day",
              overrides=CI_BAND_OVERRIDES),
        panel(2, "Nutrient variation (%)", "timeseries", NUTRIENT_SQL, (0, 9, 24, 9), unit="percent"),
        {
            "id": 3, "type": "text", "title": "Weather", "gridPos": {"x": 0, "y": 18, "w": 24, "h": 3},
            "options": {"mode": "markdown",
                        "content": f"Barn and outdoor temperature/humidity are on the [ThingsBoard weather dashboard]({WEATHER_URL}) (managed by Purdue IT)."},
        },
    ], links=links)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, build in {
        "group-traits.json": group_traits,
        "individual-traits.json": individual_traits,
        "feeding-accuracy.json": feeding_accuracy,
        "yield-nutrient-weather.json": combined,
    }.items():
        (OUT_DIR / name).write_text(json.dumps(build(), indent=2) + "\n")
        print(f"wrote {OUT_DIR / name}")


if __name__ == "__main__":
    main()
