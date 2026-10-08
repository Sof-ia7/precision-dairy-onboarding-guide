# Precision Dairy Dashboards: Onboarding Guide

[![CI](https://github.com/Sof-ia7/precision-dairy-onboarding-guide/actions/workflows/ci.yml/badge.svg)](https://github.com/Sof-ia7/precision-dairy-onboarding-guide/actions/workflows/ci.yml)

**Welcome!** If you are taking over this project, start here. This page explains **what the project is, how the pieces fit together, what is finished, what is still missing**, and then walks you **step by step** from zero to a deployed system.

This project comes from the MS thesis *Container-Based Data Integration for Centralized Visualization* (Sofia Gerena Godoy, Purdue Agricultural & Biological Engineering, 2026). The thesis explains the *why* and the math; this repository is the *how*.

> **Where things stand:** the software works and is tested, but it has **not been deployed on the Purdue cluster yet**. A few cluster-side facts are missing, mainly about access and where data lives. Section 3 lists them. You do not need the cluster to start: Step 2 runs everything on your laptop in about 15 minutes.

---

## Contents
1. [The big picture](#1-the-big-picture)
2. [How it works](#2-how-it-works)
3. [Project status: done and missing](#3-project-status-done-and-missing)
4. [The guide, step by step](#4-the-guide-step-by-step)
5. [Reference](#5-reference)
6. [Glossary](#6-glossary)

---

## 1. The big picture

### The problem
The Purdue Dairy farm (ASREC) uses several separate software systems:

| System | What it records |
|---|---|
| **Afimilk** | milk yield per cow per day, days in milk, pen group |
| **PCDart** | herd records, including monthly body weights |
| **TMR Tracker** | feed mixing: how much of each ingredient the nutritionist *called* for and how much was *actually* loaded |
| **Weather sensors** | temperature and humidity inside and outside the barn (shown on a ThingsBoard dashboard run by Purdue IT) |

Their data is copied to Purdue's research computing cluster (**Geddes**), into a shared storage area called the **PASDE Data Depot**. But there it is only usable by researchers with cluster accounts who can write Python. **Farm staff and the nutritionist cannot see it.**

### The solution
An automatic pipeline that, once a day:
1. **reads** the farm files from the Data Depot,
2. **calculates** herd and feeding indicators (thesis Chapters 3 and 4),
3. **stores** the results in a database, and
4. **shows** them in **Grafana dashboards** that anyone with the link can open in a web browser, with no cluster account needed.

Everything runs in **containers**, packaged software that runs the same way on a laptop and on the cluster. That makes it reproducible and easy to hand over.

### What farm staff get: 4 dashboards
| Dashboard | Choose | See |
|---|---|---|
| **Animal Group Traits** | a pen group + dates | average milk yield (with an 80 % confidence band), average days in milk, number of cows, monthly body weight |
| **Individual Animal Traits** | a cow + dates | that cow's milk yield and body weight across her lactation |
| **Feeding Accuracy** | a recipe + dates | how far each ingredient, each batch, and the ration's protein/fiber/starch were from what the nutritionist planned |
| **Milk Yield, Nutrient Variation & Temperature** | a group, a recipe + dates | milk yield next to feeding errors, plus a link to the weather dashboard |

---

## 2. How it works

```
 ┌──────────────── FARM ────────────────┐
 │ Afimilk   PCDart   TMR Tracker  Weather sensors ──► ThingsBoard (Purdue IT)
 └───────────────┬──────────────────────┘
                 │ Globus upload. Today a person starts it by hand; TMR data arrives ~weekly by USB.
                 ▼
 ┌──────────── GEDDES CLUSTER (Kubernetes, managed with Rancher) ────────────┐
 │                                                                            │
 │  PASDE Data Depot  /depot/agpasde/...   (farm files, read-only)            │
 │        │                                                                   │
 │        ▼                                                                   │
 │  ① PIPELINE container  ── runs once a day (Kubernetes CronJob)            │
 │     src/run_all.py                                                         │
 │       a) chapter3_herd_pipeline.py  → herd tables                          │
 │       b) chapter4_feed_pipeline.py  → feeding tables                       │
 │       c) load_chapter_outputs_to_postgres.py → database                    │
 │        │                                                                   │
 │        ▼                                                                   │
 │  ② POSTGRESQL database  ── always on, keeps the 14 result tables          │
 │        │  (Grafana uses a read-only login)                                 │
 │        ▼                                                                   │
 │  ③ GRAFANA  ── always on, serves the 4 dashboards                         │
 └────────┬───────────────────────────────────────────────────────────────────┘
          ▼
   Farm staff / nutritionist open a web link
```

**Three containers, three jobs:**
- **① Pipeline:** this repository's own image, `ghcr.io/sof-ia7/precision-dairy-pipeline`. It starts, does the math, loads the database and **exits**. It never stores anything itself.
- **② PostgreSQL:** the official database image. It holds the results between runs.
- **③ Grafana:** the official Grafana Open Source image. It reads the database and draws the charts. Its 4 dashboards are stored in this repo as files, so a fresh Grafana always looks the same.

**What the pipeline calculates (short version):**
- **Herd (thesis Ch. 3):** for every group and day, group and month, and cow: mean, standard deviation, standard error and an **80 % confidence interval** (only when there are at least 2 values). Body weights are matched to cows by month and are **not** invented for missing days.
- **Feeding (thesis Ch. 4):** everything on a **dry-matter basis**.
  - **Ingredients:** each ingredient's share of the batch (planned vs actual) and its % error.
  - **Batches:** the total batch weight error.
  - **Nutrients:** how those errors change the ration's **crude protein, NDF and starch** (equations 4.1–4.9).
- **Deliberately not done:** filling in missing values, removing outliers, feed refusals, alerts.

---

## 3. Project status: done and missing

### ✅ Done and tested
- The pipeline code (Chapters 3 and 4) runs from start to finish. Several bugs in the original code were fixed; see [HANDOFF.md §5](HANDOFF.md#5-changes-from-the-original-repository).
- **Tests** reproduce the numbers in the thesis tables, using **synthetic** (made-up) data that follows the real file formats.
- The container image **builds and is published automatically** on every change (GitHub Actions → GHCR).
- The full system (pipeline + PostgreSQL + Grafana) runs locally with one command. Every dashboard panel is checked to return data.
- Kubernetes files for the cluster are written (`deploy/`), with clear `REPLACE` markers where information is missing.

### ⚠️ Done, but needs checking
- **The dashboards are reconstructions.** The original dashboards were built by hand on the cluster and never exported. These were rebuilt from the thesis descriptions, so compare them with thesis Figures 5.3–5.6.
- **Real data has never gone through this repository's code.** Real column names may differ from what the code expects; the code accepts many common variants.

### ❌ Missing (blocks deployment)
| What | Why it matters | Who can answer |
|---|---|---|
| **Cluster access** for the person deploying | Rancher, `kubectl` and the image registry all use your Purdue account. **This is the biggest obstacle.** | your advisor → RCAC |
| **How containers can read the Data Depot** | the pipeline cannot see the farm files without it | RCAC |
| Real paths of the **body-weight**, **TMR Tracker** and **nutrient table** files | only the Afimilk path is known | PASDE team / lab / nutritionist |
| Storage class names, namespace, web address (ingress) for Grafana | needed to fill in `deploy/` | visible in Rancher, or ask RCAC |
| ThingsBoard weather dashboard URL | for the weather link | Purdue IT |

Full details, with where each answer goes: **[HANDOFF.md](HANDOFF.md)**.

### 📦 Still to be added to this repo
Part of the original work lives on a **separate private server** and will be added later:
- `migrar.py`, the script that converts data into SQL,
- several versions of the database,
- the Grafana setup used there.

When it arrives, it may replace or improve the reconstructed dashboards in this repo.

---

## 4. The guide, step by step

### Step 0: What you need
- A computer with **Linux, macOS, or Windows + WSL**
- **Python 3.11+**, **Git**, and **Podman** (recommended) or Docker
- For deployment (Step 5): an active **Purdue account with access to a Geddes namespace**

### Step 1: Understand the project (about 1 hour)
1. Read sections 1–3 of this page.
2. Skim the thesis: **Chapter 2** (data flow), **Chapter 3** (herd math), **Chapter 4** (feed math) and **Chapter 5** (containers and dashboards).
3. Read [HANDOFF.md](HANDOFF.md) to see the open questions and constraints.

### Step 2: Run everything on your laptop (about 15 minutes, no cluster needed)
```bash
git clone https://github.com/Sof-ia7/precision-dairy-onboarding-guide.git
cd precision-dairy-onboarding-guide

# a) run the tests (no containers needed)
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt pytest
pytest -q                                      # expect: 10 passed

# b) start the whole system on made-up data
cp postgres.env.example postgres.env           # then edit the three passwords
python tests/make_sample_data.py sample_data
podman compose up --build                      # or: docker compose up --build
```
Open **http://localhost:3000** and log in with `GF_SECURITY_ADMIN_USER` / `GF_SECURITY_ADMIN_PASSWORD` from `postgres.env`. The dashboards are in the **Precision Dairy** folder.

> **"No data"?** The sample data covers **20 Nov – 19 Dec 2025**. Set the time picker to those dates, or open
> http://localhost:3000/d/dairy-group-traits?from=2025-11-15&to=2025-12-31

When you are done: `podman compose down` (add `-v` to also delete the test database).

### Step 3: Explore and compare
- Click through the 4 dashboards and compare them with thesis **Figures 5.3–5.6**.
- To change a dashboard, edit `grafana/build_dashboards.py`, run `python grafana/build_dashboards.py`, and restart Grafana. **Don't** edit the JSON files by hand.
- Check that every panel still returns data:
  ```bash
  GF_SECURITY_ADMIN_PASSWORD=<your password> python tests/check_grafana_panels.py
  ```

### Step 4: Get access and answers
Work through the **Missing** table in section 3. Start early: access requests take the longest. Write each answer into the matching `REPLACE` spot in `deploy/` (HANDOFF.md says which file).

### Step 5: Try real data, then deploy
1. If you can, copy a few **real** input files (with values anonymized) to your laptop. Point `compose.yaml` at them instead of `sample_data/` and run Step 2 again. Fix any column-name problems **now**; it is much easier than on the cluster.
2. Follow **[DEPLOY.md](DEPLOY.md)**:
   - create the secrets
   - load the Grafana configuration
   - apply `deploy/`
   - run the pipeline once by hand
   - open Grafana

### Step 6: Keep it running
- **Code change:** push to `main` → GitHub builds a new image tagged `sha-<commit>` → put that tag in `deploy/20-pipeline-cronjob.yaml` → `kubectl apply`.
- **Nutrient table:** the nutritionist must keep it up to date. Ingredients missing from it get no nutrient values.
- **Fresh data depends on people:** the farm-to-cluster upload is manual, so the dashboards are only as current as the last upload. Automating it (StreamCI) is the top future-work item.

---

## 5. Reference

### Repository map
```
README.md                 ← you are here (overview + guide)
HANDOFF.md                status, missing information, constraints, changes from the original code
DEPLOY.md                 detailed cluster deployment
src/                      the pipeline (Python): run_all.py, chapter3_*, chapter4_*, load_*_to_postgres.py
tests/                    sample-data generator, tests, dashboard checks
Containerfile             recipe for the pipeline image (Python 3.11, runs as non-root)
compose.yaml              runs pipeline + PostgreSQL + Grafana locally
postgres/init/            first-start database setup (schema + read-only Grafana user)
grafana/                  dashboards (generated by build_dashboards.py) + Grafana configuration
deploy/                   Kubernetes files for the cluster (fill in the REPLACE markers)
.github/workflows/ci.yml  automatic tests + image build on every push
```

### Container inputs and outputs
| Path inside the container | Contents | Change it with |
|---|---|---|
| `/data/afi` | Afimilk daily `*.parquet` files (the date is taken from the file name if there is no date column) | `CH3_AFI_DIR` |
| `/data/allWeights.csv` | PCDart body weights | `CH3_WEIGHTS_CSV` |
| `/data/feed-intake` | TMR Tracker files (csv, tsv, txt, parquet, xlsx; subfolders included) | `CH4_FEED_INTAKE_DIR` |
| `/data/nutrient-table.csv` | nutrient table (crude protein, NDF, starch as % of dry matter, with dates; the newest row per ingredient is used) | `CH4_NUTRIENT_TABLE` |
| `/outputs/chapter3`, `/outputs/chapter4` | CSV copies of every result | `CH3_OUTPUT_DIR`, `CH4_OUTPUT_DIR` |

- **Database settings:** `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_SCHEMA`. Without `POSTGRES_HOST`, only the CSVs are written.
- **Handy options:** `python /app/run_all.py --dry-run`, `--skip-chapter3`, `--skip-chapter4`, `--skip-postgres`.

### Database tables (schema `dairy`)
- **Herd:** `chapter3_yield_and_dim`, `chapter3_dim_weights_merged`, `chapter3_yield_group_day`, `chapter3_animal_month_yield`, `chapter3_yield_group_month`, `chapter3_cow_month_weight`, `chapter3_weight_group`, `chapter3_yield_per_cow`
- **Feeding:** `chapter4_filtered_feed_intake`, `chapter4_dry_weight_participation`, `chapter4_weight_difference_ing`, `chapter4_error_by_weight`, `chapter4_nutrient_delivery_by_ingredient`, `chapter4_nutrient_error_by_formula`

The tables are rebuilt on every run. **The dashboards depend on these names**: if you rename one, update `grafana/build_dashboards.py` too, and let the automatic checks confirm it.

### Container image
`ghcr.io/sof-ia7/precision-dairy-pipeline` (public). Each push to `main` publishes `:latest` and `:sha-<commit>`. **Deploy a `sha-` tag**, so you always know which version is running.

---

## 6. Glossary
| Term | Meaning |
|---|---|
| **ASREC** | Animal Sciences Research and Education Center, home of the Purdue Dairy unit |
| **PASDE** | the Purdue project and pipeline that collects farm data onto the cluster |
| **Data Depot** | the shared storage on the cluster where PASDE keeps the farm files |
| **Geddes** | Purdue's (RCAC's) Kubernetes cluster where the containers will run |
| **RCAC** | Rosen Center for Advanced Computing: Purdue's research computing group, which runs Geddes |
| **Rancher / kubectl** | the web interface / command-line tool for managing containers on Geddes |
| **Harbor** | Purdue's private image registry (campus/VPN only). Optional here; this project uses GHCR. |
| **GHCR** | GitHub Container Registry, where this repo's image is published |
| **Container / image** | an image is packaged software; a container is a running copy of it |
| **CronJob** | a Kubernetes job that runs on a schedule (here: daily) |
| **Grafana** | open-source dashboard software |
| **DIM** | days in milk: days since the cow calved |
| **TMR** | total mixed ration: the blended feed delivered to each pen |
| **Called / actual weight** | what the recipe asked for / what was really loaded |
| **DM** | dry matter: feed weight without water. All feed math uses it. |
| **CP / NDF** | crude protein / neutral detergent fiber |
| **80 % CI** | 80 % confidence interval: the shaded band around averages |

---

*Origin: this repository started from [`PrecisionDairy--Read-from-Geddes-to-Grafana`](https://github.com/Sof-ia7/PrecisionDairy--Read-from-Geddes-to-Grafana) (commit `cb0a4b7`). The first commit here is that code unchanged; `git log` shows every change since.*
