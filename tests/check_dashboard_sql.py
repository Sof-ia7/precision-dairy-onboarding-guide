#!/usr/bin/env python3
"""
Run every SQL query from the Grafana dashboards against a loaded database.

Grafana macros and variables are replaced with plain SQL so the queries can run
outside Grafana. Used in CI after the pipeline has loaded the synthetic data;
connects with the read-only Grafana user (GRAFANA_DB_USER / GRAFANA_DB_PASSWORD).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text

DASHBOARDS = Path(__file__).resolve().parents[1] / "grafana" / "dashboards"


def first_value(conn, sql: str) -> str:
    row = conn.execute(text(sql)).first()
    if row is None:
        raise SystemExit(f"Variable query returned no rows: {sql}")
    return str(row[0])


def main() -> int:
    url = "postgresql+psycopg2://{u}:{p}@{h}:{port}/{db}".format(
        u=quote_plus(os.environ["GRAFANA_DB_USER"]),
        p=quote_plus(os.environ["GRAFANA_DB_PASSWORD"]),
        h=os.environ["POSTGRES_HOST"],
        port=os.environ.get("POSTGRES_PORT", "5432"),
        db=os.environ["POSTGRES_DB"],
    )
    engine = create_engine(url)
    failures = 0
    with engine.connect() as conn:
        for path in sorted(DASHBOARDS.glob("*.json")):
            dash = json.loads(path.read_text())
            values = {v["name"]: first_value(conn, v["query"]) for v in dash["templating"]["list"]}
            for panel in dash["panels"]:
                for target in panel.get("targets", []):
                    sql = re.sub(r"\$__timeFilter\([^()]*(\([^()]*\)[^()]*)*\)", "TRUE", target["rawSql"])
                    for name, value in values.items():
                        sql = sql.replace(f"${name}", value)
                    try:
                        rows = conn.execute(text(sql)).fetchall()
                        print(f"ok   {path.name} / {panel['title']}: {len(rows)} rows")
                        if not rows:
                            failures += 1
                            print("     ^ returned no rows")
                    except Exception as exc:  # noqa: BLE001
                        failures += 1
                        conn.rollback()
                        print(f"FAIL {path.name} / {panel['title']}: {exc}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
