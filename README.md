# Precision Dairy Pipeline: PASDE → PostgreSQL → Grafana

[![CI](https://github.com/Sof-ia7/precision-dairy-onboarding-guide/actions/workflows/ci.yml/badge.svg)](https://github.com/Sof-ia7/precision-dairy-onboarding-guide/actions/workflows/ci.yml)

**Container image (public):** `ghcr.io/sof-ia7/precision-dairy-pipeline`. CI publishes `:latest` and `:sha-<commit>` on every push to `main`. Use a `sha-` tag when deploying.

Containerized data pipeline for the Purdue Dairy (ASREC) farm. It turns farm data stored in PASDE on the Geddes cluster into dashboards that farm staff and the nutritionist can open in a browser without cluster credentials.

Based on the MS thesis *Container-Based Data Integration for Centralized Visualization* (S. Gerena Godoy, Purdue ABE, 2026). Chapters 3–5 describe the methods implemented here.

> **Status: ready for deployment, not yet deployed.** The code runs and is tested on synthetic data. Deploying on Geddes needs a few cluster-side facts that the original author could not get. **Read [HANDOFF.md](HANDOFF.md) first.**

---

## What it does

```
Farm systems (Afimilk, PCDart, TMR Tracker, weather sensors)
      │  Globus upload (manual today)
      ▼
PASDE Data Depot on Geddes  (/depot/agpasde/...)
      │  mounted read-only
      ▼
Container 1: pipeline  (this repo's image, runs daily as a CronJob)
   src/run_all.py
     1. chapter3_herd_pipeline.py   → herd tables   (milk yield, DIM, body weight)
     2. chapter4_feed_pipeline.py   → feed tables   (feeding accuracy, nutrient error)
     3. load_chapter_outputs_to_postgres.py → PostgreSQL
   CSV backups → /outputs/chapter3, /outputs/chapter4
      ▼
PostgreSQL  (always-on pod, schema "dairy")
      ▼
Container 2: Grafana OSS  (4 provisioned dashboards, read-only DB user)
      ▼
Farm staff: web browser
```

Weather is **not processed** here. The dashboards link to the existing ThingsBoard weather dashboard that Purdue IT runs.

### Dashboards (thesis §5.5)
| Dashboard | Filters | Panels |
|---|---|---|
| Animal Group Traits | group, time | avg milk yield with 80 % CI band, avg DIM, cattle per pen, monthly body weight |
| Individual Animal Traits | animal ID, time | milk yield vs DIM, body weight vs DIM |
| Feeding Accuracy | recipe, time | ingredient-level difference %, nutrient variation % (CP/NDF/starch), batch weight variation %, average delivered % (pie) |
| Milk Yield, Nutrient Variation & Temperature | group, recipe, time | avg milk yield, nutrient variation, link to weather |

## Repository layout
```
src/                      pipeline code (copied to /app in the image)
tests/                    synthetic data generator, pytest suite, dashboard SQL check
Containerfile             image for Container 1 (Python 3.11, non-root)
compose.yaml              local stack: postgres + pipeline + grafana
postgres/init/            creates schema + read-only Grafana role on first start
grafana/                  provisioning (data source, dashboards) + dashboard generator
deploy/                   Kubernetes manifests for Geddes (with placeholders)
.github/workflows/ci.yml  tests, Postgres integration, image build → GHCR
DEPLOY.md                 step-by-step deployment on Geddes
HANDOFF.md                what is missing, constraints, who to ask
```

## Quick start (local, synthetic data, no cluster needed)

Needs Python 3.11+, and Podman or Docker for the full stack.

```bash
# 1. Tests only (no containers)
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt pytest
pytest -q

# 2. Full stack: Postgres + pipeline + Grafana
cp postgres.env.example postgres.env           # edit the passwords
python tests/make_sample_data.py sample_data
podman compose up --build                      # or: docker compose up --build
# open http://localhost:3000 and log in with GF_SECURITY_ADMIN_* from postgres.env
```

The pipeline container runs once and exits. Re-run it with `podman compose run --rm pipeline`.

**The sample data covers 2025-11-20 → 2025-12-19.** Dashboards open on "last 90 days", so set the time picker to that range or you will see "No data". For example:
`http://localhost:3000/d/dairy-group-traits?from=2025-11-15&to=2025-12-31`

Check that every panel returns data through Grafana:
```bash
GF_SECURITY_ADMIN_PASSWORD=<from postgres.env> python tests/check_grafana_panels.py
```
Stop everything with `podman compose down` (add `-v` to also delete the database volume).

## Container contract

| Container path | Contents | Override env var |
|---|---|---|
| `/data/afi` | Afimilk daily `*.parquet` files (date in the file name `YYYYMMDD` / `YYYY-MM-DD` if there is no date column) | `CH3_AFI_DIR` |
| `/data/allWeights.csv` | PCDart body weights | `CH3_WEIGHTS_CSV` |
| `/data/feed-intake` | TMR Tracker files (csv/tsv/txt/parquet/xlsx, read recursively) | `CH4_FEED_INTAKE_DIR` |
| `/data/nutrient-table.csv` | nutrient composition table (CP, NDF, starch % DM, with a date; the latest row per ingredient is used) | `CH4_NUTRIENT_TABLE` |
| `/outputs/chapter3`, `/outputs/chapter4` | CSV backups (writable) | `CH3_OUTPUT_DIR`, `CH4_OUTPUT_DIR` |

Database: `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_SCHEMA`. If `POSTGRES_HOST` is unset, the database load is skipped and only CSVs are written.

Useful flags: `python /app/run_all.py --dry-run | --skip-chapter3 | --skip-chapter4 | --skip-postgres`.

### PostgreSQL tables (schema `dairy`, snake_case columns)
- Chapter 3: `chapter3_yield_and_dim`, `chapter3_dim_weights_merged`, `chapter3_yield_group_day`, `chapter3_animal_month_yield`, `chapter3_yield_group_month`, `chapter3_cow_month_weight`, `chapter3_weight_group`, `chapter3_yield_per_cow`
- Chapter 4: `chapter4_filtered_feed_intake`, `chapter4_dry_weight_participation`, `chapter4_weight_difference_ing`, `chapter4_error_by_weight`, `chapter4_nutrient_delivery_by_ingredient`, `chapter4_nutrient_error_by_formula`

Tables are replaced on every run. **Grafana queries depend on these names.** If you rename anything, update `grafana/build_dashboards.py`, regenerate the dashboards, and let CI's dashboard-SQL check confirm the result.

## Methods (summary)
- **Herd (Ch. 3):** mean, SD (n−1), SE and an **80 % t confidence interval** (only when n ≥ 2) by group×day, group×month (via cow-month means) and per cow. Body weights are matched by cow and month and are **not interpolated** to daily values.
- **Feed (Ch. 4):** all on a **dry matter** basis.
  - Batch weights (eq. 4.1) and ingredient shares (eq. 4.2)
  - Ingredient error (eq. 4.3) and batch error (eq. 4.4)
  - Nutrient delivery and error per ingredient and per formula for crude protein, NDF and starch (eqs. 4.5–4.9)
- **Not done (by design):** no filling of missing values, no outlier removal, no feed refusals, no alerts.

## Origin
Imported from `PrecisionDairy--Read-from-Geddes-to-Grafana` (commit `cb0a4b7`). The first commit of this repo is that code unchanged; later commits fix bugs and add deployment. See `git log`.
