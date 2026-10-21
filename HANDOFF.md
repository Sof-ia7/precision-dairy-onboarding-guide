# Handoff: what is done, what is missing, and why

This document is for the next person who picks up the project. The original author could not finish the deployment because their Purdue account access became limited. Everything that does **not** need the cluster is done and tested. What remains needs someone with **active Geddes access** and a few answers from **RCAC / Purdue IT**.

---

## 1. Status

| Part | Status |
|---|---|
| Chapter 3 herd pipeline | ✅ works on synthetic data; matches the thesis statistics (80 % t CI, n ≥ 2) |
| Chapter 4 feed pipeline | ✅ works; reproduces thesis Tables 4.3/4.4 (e.g. DRYCOW 2025-12-16: 1708 vs 1684 lb DM → 1.43 %) |
| PostgreSQL loader | ✅ stable table names, snake_case columns; tested with Podman against PostgreSQL 16, including the read-only Grafana user (can read, cannot write) |
| Container image | ✅ builds with Podman 5.7 and runs the full workflow as non-root (exit 0). CI will also build it and push it to GHCR. |
| Grafana dashboards | ⚠️ **reconstructed** from the thesis text (the originals were never exported). All 4 load in Grafana 11.6 and all 12 panels return data through Grafana (`tests/check_grafana_panels.py`), but the visual layout has not been compared with thesis Figures 5.3–5.6. |
| Kubernetes manifests | ⚠️ written, **never applied**: placeholders still need values (see §2) |
| Deployed on Geddes | ❌ not done |
| Real data | ❌ never run in this repo. Tested only on synthetic data that follows the thesis tables. |

## 2. Missing information (blocking deployment)

Every `REPLACE` in `deploy/` corresponds to one of these.

| # | Missing | Where it goes | Who can answer |
|---|---|---|---|
| 1 | **How pods can read the PASDE Data Depot** (`/depot/agpasde/...`): an existing PVC in the namespace? a hostPath? something else? | `deploy/20-pipeline-cronjob.yaml`, volume `pasde` | RCAC |
| 2 | **Real path of the PCDart body-weight file** (`allWeights.csv`). It may be a manual export, not something PASDE delivers. | `CH3_WEIGHTS_CSV` | PASDE team / lab |
| 3 | **Real path of the TMR Tracker files** | `CH4_FEED_INTAKE_DIR` | PASDE team |
| 4 | **Real path of the nutrient table.** The nutritionist keeps it as Excel with macros on the farm computer, so a CSV (or the xlsx) must reach the Depot. | `CH4_NUTRIENT_TABLE` | nutritionist / farm |
| 5 | Namespace name, Ceph **storage class** names, resource quota | all `storageClassName`, `kubectl` context | visible in Rancher once logged in |
| 6 | **Ingress** class and host name for Grafana. Should farm staff reach it off campus? | `deploy/30-grafana.yaml` | RCAC |
| 7 | ThingsBoard weather dashboard URL | `WEATHER_URL` in `grafana/build_dashboards.py` | Purdue IT |
| 8 | Real column names of the input files. The code recognizes many variants, but real files were never tested here. | none, unless a run fails | first real run |

The only path known for sure is Afimilk: `/depot/agpasde/data/Reference/purdue/asrec/dairy/afimilk-daily`.

## 2b. Work not yet in this repo (private server)
Part of the original work lives on a separate private Fedora server and will be added later:
- `migrar.py`, the script that converts data into SQL
- several versions of the database
- the Grafana setup used there

When it is added, compare its dashboards and SQL with `grafana/` here. Prefer the originals where they differ, and remove any passwords before committing; this repo is public.

## 3. Constraints

### Access and IT (the biggest obstacle)
- **Geddes access is per person.** Rancher, `kubectl` and Harbor all use the Purdue career account. A limited or expired account cannot deploy. Make sure the next maintainer has an active account **in the right namespace** before starting. The lab PI may need to request it from RCAC.
- IT said namespace owners can deploy and manage workloads **themselves**, so IT does not need to deploy it. They are still the source for the facts in §2.
- **Harbor** (`geddes-registry.rcac.purdue.edu`) is only reachable **on campus or via the Purdue VPN** and is optional. CI therefore publishes to **GHCR**, which works from anywhere. GitHub's runners cannot reach Harbor.
- **RCAC rule:** pull Docker Hub images through `geddes-registry.rcac.purdue.edu/docker-hub-cache/...` because of Docker Hub rate limits. The manifests do this already.
- Do not hard-code `/depot/...` in Python. Paths are given only through mounts and env vars.

