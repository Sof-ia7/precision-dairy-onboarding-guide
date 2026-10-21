# 2. Formula dictionary

Every **calculation step** of the pipeline: what it calculates, what goes in, and where the result ends up. The formula itself never appears in a table; only its result does.

Part of a set of three dictionaries:

| Dictionary | What it answers |
|---|---|
| [1. Tables](1_tables.md) | What does this column mean, and where does it come from? |
| **2. Formulas** (this file) | What does each calculation step produce? |
| [3. Math terms](3_math_terms.md) | What does each symbol in the equations mean? |

## How formulas are numbered

| Label | Meaning |
|---|---|
| **3.x**, **4.x** | Equation number in the thesis (Chapter 3 or 4) |
| **P4.x** | Added by the pipeline; not a numbered thesis equation |
| **S3.x**, **S4.x** | Internal step: a rule applied behind the scenes. Its result is not a column of its own, but it shapes other columns |

Each formula lists:
- **Gives**: what the result means.
- **Inputs**: the [math terms](3_math_terms.md) it uses.
- **Result in**: the table column(s) that hold the result ([1. Tables](1_tables.md)).
- **Code**: the function that does it.

---

# Chapter 3: Herd characteristics

Chapter 3 uses one general set of statistics (3.2 to 3.5) and applies it to different metrics $M$ (milk yield, DIM, body weight) and analytical units $u$ (group-day, group-month, cow). Equation 3.1 only defines $M \in \{Y, DIM, W\}$; see [3. Math terms](3_math_terms.md#chapter-3-symbols).

## General statistics

### 3.2 Mean

$$\bar{M}_u = \frac{1}{n_u}\sum_{r=1}^{n_u} M_{r,u}$$

- **Gives**: the average of metric $M$ in unit $u$.
- **Inputs**: $M_{r,u}$, $n_u$.
- **Result in**: every `Avg ...` column of Chapter 3.
- **Code**: pandas `mean` inside each `summarize_*` function in `src/chapter3_herd_pipeline.py`.

### 3.3 Sample standard deviation

$$s_{M,u} = \sqrt{\frac{\sum_{r=1}^{n_u}\left(M_{r,u} - \bar{M}_u\right)^2}{n_u - 1}}$$

- **Gives**: how spread out the observations are around the mean (divides by $n_u - 1$).
- **Inputs**: $M_{r,u}$, $\bar{M}_u$, $n_u$.
- **Result in**: `Yield STD` (`yield_std`), `Weight STD` (`weight_std`).
- **Code**: `x.std(ddof=1)`. Blank when there is only 1 observation.

### 3.4 Standard error

$$SE_{M,u} = \frac{s_{M,u}}{\sqrt{n_u}}$$

- **Gives**: how precise the mean is.
- **Inputs**: $s_{M,u}$, $n_u$.
- **Result in**: `SE` (`se`) in every Chapter 3 summary table.
- **Code**: `std / np.sqrt(n)` in each `summarize_*` function.

### 3.5 Confidence interval

$$CI_{M,u} = \bar{M}_u \pm t_{1-\alpha/2,\;n_u-1}\cdot SE_{M,u}$$

- **Gives**: the range that contains the true mean with 80 % confidence ($\alpha = 0.20$).
- **Inputs**: $\bar{M}_u$, $t_{1-\alpha/2,\,n_u-1}$, $SE_{M,u}$, $\alpha$, $n_u$.
- **Result in**: `T Value`, `CI Lower`, `CI Upper` (`t_value`, `ci_lower`, `ci_upper`) in `chapter3_yield_group_day` and `chapter3_yield_group_month`. Not computed for body weight.
- **Code**: `add_t_confidence_interval` and `safe_t_value`. Only when $n_u \ge 2$ ([S3.6](#s36-t-value-only-with-2-or-more-observations)).

## Applications

### 3.6 Daily group mean

$$\bar{M}_{g,d} = \frac{1}{n_{g,d}}\sum_{r=1}^{n_{g,d}} M_{r,g,d}, \quad M \in \{Y, DIM\}$$

- **Gives**: the mean milk yield and mean DIM of each group on each day. Equations 3.3–3.5 then give its STD, SE and CI (for yield only).
- **Inputs**: $Y_{r,g,d}$, $DIM_{r,g,d}$, $n_{g,d}$, unit $u = (g,d)$.
- **Result in**: `Avg Daily Yield`, `Avg DIM`, and through 3.3–3.5 `Yield STD`, `SE`, `T Value`, `CI Lower`, `CI Upper` of `chapter3_yield_group_day`.
- **Code**: `summarize_yield_group_day`.

### 3.7 Cow-month mean yield

$$\bar{Y}_{r,g,m} = \frac{1}{D_{r,g,m}}\sum_{d=1}^{D_{r,g,m}} Y_{r,g,d}$$

- **Gives**: the average daily milk yield of one cow in one group during one month. This is the first of two stages; it makes each cow count once in the monthly group summary.
- **Inputs**: $Y_{r,g,d}$, $D_{r,g,m}$.
- **Result in**: `Avg Monthly Yield` of `chapter3_animal_month_yield`. It is then the input $M$ of 3.2–3.5 for `chapter3_yield_group_month`.
- **Code**: `summarize_animal_month_yield`, then `summarize_yield_group_month`.

### 3.8 Group-month mean body weight

$$\bar{W}_{g,m} = \frac{1}{n_{g,m}}\sum_{r=1}^{n_{g,m}} W_{r,g,m}$$

- **Gives**: the average body weight of each group in each month. Equations 3.3–3.4 then give its STD and SE.
- **Inputs**: $W_{r,g,m}$ (from [S3.3](#s33-cow-month-body-weight)), $n_{g,m}$.
- **Result in**: `Avg Weight`, `Weight STD`, `SE` of `chapter3_weight_group`.
- **Code**: `summarize_weight_group`.

### 3.9 Per-cow mean daily yield

$$\bar{Y}_r = \frac{1}{D_r}\sum_{d=1}^{D_r} Y_{r,d}$$

- **Gives**: the average daily milk yield of one cow over the whole period. 3.3 and 3.4 give its STD and SE with $n_u$ replaced by $D_r$.
- **Inputs**: $Y_{r,d}$, $D_r$.
- **Result in**: `Avg Daily Yield`, `Yield STD`, `SE` of `chapter3_yield_per_cow`.
- **Code**: `summarize_per_cow_daily_yield`.

### 3.10 Per-cow confidence interval

$$CI_{Y,r} = \bar{Y}_r \pm t_{1-\alpha/2,\;D_r-1}\cdot\frac{s_{Y,r}}{\sqrt{D_r}}$$

- **Gives**: the 80 % confidence interval of the cow's mean daily yield.
- **Inputs**: $\bar{Y}_r$, $s_{Y,r}$, $D_r$, $t_{1-\alpha/2,\,D_r-1}$, $\alpha$.
- **Result in**: `T Value`, `CI Lower`, `CI Upper` of `chapter3_yield_per_cow`.
- **Code**: `summarize_per_cow_daily_yield` via `add_t_confidence_interval`.

## Internal steps (Chapter 3)

### S3.1 Daily milk yield

If the Afimilk file has a daily-yield column it is used as is. Otherwise:

$$Y_{r,g,d} = Y_{s1} + Y_{s2}$$

- A missing session counts as 0.
- **Shapes**: `Yield` in `chapter3_yield_and_dim`, and every yield statistic after it.
- **Code**: `standardize_afi_daily`.

### S3.2 Group label mapping

Text group labels are turned into numbers: `pack` → 15, `G1` → 1, `G2` → 2, `G3` → 3, `G4` → 4. Other values are read as numbers.

- **Shapes**: every `Grp` / `Group` column, and therefore every group summary.
- **Code**: `clean_group_series`, `DEFAULT_GROUP_MAPPING`.

### S3.3 Cow-month body weight

$$W_{r,g,m} = \text{mean of all weighings of cow } r \text{ in month } m$$

- If a cow was weighed more than once in a month, the weights are averaged; the latest weighing date is kept.
- Daily weights are **not** interpolated; the monthly weight is repeated on each day in `chapter3_dim_weights_merged`.
- **Shapes**: `Weight` in `chapter3_dim_weights_merged` and `chapter3_cow_month_weight`, and the inputs of 3.8.
- **Code**: `load_weights_csv`.

### S3.4 Cow-month group

The group of a cow in a month is its **most frequent** Afimilk group that month. If Afimilk has none, the group from the weight file is used.

- **Shapes**: `Group` in `chapter3_cow_month_weight` and `chapter3_weight_group`.
- **Code**: `cow_month_group_from_afi`, `merge_dim_weights`.

### S3.5 Per-cow daily records

Before the per-cow summary, duplicate records for the same cow and day are averaged into one. The cow's group is its most frequent group over the period.

- **Shapes**: `N Days`, `Group` and all statistics of `chapter3_yield_per_cow`.
- **Code**: `summarize_per_cow_daily_yield`.

### S3.6 t value only with 2 or more observations

$$t = t_{1-\alpha/2,\;n-1} \text{ only if } n \ge 2, \text{ otherwise blank}$$

- With one observation there is no spread, so no confidence interval.
- **Shapes**: `T Value`, `CI Lower`, `CI Upper`.
- **Code**: `safe_t_value`.

### S3.7 Dates, year and month

The observation day comes from the file's date column, or from the date in the file name (`YYYYMMDD` or `YYYY-MM-DD`). Year, month number and month name are taken from that day. Records before the start date (`CH3_START_DATE`) are removed.

- **Shapes**: `Date`, `Day`, `File Date`, `Year`, `Month`, `Month Num`.
- **Code**: `parse_date_from_filename`, `standardize_afi_daily`.

---

# Chapter 4: Feed traits

All Chapter 4 formulas are calculated **per formula** (one recipe on one feeding day, see [S4.5](#s45-formula-grouping)) and on a **dry matter** basis. $k \in \{call, actual\}$: each formula with $k$ is calculated twice, once with the called weights and once with the actual weights.

## Weight accuracy

### 4.1 Batch weight

$$BW^k = \sum_{i=1}^{n} W_i^k$$

- **Gives**: the total dry weight of the formula, called and actual.
- **Inputs**: $W_i^k$, $n$, $k$.
- **Result in**: `dry_call_weight_sum`, `dry_actual_weight_sum` (in `chapter4_filtered_feed_intake`, `chapter4_dry_weight_participation`, `chapter4_error_by_weight`, `chapter4_nutrient_error_by_formula`).
- **Code**: `prepare_feed_intake_data`, `calculate_error_by_weight`. A missing ingredient weight is skipped in the sum.

### 4.2 Ingredient share (participation)

$$W_{\%,i}^k = \frac{W_i^k}{BW^k}\times 100$$

- **Gives**: each ingredient's percentage of the formula's dry weight, called and actual.
- **Inputs**: $W_i^k$, $BW^k$.
- **Result in**: `call_pct_participation`, `actual_pct_participation`, `pct_participation`.
- **Code**: `prepare_feed_intake_data`.

### 4.3 Ingredient weight error (participation-based)

$$E_{W,i} = \frac{W_{\%,i}^{actual} - W_{\%,i}^{call}}{W_{\%,i}^{call}}\times 100$$

- **Gives**: how far the ingredient's share of the mix was from its target, as a percentage of the target share.
- **Inputs**: $W_{\%,i}^{actual}$, $W_{\%,i}^{call}$.
- **Result in**: `participation_difference_pct` in `chapter4_weight_difference_ing`.
- **Code**: `calculate_weight_difference_ing`.
- **Note**: this is the equation as written in the thesis. The thesis tables report [P4.1](#p41-direct-ingredient-weight-error) instead.

### P4.1 Direct ingredient weight error

$$E_{W,i}^{direct} = \frac{W_i^{actual} - W_i^{call}}{W_i^{call}}\times 100$$

- **Gives**: how far the ingredient's loaded weight was from its called weight, as a percentage of the called weight.
- **Inputs**: $W_i^{actual}$, $W_i^{call}$.
- **Result in**: `weight_difference_pct` in `chapter4_weight_difference_ing`.
- **Code**: `calculate_weight_difference_ing`.

### 4.4 Batch weight error

$$E_{BW} = \frac{BW^{actual} - BW^{call}}{BW^{call}}\times 100$$

- **Gives**: how far the whole formula's weight was from its target.
- **Inputs**: $BW^{actual}$, $BW^{call}$.
- **Result in**: `error_by_weight_pct` in `chapter4_error_by_weight`.
- **Code**: `calculate_error_by_weight`.

### P4.2 Intake

$$I = BW^{actual} - R$$

- **Gives**: the dry feed the group actually ate: what was delivered minus what was refused.
- **Inputs**: $BW^{actual}$, $R$ (from [S4.4](#s44-refusals-per-formula)).
- **Result in**: `intake` in `chapter4_error_by_weight`. Blank when the formula has no refusals record, or while refusals are not configured.
- **Code**: `add_intake`.

## Nutrient accuracy

$j \in \{CP, NDF, starch\}$: each formula with $j$ is calculated once per nutrient (crude protein, fiber, starch).

### 4.5 Nutrient delivered by each ingredient

$$ND_{j,i}^k = W_i^k \times \frac{NCP_{j,i}}{100}$$

- **Gives**: the pounds of nutrient $j$ supplied by ingredient $i$, called and actual.
- **Inputs**: $W_i^k$, $NCP_{j,i}$ (from [S4.2](#s42-latest-nutrient-analysis)).
- **Result in**: `call_protein`, `actual_protein`, `call_andfom`, `actual_andfom`, `call_starch`, `actual_starch` in `chapter4_nutrient_delivery_by_ingredient`.
- **Code**: `calculate_nutrient_delivery_by_ingredient`. Blank if the ingredient is missing from the nutrient table.

### 4.6 Ingredient nutrient error

$$E_{j,i} = \frac{ND_{j,i}^{actual} - ND_{j,i}^{call}}{ND_{j,i}^{call}}\times 100$$

- **Gives**: how far the nutrient supplied by one ingredient was from its target.
- **Inputs**: $ND_{j,i}^{actual}$, $ND_{j,i}^{call}$.
- **Result in**: `protein_error_pct`, `andfom_error_pct`, `starch_error_pct` in `chapter4_nutrient_delivery_by_ingredient`.
- **Code**: `calculate_nutrient_delivery_by_ingredient`.
- **Note**: because $NCP_{j,i}$ is the same in both terms it cancels, so $E_{j,i}$ equals [P4.1](#p41-direct-ingredient-weight-error) for every nutrient. It is blank when the ingredient has 0 % of that nutrient (division by zero).

### 4.7 Formula nutrient total

$$ND_j^k = \sum_{i=1}^{n} ND_{j,i}^k$$

- **Gives**: the total pounds of nutrient $j$ in the whole formula, called and actual.
- **Inputs**: $ND_{j,i}^k$, $n$.
- **Result in**: `call_protein`, `actual_protein`, `call_andfom`, `actual_andfom`, `call_starch`, `actual_starch` in `chapter4_nutrient_error_by_formula` (same names as 4.5, but totals).
- **Code**: `calculate_nutrient_error_by_formula`. Ingredients without nutrient values are skipped in the sum.

### 4.8 Formula nutrient concentration

$$C_j^k = \frac{ND_j^k}{\sum_{i=1}^{n} W_i^k}\times 100 = \frac{ND_j^k}{BW^k}\times 100$$

- **Gives**: the percentage of nutrient $j$ in the dry matter of the whole ration, called and actual.
- **Inputs**: $ND_j^k$, $BW^k$ (= $\sum W_i^k$).
- **Result in**: `call_protein_pct_dm`, `actual_protein_pct_dm`, `call_andfom_pct_dm`, `actual_andfom_pct_dm`, `call_starch_pct_dm`, `actual_starch_pct_dm`.
- **Code**: `calculate_nutrient_error_by_formula`.
- **Note**: $BW^k$ includes every ingredient, also those missing from the nutrient table, so a missing ingredient makes the concentration lower than it really is.

### 4.9 Formula nutrient error

$$E_j = \frac{C_j^{actual} - C_j^{call}}{C_j^{call}}\times 100$$

- **Gives**: how far the nutrient content of the delivered ration was from the formulated ration.
- **Inputs**: $C_j^{actual}$, $C_j^{call}$.
- **Result in**: `total_protein_error_pct`, `total_andfom_error_pct`, `total_starch_error_pct`.
- **Code**: `calculate_nutrient_error_by_formula`.

## Internal steps (Chapter 4)

### S4.1 Ingredient code standardization

Each TMR Tracker ingredient name is turned into a short code so it can be matched to the nutrient table. In order:
1. a farm-specific mapping file, if given (`CH4_INGREDIENT_MAP`);
2. fixed phrases (`CORN SILAGE` → CSL, `SOYBEAN MEAL` → SBM, `SOY HULL` → SOY, ...);
3. otherwise the first three letters of the name.

- **Shapes**: `ingredient_code`, and which nutrient values each ingredient gets in 4.5.
- **Code**: `standardize_ingredient_code`, `DEFAULT_INGREDIENT_CODE_RULES`.

### S4.2 Latest nutrient analysis

The nutrient table keeps old lab analyses as history. For each ingredient code only the **most recent** row is used. Ingredients missing from the table get blank nutrient values; they are not dropped or filled.

- **Shapes**: `protein_pct`, `andfom_pct`, `starch_pct`, `nutrient_date`, and every nutrient formula (4.5–4.9).
- **Code**: `prepare_nutrient_table`.

### S4.3 Safe division

Every percentage formula (4.2, 4.3, P4.1, 4.4, 4.6, 4.8, 4.9) returns **blank** instead of an error when the bottom of the fraction is 0 or missing.

- **Code**: `safe_percent`.

### S4.4 Refusals per formula

$$R = \sum_{\text{pens}} \text{refused dry weight}$$

Refusals are read per feeding date, recipe and pen. Without `--group-by-pen` the pens of the same recipe and day are added together, to match how $BW^{actual}$ is grouped. With `--group-by-pen` each pen keeps its own value.

- **Shapes**: `refusals`, and `intake` through P4.2.
- **Code**: `load_refusals_data`, `add_intake`. Not active until the refusals path and column are set (see `HANDOFF.md`, "Adding feed refusals").

### S4.5 Formula grouping

All "per formula" values are grouped by **feeding date + recipe**. With `--group-by-pen` the pen is added: **feeding date + recipe + pen**. Several batches of the same recipe on the same day are combined.

- **Shapes**: every sum and formula-level value (4.1, 4.4, 4.7–4.9, P4.2).
- **Code**: `get_formula_group_columns`.

### S4.6 Dates

Feeding dates are read as normal dates or as Excel date numbers. Rows outside `CH4_START_DATE` / `CH4_END_DATE` are removed. Rows missing the date, recipe or ingredient, or missing both dry weights, are dropped.

- **Shapes**: `feeding_date` and which rows enter every formula.
- **Code**: `clean_date`, `prepare_feed_intake_data`.
