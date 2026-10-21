# 1. Table dictionary

Every column of every **output table** written by the pipeline (Chapter 3 and Chapter 4). Input files are not covered.

Part of a set of three dictionaries:

| Dictionary | What it answers |
|---|---|
| **1. Tables** (this file) | What does this column mean, and where does it come from? |
| [2. Formulas](2_formulas.md) | What does each calculation step produce? |
| [3. Math terms](3_math_terms.md) | What does each symbol in the equations mean? |

## How to read this file

- **CSV header**: the column name in the CSV files under `/outputs/chapter3` or `/outputs/chapter4`.
- **Database column**: the name in PostgreSQL / Grafana. The loader lowercases names and replaces spaces and symbols with `_`. Chapter 4 names are already in this form, so they are the same in both places.
- **Formula**: the step in [2. Formulas](2_formulas.md) that creates the value. `—` means the value is copied from the input, not calculated.
- **Math terms**: the symbols in [3. Math terms](3_math_terms.md) that contribute to the value.
- **Units**: weights in **lb**; milk yield in **lb/day**; Chapter 4 weights are **lb of dry matter (lb DM)**.
- A blank value means it could not be calculated (missing input, division by zero, or fewer than 2 observations for a confidence interval). The pipeline never fills blanks with guesses.

---

# Chapter 3: Herd characteristics

Source data: Afimilk daily files (milk yield, DIM, group) and the PCDart body-weight file.
Confidence level: 80 % by default (`CH3_CONFIDENCE_LEVEL`).

## `chapter3_yield_and_dim` (thesis Table 3.1)

CSV file: `table_3_1_yield_and_dim.csv`. One row per cow per day: the cleaned Afimilk records.