### Data
- **Upstream ingestion is manual.** Someone must run the Globus upload from the farm computer, and TMR Tracker data reaches that computer by **USB, about weekly**. The dashboards can only be as fresh as the last upload. StreamCI was being evaluated to automate this (thesis §5.2).
- The **nutrient table must be kept current** by the nutritionist. An ingredient missing from the table gets blank nutrient values, and the pipeline does not drop or guess them.
- New ingredient names that do not match the built-in rules can be mapped with an `--ingredient-map` file (`CH4_INGREDIENT_MAP`) instead of changing the code.
- No outlier removal and no filling of missing values: unusual values in the dashboards should be checked in the source system.
- Feed refusals (weighbacks) are **not** used, so the feeding dashboard measures **delivery accuracy, not intake**.

### Security
- No farm data, outputs or passwords in git or in the image (`.gitignore` and `.containerignore` enforce this).
- Grafana connects with a **read-only** database user.
- Grafana should not be public with anonymous access turned on.

## 4. Suggested order for the next person
1. Run it locally: `pytest -q`, then `podman compose up --build` (see README). This takes about 15 minutes and needs no cluster.
2. Get Geddes access and answers to §2 items 1–5.
3. If possible, copy a few **real** input files (with values anonymized) and run the pipeline locally against them. Fix any column-name mismatches **before** deploying.
   - **Check the ingredient codes.** The original code coded "SOYBEAN MEAL" as `SOY` (soy hulls); see §5. List every ingredient name in the real TMR files with the code the pipeline gives it:
     ```bash
     python3 -c "
     import sys; sys.path.insert(0, 'src')
     from chapter4_feed_pipeline import load_feed_intake_data, find_column, FEED_COLUMN_CANDIDATES, standardize_ingredient_code
     df = load_feed_intake_data(sys.argv[1])
     col = find_column(df, FEED_COLUMN_CANDIDATES['ingredient_name'])
     for name in sorted(df[col].dropna().astype(str).unique()): print(repr(name), '->', standardize_ingredient_code(name))
     " <path to the TMR files>
     ```
     Every code must match a code in the nutrient table. Watch soy products: a name the rules do not know (e.g. `SOYPLUS`, `SOYBEANS`) falls back to its first three letters and gets **soy-hull** values. Fix wrong codes with an `--ingredient-map` file (`CH4_INGREDIENT_MAP`), not by editing the code.
     If any name starts with "SOYBEAN", results made with the original code (or the thesis Appendix A.2 code) gave soybean meal soy-hull nutrient values, and the nutrient errors and the soybean meal / soy hull shares from that code should be recalculated.
4. Follow [DEPLOY.md](DEPLOY.md) step by step, starting with a manual Job run.
5. Compare the dashboards with thesis Figures 5.3–5.6 and adjust `grafana/build_dashboards.py`.
6. Optional, if the old cluster Grafana still exists: export its dashboards (*Share → Export → Save to file*) and compare.

## 5. Changes from the original repository
The first commit is the original code, unchanged (from `PrecisionDairy--Read-from-Geddes-to-Grafana` @ `cb0a4b7`). Fixes since then:
- `chapter3_herd_pipeline.py` **did not run** (SyntaxError): a find-and-replace had pasted the end of the script inside `Path("")`. It was repaired; the pasted copy and the remaining copy were identical apart from defaults.
- `run_all.py` passed `--confidence-level`, which Chapter 3 does not accept, so the whole run would fail.
- Chapter 4 coded **"SOYBEAN MEAL" as `SOY`** (soy hulls) instead of `SBM`, because the 3-letter rule ran before the phrase rules. If the real TMR files use the full name, soybean meal got soy-hull nutrient values.
- The PostgreSQL table names did not match the README. They are now fixed explicitly in the loader.
- The Containerfile copied a deleted `watcher.py`, never copied the pipeline, used Python 3.14 (the thesis says 3.11) and ran as root.

Known differences from the thesis, left as-is:
- The monthly body-weight table has mean/SD/SE but **no confidence interval**. The thesis says one "can be included".
- The nutrient table's NDF column is stored as `andfom` (the lab's aNDFom). The dashboards label it NDF.
