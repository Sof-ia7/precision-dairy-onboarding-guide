#!/usr/bin/env python3
"""
Run every dashboard panel query THROUGH GRAFANA (so Grafana macros such as
$__timeFilter are tested too) and report rows per panel.

Usage, with the local stack running (podman compose up):
    GRAFANA_URL=http://localhost:3000 GF_SECURITY_ADMIN_USER=admin \
    GF_SECURITY_ADMIN_PASSWORD=... python tests/check_grafana_panels.py [FROM] [TO]

FROM/TO are dates (default: 2025-11-01 2026-01-01, the synthetic data range).
"""

from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DASHBOARDS = Path(__file__).resolve().parents[1] / "grafana" / "dashboards"
DS = {"type": "grafana-postgresql-datasource", "uid": "dairy-pg"}


def epoch_ms(day: str) -> str:
    return str(int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp() * 1000))


def main(argv: list[str]) -> int:
    url = os.getenv("GRAFANA_URL", "http://localhost:3000")
    user = os.getenv("GF_SECURITY_ADMIN_USER", "admin")
    password = os.environ["GF_SECURITY_ADMIN_PASSWORD"]
    auth = "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()
    time_range = {"from": epoch_ms(argv[1] if len(argv) > 1 else "2025-11-01"),
                  "to": epoch_ms(argv[2] if len(argv) > 2 else "2026-01-01")}

    def query(q: dict) -> dict:
        body = json.dumps({**time_range, "queries": [q]}).encode()
        req = urllib.request.Request(f"{url}/api/ds/query", data=body,
                                     headers={"Content-Type": "application/json", "Authorization": auth})
        try:
            return json.load(urllib.request.urlopen(req))["results"][q["refId"]]
        except urllib.error.HTTPError as exc:
            return json.load(exc)["results"][q["refId"]]

    failures = 0
    for path in sorted(DASHBOARDS.glob("*.json")):
        dash = json.loads(path.read_text())
        values = {}
        for var in dash["templating"]["list"]:
            res = query({"refId": "V", "datasource": DS, "rawSql": var["query"], "format": "table"})
            values[var["name"]] = str(res["frames"][0]["data"]["values"][0][0])
        for panel in dash["panels"]:
            for target in panel.get("targets", []):
                sql = target["rawSql"]
                for name, value in values.items():
                    sql = sql.replace(f"${name}", value)
                res = query({**target, "rawSql": sql})
                if res.get("error"):
                    failures += 1
                    print(f"FAIL {path.name} / {panel['title']}: {res['error']}")
                    continue
                rows = sum(len(f["data"]["values"][0]) for f in res.get("frames", []) if f["data"]["values"])
                status = "ok  " if rows else "EMPTY"
                failures += 0 if rows else 1
                print(f"{status} {path.name} / {panel['title']}: {rows} rows")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