| CSV header | Database column | Meaning | Unit | Formula | Math terms |
|---|---|---|---|---|---|
| Farm Animal ID | `farm_animal_id` | Cow identifier | — | — | $r$ |
| Grp | `grp` | Group the cow was in that day (`pack` is stored as 15, `G1` as 1, ...) | — | [S3.2](2_formulas.md#s32-group-label-mapping) | $g$ |
| DIM | `dim` | Days in milk on that day | days | — | $DIM_{r,g,d}$ |
| Date | `date` | Observation day (from the file's date column, or from the file name) | date | [S3.7](2_formulas.md#s37-dates-year-and-month) | $d$ |
| Run Date Time | `run_date_time` | When Afimilk produced the record, if the file has it | date-time | — | — |
| Yield | `yield` | Daily milk yield of the cow | lb/day | [S3.1](2_formulas.md#s31-daily-milk-yield) | $Y_{r,g,d}$ |

## `chapter3_dim_weights_merged` (thesis Table 3.2)

CSV file: `table_3_2_dim_weights_merged.csv`. Only produced when the body-weight file is given. One row per cow per day, with that cow's **monthly** weight repeated on every day of the month (daily weights are not interpolated).

| CSV header | Database column | Meaning | Unit | Formula | Math terms |
|---|---|---|---|---|---|
| Farm Animal ID | `farm_animal_id` | Cow identifier | — | — | $r$ |
| File Date | `file_date` | Observation day | date | [S3.7](2_formulas.md#s37-dates-year-and-month) | $d$ |
| DIM | `dim` | Days in milk on that day | days | — | $DIM_{r,g,d}$ |
| Weight | `weight` | Body weight of the cow for that month | lb | [S3.3](2_formulas.md#s33-cow-month-body-weight) | $W_{r,g,m}$ |

## `chapter3_yield_group_day` (thesis Table 3.3)

CSV file: `table_3_3_yield_group_day.csv`. One row per group per day ($u = (g,d)$).

| CSV header | Database column | Meaning | Unit | Formula | Math terms |
|---|---|---|---|---|---|
| Day | `day` | Observation day | date | — | $d$ |
| Year | `year` | Year of the day | — | [S3.7](2_formulas.md#s37-dates-year-and-month) | $d$ |
| Month | `month` | Month name of the day | — | [S3.7](2_formulas.md#s37-dates-year-and-month) | $d$ |
| Month Num | `month_num` | Month number (1–12) | — | [S3.7](2_formulas.md#s37-dates-year-and-month) | $d$ |
| Group | `group` | Group | — | [S3.2](2_formulas.md#s32-group-label-mapping) | $g$ |
| Avg DIM | `avg_dim` | Mean days in milk of the group that day | days | [3.6](2_formulas.md#36-daily-group-mean) | $\bar{M}_{g,d}$ with $M = DIM$; $DIM_{r,g,d}$, $n_{g,d}$ |
| Avg Daily Yield | `avg_daily_yield` | Mean milk yield of the group that day | lb/day | [3.6](2_formulas.md#36-daily-group-mean) | $\bar{M}_{g,d}$ with $M = Y$; $Y_{r,g,d}$, $n_{g,d}$ |
| Yield STD | `yield_std` | Sample standard deviation of milk yield | lb/day | [3.3](2_formulas.md#33-sample-standard-deviation) | $s_{M,u}$; $Y_{r,g,d}$, $\bar{M}_{g,d}$, $n_{g,d}$ |
| N Animals | `n_animals` | Number of different cows in the group that day | cows | — | $n_{g,d}$ |
| SE | `se` | Standard error of the mean yield | lb/day | [3.4](2_formulas.md#34-standard-error) | $SE_{M,u}$; $s_{M,u}$, $n_{g,d}$ |
| T Value | `t_value` | Student's t critical value (blank when fewer than 2 cows) | — | [3.5](2_formulas.md#35-confidence-interval) | $t_{1-\alpha/2,\,n_u-1}$; $\alpha$, $n_{g,d}$ |
| CI Lower | `ci_lower` | Lower limit of the 80 % confidence interval of mean yield | lb/day | [3.5](2_formulas.md#35-confidence-interval) | $CI_{M,u}$; $\bar{M}_{g,d}$, $t$, $SE_{M,u}$ |
| CI Upper | `ci_upper` | Upper limit of the 80 % confidence interval of mean yield | lb/day | [3.5](2_formulas.md#35-confidence-interval) | $CI_{M,u}$; $\bar{M}_{g,d}$, $t$, $SE_{M,u}$ |

> Note: the thesis says the same statistics were also applied to DIM. The code only outputs the **mean** DIM; the STD, SE and CI columns are for milk yield only.

## `chapter3_animal_month_yield` (first stage of thesis Table 3.4)

CSV file: `animal_month_yield.csv`. One row per cow per group per month. A cow that changed group during a month has one row for each group.

| CSV header | Database column | Meaning | Unit | Formula | Math terms |
|---|---|---|---|---|---|
| Farm Animal ID | `farm_animal_id` | Cow identifier | — | — | $r$ |
| Year | `year` | Year | — | [S3.7](2_formulas.md#s37-dates-year-and-month) | $m$ |
| Month Num | `month_num` | Month number (1–12) | — | [S3.7](2_formulas.md#s37-dates-year-and-month) | $m$ |
| Month | `month` | Month name | — | [S3.7](2_formulas.md#s37-dates-year-and-month) | $m$ |
| Group | `group` | Group | — | [S3.2](2_formulas.md#s32-group-label-mapping) | $g$ |
| Avg Monthly Yield | `avg_monthly_yield` | Mean daily milk yield of the cow in that month | lb/day | [3.7](2_formulas.md#37-cow-month-mean-yield) | $\bar{Y}_{r,g,m}$; $Y_{r,g,d}$, $D_{r,g,m}$ |
| N Days | `n_days` | Days with a valid milk-yield record that month | days | — | $D_{r,g,m}$ |
| Avg DIM | `avg_dim` | Mean days in milk of the cow that month | days | [3.2](2_formulas.md#32-mean) | $DIM_{r,g,d}$, $D_{r,g,m}$ |
| First Day | `first_day` | First day with a record that month | date | — | $d$ |
| Last Day | `last_day` | Last day with a record that month | date | — | $d$ |

## `chapter3_yield_group_month` (thesis Table 3.4)

CSV file: `table_3_4_yield_group_month.csv`. One row per group per month ($u = (g,m)$). Built from `chapter3_animal_month_yield`: each cow counts once, with its monthly mean.

| CSV header | Database column | Meaning | Unit | Formula | Math terms |
|---|---|---|---|---|---|
| Year | `year` | Year | — | [S3.7](2_formulas.md#s37-dates-year-and-month) | $m$ |
| Month Num | `month_num` | Month number (1–12) | — | [S3.7](2_formulas.md#s37-dates-year-and-month) | $m$ |
| Month | `month` | Month name | — | [S3.7](2_formulas.md#s37-dates-year-and-month) | $m$ |
| Group | `group` | Group | — | [S3.2](2_formulas.md#s32-group-label-mapping) | $g$ |
| Avg Monthly Yield | `avg_monthly_yield` | Mean of the cows' monthly mean yields | lb/day | [3.2](2_formulas.md#32-mean) applied to [3.7](2_formulas.md#37-cow-month-mean-yield) | $\bar{M}_{g,m}$ with $M = \bar{Y}_{r,g,m}$; $n_{g,m}$ |
| Yield STD | `yield_std` | Sample standard deviation of the cows' monthly means | lb/day | [3.3](2_formulas.md#33-sample-standard-deviation) | $s_{M,u}$; $\bar{Y}_{r,g,m}$, $n_{g,m}$ |
| N Animals | `n_animals` | Number of cows in the group that month | cows | — | $n_{g,m}$ |
| SE | `se` | Standard error | lb/day | [3.4](2_formulas.md#34-standard-error) | $SE_{M,u}$; $s_{M,u}$, $n_{g,m}$ |
| T Value | `t_value` | t critical value (blank when fewer than 2 cows) | — | [3.5](2_formulas.md#35-confidence-interval) | $t_{1-\alpha/2,\,n_u-1}$; $\alpha$, $n_{g,m}$ |
| CI Lower | `ci_lower` | Lower limit of the 80 % confidence interval | lb/day | [3.5](2_formulas.md#35-confidence-interval) | $CI_{M,u}$ |
| CI Upper | `ci_upper` | Upper limit of the 80 % confidence interval | lb/day | [3.5](2_formulas.md#35-confidence-interval) | $CI_{M,u}$ |

## `chapter3_cow_month_weight` (intermediate for thesis Table 3.5)

CSV file: `cow_month_weight.csv`. Only produced when the body-weight file is given. One row per cow per month that has both Afimilk records and a body weight.

| CSV header | Database column | Meaning | Unit | Formula | Math terms |
|---|---|---|---|---|---|
| Farm Animal ID | `farm_animal_id` | Cow identifier | — | — | $r$ |
| Year | `year` | Year | — | [S3.7](2_formulas.md#s37-dates-year-and-month) | $m$ |
| Month Num | `month_num` | Month number (1–12) | — | [S3.7](2_formulas.md#s37-dates-year-and-month) | $m$ |
| Group | `group` | The cow's most frequent Afimilk group that month (from the weight file if Afimilk has none) | — | [S3.4](2_formulas.md#s34-cow-month-group) | $g$ |
| Avg DIM | `avg_dim` | Mean days in milk of the cow that month | days | [3.2](2_formulas.md#32-mean) | $DIM_{r,g,d}$ |
| First AFI Day | `first_afi_day` | First Afimilk day of the cow that month | date | — | $d$ |
| Last AFI Day | `last_afi_day` | Last Afimilk day of the cow that month | date | — | $d$ |
| N AFI Days | `n_afi_days` | Number of Afimilk days of the cow that month | days | — | — |
| Month | `month` | Month name | — | [S3.7](2_formulas.md#s37-dates-year-and-month) | $m$ |
| Weight | `weight` | Body weight of the cow for the month (mean if weighed more than once) | lb | [S3.3](2_formulas.md#s33-cow-month-body-weight) | $W_{r,g,m}$ |
| Weight Date | `weight_date` | Latest weighing date that month (blank if the file only has months) | date | [S3.3](2_formulas.md#s33-cow-month-body-weight) | — |
| weight_group | `weight_group` | Group recorded in the weight file, if any | — | [S3.2](2_formulas.md#s32-group-label-mapping) | — |

## `chapter3_weight_group` (thesis Table 3.5)

CSV file: `table_3_5_weight_group.csv`. Only produced when the body-weight file is given. One row per group per month ($u = (g,m)$).

| CSV header | Database column | Meaning | Unit | Formula | Math terms |
|---|---|---|---|---|---|
| Year | `year` | Year | — | [S3.7](2_formulas.md#s37-dates-year-and-month) | $m$ |
| Month Num | `month_num` | Month number (1–12) | — | [S3.7](2_formulas.md#s37-dates-year-and-month) | $m$ |
| Month | `month` | Month name | — | [S3.7](2_formulas.md#s37-dates-year-and-month) | $m$ |
| Group | `group` | Group | — | [S3.4](2_formulas.md#s34-cow-month-group) | $g$ |
| N Animals | `n_animals` | Number of weighed cows in the group that month | cows | — | $n_{g,m}$ |
| Avg Weight | `avg_weight` | Mean body weight of the group | lb | [3.8](2_formulas.md#38-group-month-mean-body-weight) | $\bar{W}_{g,m}$; $W_{r,g,m}$, $n_{g,m}$ |
| Weight STD | `weight_std` | Sample standard deviation of body weight | lb | [3.3](2_formulas.md#33-sample-standard-deviation) | $s_{M,u}$ with $M = W$; $W_{r,g,m}$, $\bar{W}_{g,m}$, $n_{g,m}$ |
| SE | `se` | Standard error of the mean weight | lb | [3.4](2_formulas.md#34-standard-error) | $SE_{M,u}$; $s_{M,u}$, $n_{g,m}$ |

> Note: thesis Table 3.5 shows CI Lower / CI Upper for body weight, but the code does **not** compute a confidence interval for weight (no T Value, CI Lower or CI Upper columns).

## `chapter3_yield_per_cow` (thesis §3.3.5)

CSV file: `per_cow_daily_yield_summary.csv`. One row per cow over the whole period ($u = r$). Duplicate records for the same cow and day are averaged first ([S3.5](2_formulas.md#s35-per-cow-daily-records)).

| CSV header | Database column | Meaning | Unit | Formula | Math terms |
|---|---|---|---|---|---|
| Farm Animal ID | `farm_animal_id` | Cow identifier | — | — | $r$ |
| Group | `group` | The cow's most frequent group over the period | — | [S3.5](2_formulas.md#s35-per-cow-daily-records) | $g$ |
| Avg DIM | `avg_dim` | Mean days in milk over the period | days | [3.2](2_formulas.md#32-mean) | $DIM_{r,g,d}$, $D_r$ |
| N Days | `n_days` | Days with a valid milk-yield record | days | — | $D_r$ |
| Avg Daily Yield | `avg_daily_yield` | Mean daily milk yield of the cow | lb/day | [3.9](2_formulas.md#39-per-cow-mean-daily-yield) | $\bar{Y}_r$; $Y_{r,d}$, $D_r$ |
| Yield STD | `yield_std` | Sample standard deviation of the cow's daily yield | lb/day | [3.3](2_formulas.md#33-sample-standard-deviation) | $s_{Y,r}$; $Y_{r,d}$, $\bar{Y}_r$, $D_r$ |
| SE | `se` | Standard error | lb/day | [3.4](2_formulas.md#34-standard-error) | $SE$; $s_{Y,r}$, $D_r$ |
| T Value | `t_value` | t critical value (blank when fewer than 2 days) | — | [3.10](2_formulas.md#310-per-cow-confidence-interval) | $t_{1-\alpha/2,\,D_r-1}$; $\alpha$, $D_r$ |
| CI Lower | `ci_lower` | Lower limit of the 80 % confidence interval | lb/day | [3.10](2_formulas.md#310-per-cow-confidence-interval) | $CI_{Y,r}$; $\bar{Y}_r$, $t$, $s_{Y,r}$, $D_r$ |
| CI Upper | `ci_upper` | Upper limit of the 80 % confidence interval | lb/day | [3.10](2_formulas.md#310-per-cow-confidence-interval) | $CI_{Y,r}$; $\bar{Y}_r$, $t$, $s_{Y,r}$, $D_r$ |
| First Day | `first_day` | First day with a record | date | — | $d$ |
| Last Day | `last_day` | Last day with a record | date | — | $d$ |

Chapter 3 also writes `run_summary.json` (row counts and settings of the run). It is not loaded into the database.

---

# Chapter 4: Feed traits

Source data: TMR Tracker feed-intake files, the nutrient table, and (once configured) the refusals file. All weights are **dry matter (lb DM)**.

**Grouping.** "Formula" means one recipe on one feeding day. By default all pens fed that recipe that day are added together. With `--group-by-pen` each pen is its own formula, and the formula-level tables get a `pen_name` column. See [S4.5](2_formulas.md#s45-formula-grouping).

## Columns shared by several Chapter 4 tables

These columns have the same meaning in every table they appear in.

| Column | Meaning | Unit | Formula | Math terms |
|---|---|---|---|---|
| `feeding_date` | Feeding day | date | [S4.6](2_formulas.md#s46-dates) | — |
| `recipe_display_name` | Recipe (formula) name from TMR Tracker | — | — | — |
| `pen_name` | Pen the ingredient row was delivered to (in the formula-level tables, only with `--group-by-pen`) | — | — | — |
| `ingredient_name_raw` | Ingredient name exactly as in TMR Tracker | — | — | $i$ |
| `ingredient_code` | Standardized ingredient code used to join to the nutrient table (CSL, HLG, SBM, ...) | — | [S4.1](2_formulas.md#s41-ingredient-code-standardization) | $i$ |
| `dry_call_weight` | Dry weight of the ingredient the recipe called for | lb DM | — | $W_i^{call}$ |
| `dry_actual_weight` | Dry weight of the ingredient actually loaded | lb DM | — | $W_i^{actual}$ |
| `dry_call_weight_sum` | Total called dry weight of the formula (batch call weight) | lb DM | [4.1](2_formulas.md#41-batch-weight) | $BW^{call}$; $W_i^{call}$, $n$ |
| `dry_actual_weight_sum` | Total actual dry weight of the formula (batch actual weight) | lb DM | [4.1](2_formulas.md#41-batch-weight) | $BW^{actual}$; $W_i^{actual}$, $n$ |
| `call_pct_participation` | Ingredient's share of the called batch | % DM | [4.2](2_formulas.md#42-ingredient-share-participation) | $W_{\%,i}^{call}$; $W_i^{call}$, $BW^{call}$ |
| `actual_pct_participation` | Ingredient's share of the actual batch | % DM | [4.2](2_formulas.md#42-ingredient-share-participation) | $W_{\%,i}^{actual}$; $W_i^{actual}$, $BW^{actual}$ |
| `pct_participation` | Same value as `actual_pct_participation` (name kept from the original notebook) | % DM | [4.2](2_formulas.md#42-ingredient-share-participation) | $W_{\%,i}^{actual}$ |
| `source_file` | Input file the row came from | — | — | — |
| `source_sheet` | Excel sheet the row came from (only for Excel inputs) | — | — | — |

## `chapter4_filtered_feed_intake` (thesis Table 4.1)

CSV file: `filtered_feed_intake.csv`. One row per ingredient per formula: the cleaned TMR Tracker data with the batch totals and shares added.

Columns: `feeding_date`, `recipe_display_name`, `ingredient_name_raw`, `ingredient_code`, `pen_name`, `dry_call_weight`, `dry_actual_weight`, `dry_actual_weight_sum`, `dry_call_weight_sum`, `pct_participation`, `call_pct_participation`, `actual_pct_participation`, `source_file`, `source_sheet` (Excel only). All are defined in the shared table above.

## `chapter4_dry_weight_participation` (thesis Table 4.3)

CSV file: `dry_weight_participation.csv`. One row per ingredient per formula: each ingredient's share of the mix.

Columns: `feeding_date`, `recipe_display_name`, `ingredient_code`, `ingredient_name_raw`, `pen_name`, `dry_call_weight`, `dry_actual_weight`, `dry_call_weight_sum`, `dry_actual_weight_sum`, `call_pct_participation`, `actual_pct_participation`, `pct_participation`. All are defined in the shared table above.

## `chapter4_weight_difference_ing`

CSV file: `weight_difference_ing.csv`. One row per ingredient per formula: the ingredient-level weight error. Includes `feeding_date`, `recipe_display_name`, `ingredient_code`, `ingredient_name_raw`, `pen_name`, `dry_call_weight`, `dry_actual_weight`, `call_pct_participation`, `actual_pct_participation` (see shared table), plus:

| Column | Meaning | Unit | Formula | Math terms |
|---|---|---|---|---|
| `weight_difference_pct` | Relative error of the ingredient's dry weight: (actual − called) / called × 100. This is the value the thesis tables report. | % | [P4.1](2_formulas.md#p41-direct-ingredient-weight-error) | $E_{W,i}^{direct}$; $W_i^{actual}$, $W_i^{call}$ |
| `participation_difference_pct` | Relative error of the ingredient's share of the mix, as written in thesis Equation 4.3 | % | [4.3](2_formulas.md#43-ingredient-weight-error-participation-based) | $E_{W,i}$; $W_{\%,i}^{actual}$, $W_{\%,i}^{call}$ |

> Note: the thesis text defines Equation 4.3 with the shares (`participation_difference_pct`), but its tables match the direct weight error (`weight_difference_pct`). Both are kept so either can be used.

## `chapter4_error_by_weight` (thesis Table 4.4)

CSV file: `error_by_weight.csv`. One row per formula (recipe per day, and per pen with `--group-by-pen`).

| Column | Meaning | Unit | Formula | Math terms |
|---|---|---|---|---|
| `feeding_date` | Feeding day | date | [S4.6](2_formulas.md#s46-dates) | — |
| `recipe_display_name` | Recipe name | — | — | — |
| `pen_name` | Pen (only with `--group-by-pen`) | — | — | — |
| `dry_actual_weight_sum` | Batch actual weight | lb DM | [4.1](2_formulas.md#41-batch-weight) | $BW^{actual}$; $W_i^{actual}$ |
| `dry_call_weight_sum` | Batch call weight | lb DM | [4.1](2_formulas.md#41-batch-weight) | $BW^{call}$; $W_i^{call}$ |
| `error_by_weight_pct` | Batch-level weight error | % | [4.4](2_formulas.md#44-batch-weight-error) | $E_{BW}$; $BW^{actual}$, $BW^{call}$ |
| `refusals` | Dry feed refused (weighback) for the formula, summed across pens unless `--group-by-pen`. Blank until refusals are configured (see `HANDOFF.md`). | lb DM | [S4.4](2_formulas.md#s44-refusals-per-formula) | $R$ |
| `intake` | Dry feed actually eaten: batch actual weight minus refusals | lb DM | [P4.2](2_formulas.md#p42-intake) | $I$; $BW^{actual}$, $R$ |

## `chapter4_nutrient_delivery_by_ingredient`

CSV file: `nutrient_delivery_by_ingredient.csv`. One row per ingredient per formula: how much of each nutrient the ingredient supplied. Includes `feeding_date`, `recipe_display_name`, `ingredient_code`, `ingredient_name_raw`, `pen_name`, `dry_call_weight`, `dry_actual_weight` (see shared table), plus:

| Column | Meaning | Unit | Formula | Math terms |
|---|---|---|---|---|
| `ingredient_name_nutrient_table` | Ingredient name as written in the nutrient table | — | — | $i$ |
| `protein_pct` | Crude protein content of the ingredient (latest analysis) | % DM | [S4.2](2_formulas.md#s42-latest-nutrient-analysis) | $NCP_{CP,i}$ |
| `andfom_pct` | Fiber (aNDFom / NDF) content of the ingredient (latest analysis) | % DM | [S4.2](2_formulas.md#s42-latest-nutrient-analysis) | $NCP_{NDF,i}$ |
| `starch_pct` | Starch content of the ingredient (latest analysis) | % DM | [S4.2](2_formulas.md#s42-latest-nutrient-analysis) | $NCP_{starch,i}$ |
| `call_protein` | Crude protein the ingredient should have supplied | lb | [4.5](2_formulas.md#45-nutrient-delivered-by-each-ingredient) | $ND_{CP,i}^{call}$; $W_i^{call}$, $NCP_{CP,i}$ |
| `actual_protein` | Crude protein the ingredient actually supplied | lb | [4.5](2_formulas.md#45-nutrient-delivered-by-each-ingredient) | $ND_{CP,i}^{actual}$; $W_i^{actual}$, $NCP_{CP,i}$ |
| `protein_error_pct` | Ingredient-level crude protein delivery error | % | [4.6](2_formulas.md#46-ingredient-nutrient-error) | $E_{CP,i}$; $ND_{CP,i}^{actual}$, $ND_{CP,i}^{call}$ |
| `call_andfom` | Fiber the ingredient should have supplied | lb | [4.5](2_formulas.md#45-nutrient-delivered-by-each-ingredient) | $ND_{NDF,i}^{call}$; $W_i^{call}$, $NCP_{NDF,i}$ |
| `actual_andfom` | Fiber the ingredient actually supplied | lb | [4.5](2_formulas.md#45-nutrient-delivered-by-each-ingredient) | $ND_{NDF,i}^{actual}$; $W_i^{actual}$, $NCP_{NDF,i}$ |
| `andfom_error_pct` | Ingredient-level fiber delivery error | % | [4.6](2_formulas.md#46-ingredient-nutrient-error) | $E_{NDF,i}$; $ND_{NDF,i}^{actual}$, $ND_{NDF,i}^{call}$ |
| `call_starch` | Starch the ingredient should have supplied | lb | [4.5](2_formulas.md#45-nutrient-delivered-by-each-ingredient) | $ND_{starch,i}^{call}$; $W_i^{call}$, $NCP_{starch,i}$ |
| `actual_starch` | Starch the ingredient actually supplied | lb | [4.5](2_formulas.md#45-nutrient-delivered-by-each-ingredient) | $ND_{starch,i}^{actual}$; $W_i^{actual}$, $NCP_{starch,i}$ |
| `starch_error_pct` | Ingredient-level starch delivery error | % | [4.6](2_formulas.md#46-ingredient-nutrient-error) | $E_{starch,i}$; $ND_{starch,i}^{actual}$, $ND_{starch,i}^{call}$ |
| `nutrient_date` | Date of the nutrient analysis used | date | [S4.2](2_formulas.md#s42-latest-nutrient-analysis) | — |

## `chapter4_nutrient_error_by_formula` (thesis Table 4.5)

CSV file: `nutrient_error_by_formula.csv`. One row per formula: nutrient totals, concentrations and errors for the whole ration.

> Watch out: `call_protein`, `actual_protein` (and the fiber/starch versions) also exist in `chapter4_nutrient_delivery_by_ingredient`, but **here they are totals for the whole formula**, not per ingredient.

| Column | Meaning | Unit | Formula | Math terms |
|---|---|---|---|---|
| `feeding_date`, `recipe_display_name`, `pen_name` | Formula identifiers (`pen_name` only with `--group-by-pen`) | — | [S4.5](2_formulas.md#s45-formula-grouping) | — |
| `dry_call_weight_sum` | Batch call weight | lb DM | [4.1](2_formulas.md#41-batch-weight) | $BW^{call}$ |
| `dry_actual_weight_sum` | Batch actual weight | lb DM | [4.1](2_formulas.md#41-batch-weight) | $BW^{actual}$ |
| `call_protein` | Total crude protein the formula called for | lb | [4.7](2_formulas.md#47-formula-nutrient-total) | $ND_{CP}^{call}$; $ND_{CP,i}^{call}$ |
| `actual_protein` | Total crude protein actually delivered | lb | [4.7](2_formulas.md#47-formula-nutrient-total) | $ND_{CP}^{actual}$; $ND_{CP,i}^{actual}$ |
| `call_protein_pct_dm` | Crude protein concentration of the called ration | % DM | [4.8](2_formulas.md#48-formula-nutrient-concentration) | $C_{CP}^{call}$; $ND_{CP}^{call}$, $BW^{call}$ |
| `actual_protein_pct_dm` | Crude protein concentration of the delivered ration | % DM | [4.8](2_formulas.md#48-formula-nutrient-concentration) | $C_{CP}^{actual}$; $ND_{CP}^{actual}$, $BW^{actual}$ |
| `total_protein_error_pct` | Formula-level crude protein error | % | [4.9](2_formulas.md#49-formula-nutrient-error) | $E_{CP}$; $C_{CP}^{actual}$, $C_{CP}^{call}$ |
| `call_andfom` | Total fiber the formula called for | lb | [4.7](2_formulas.md#47-formula-nutrient-total) | $ND_{NDF}^{call}$; $ND_{NDF,i}^{call}$ |
| `actual_andfom` | Total fiber actually delivered | lb | [4.7](2_formulas.md#47-formula-nutrient-total) | $ND_{NDF}^{actual}$; $ND_{NDF,i}^{actual}$ |
| `call_andfom_pct_dm` | Fiber concentration of the called ration | % DM | [4.8](2_formulas.md#48-formula-nutrient-concentration) | $C_{NDF}^{call}$; $ND_{NDF}^{call}$, $BW^{call}$ |
| `actual_andfom_pct_dm` | Fiber concentration of the delivered ration | % DM | [4.8](2_formulas.md#48-formula-nutrient-concentration) | $C_{NDF}^{actual}$; $ND_{NDF}^{actual}$, $BW^{actual}$ |
| `total_andfom_error_pct` | Formula-level fiber error | % | [4.9](2_formulas.md#49-formula-nutrient-error) | $E_{NDF}$; $C_{NDF}^{actual}$, $C_{NDF}^{call}$ |
| `call_starch` | Total starch the formula called for | lb | [4.7](2_formulas.md#47-formula-nutrient-total) | $ND_{starch}^{call}$; $ND_{starch,i}^{call}$ |
| `actual_starch` | Total starch actually delivered | lb | [4.7](2_formulas.md#47-formula-nutrient-total) | $ND_{starch}^{actual}$; $ND_{starch,i}^{actual}$ |
| `call_starch_pct_dm` | Starch concentration of the called ration | % DM | [4.8](2_formulas.md#48-formula-nutrient-concentration) | $C_{starch}^{call}$; $ND_{starch}^{call}$, $BW^{call}$ |
| `actual_starch_pct_dm` | Starch concentration of the delivered ration | % DM | [4.8](2_formulas.md#48-formula-nutrient-concentration) | $C_{starch}^{actual}$; $ND_{starch}^{actual}$, $BW^{actual}$ |
| `total_starch_error_pct` | Formula-level starch error | % | [4.9](2_formulas.md#49-formula-nutrient-error) | $E_{starch}$; $C_{starch}^{actual}$, $C_{starch}^{call}$ |
