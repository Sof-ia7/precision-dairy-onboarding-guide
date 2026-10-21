# 3. Math terms dictionary

Every **symbol** used in the equations of [2. Formulas](2_formulas.md): what it means, its unit, and which formulas use it.

Part of a set of three dictionaries:

| Dictionary | What it answers |
|---|---|
| [1. Tables](1_tables.md) | What does this column mean, and where does it come from? |
| [2. Formulas](2_formulas.md) | What does each calculation step produce? |
| **3. Math terms** (this file) | What does each symbol in the equations mean? |

## How to read this file

- **Kind**: *index* (a counter: which cow, which day, ...), *set* (a list of options), *value* (a number from the data), *result* (a number calculated by a formula), *constant* (fixed setting).
- **Table column**: where the value can be seen, if anywhere. `—` means it only exists inside the math.
- **Superscripts and subscripts** say *which* one: $W_i^{call}$ is "the called weight ($call$) of ingredient $i$".

> **Same letter, different meaning.** $W$ is **body weight** in Chapter 3 but **ingredient dry weight** in Chapter 4. $n$ is a **number of observations** in Chapter 3 but the **number of ingredients** in Chapter 4. Always read the symbol together with its chapter.

---

# Chapter 3 symbols

## Indexes, sets and constants

| Symbol | Name | Kind | Meaning | Unit | Used in | Table column |
|---|---|---|---|---|---|---|
| $M$ | Metric | set | The herd metric being summarized: $M \in \{Y, DIM, W\}$ (thesis Eq. 3.1) | — | 3.2–3.6 | — |
| $Y$ | Milk yield | set member | Milk yield as a metric | lb/day | 3.1, 3.6, 3.7, 3.9, 3.10 | — |
| $DIM$ | Days in milk | set member | Days since the cow's last calving | days | 3.1, 3.6 | — |
| $W$ | Body weight | set member | Body weight as a metric (Chapter 3 only) | lb | 3.1, 3.8 | — |
| $u$ | Analytical unit | index | The group of records a statistic is calculated over: $u = (g,d)$ group-day, $u = (g,m)$ group-month, $u = r$ one cow | — | 3.2–3.5 | — |
| $r$ | Cow (record) | index | One cow, or one record of a cow | — | all | `farm_animal_id` |
| $g$ | Group | index | Group (pen group) of the cow | — | 3.6–3.8 | `group`, `grp` |
| $d$ | Day | index | Observation day | date | 3.6, 3.7, 3.9 | `day`, `date`, `file_date` |
| $m$ | Month | index | Calendar month | — | 3.7, 3.8 | `year`, `month`, `month_num` |
| $\alpha$ | Significance level | constant | $1 -$ confidence level. $\alpha = 0.20$ for 80 % confidence (`CH3_CONFIDENCE_LEVEL`) | — | 3.5, 3.10 | — |

## Counts

| Symbol | Name | Kind | Meaning | Unit | Used in | Table column |
|---|---|---|---|---|---|---|
| $n_u$ | Number of observations | value | Valid observations in unit $u$ | count | 3.2–3.5 | `n_animals` |
| $n_{g,d}$ | Animals per group-day | value | Different cows in group $g$ on day $d$ | cows | 3.6 | `n_animals` (`chapter3_yield_group_day`) |
| $n_{g,m}$ | Animals per group-month | value | Different cows in group $g$ in month $m$ | cows | 3.8, 3.2–3.5 | `n_animals` (`chapter3_yield_group_month`, `chapter3_weight_group`) |
| $D_{r,g,m}$ | Days per cow-month | value | Days with a valid yield record for cow $r$ in group $g$ in month $m$ | days | 3.7 | `n_days` (`chapter3_animal_month_yield`) |
| $D_r$ | Days per cow | value | Days with a valid yield record for cow $r$ over the whole period | days | 3.9, 3.10 | `n_days` (`chapter3_yield_per_cow`) |

## Observations (from the data)

| Symbol | Name | Kind | Meaning | Unit | Used in | Table column |
|---|---|---|---|---|---|---|
| $M_{r,u}$ | Observation | value | One value of metric $M$ for cow/record $r$ in unit $u$ | unit of $M$ | 3.2, 3.3 | — |
| $Y_{r,g,d}$ | Daily milk yield | value | Milk yield of cow $r$ in group $g$ on day $d$ | lb/day | 3.6, 3.7 | `yield` |
| $Y_{s1}$, $Y_{s2}$ | Session yield | value | Milk yield of milking session 1 and 2, when no daily total is given | lb | S3.1 | — |
| $DIM_{r,g,d}$ | Daily DIM | value | Days in milk of cow $r$ in group $g$ on day $d$ | days | 3.6 | `dim` |
| $Y_{r,d}$ | Cow daily yield | value | Milk yield of cow $r$ on day $d$ (duplicates averaged) | lb/day | 3.9 | — |
| $W_{r,g,m}$ | Cow-month body weight | value | Body weight of cow $r$ in group $g$ in month $m$ (mean of that month's weighings) | lb | 3.8 | `weight` |

## Results (calculated)

| Symbol | Name | Kind | Meaning | Unit | Created by | Table column |
|---|---|---|---|---|---|---|
| $\bar{M}_u$ | Mean | result | Average of $M$ in unit $u$ | unit of $M$ | 3.2 | `avg_*` columns |
| $\bar{M}_{g,d}$ | Daily group mean | result | Mean yield or DIM of group $g$ on day $d$ | lb/day or days | 3.6 | `avg_daily_yield`, `avg_dim` |
| $s_{M,u}$ | Sample standard deviation | result | Spread of $M$ around its mean in unit $u$ | unit of $M$ | 3.3 | `yield_std`, `weight_std` |
| $SE_{M,u}$ | Standard error | result | Precision of the mean | unit of $M$ | 3.4 | `se` |
| $t_{1-\alpha/2,\,n_u-1}$ | t critical value | result | Student's t value for $n_u - 1$ degrees of freedom | — | 3.5, S3.6 | `t_value` |
| $CI_{M,u}$ | Confidence interval | result | Range around the mean: lower and upper limit | unit of $M$ | 3.5 | `ci_lower`, `ci_upper` |
| $\bar{Y}_{r,g,m}$ | Cow-month mean yield | result | Average daily yield of cow $r$ in group $g$ in month $m$ | lb/day | 3.7 | `avg_monthly_yield` (`chapter3_animal_month_yield`) |
| $\bar{W}_{g,m}$ | Group-month mean weight | result | Average body weight of group $g$ in month $m$ | lb | 3.8 | `avg_weight` |
| $\bar{Y}_r$ | Per-cow mean yield | result | Average daily yield of cow $r$ over the period | lb/day | 3.9 | `avg_daily_yield` (`chapter3_yield_per_cow`) |
| $s_{Y,r}$ | Per-cow yield standard deviation | result | Spread of cow $r$'s daily yields | lb/day | 3.3 with $n_u = D_r$ | `yield_std` (`chapter3_yield_per_cow`) |
| $CI_{Y,r}$ | Per-cow confidence interval | result | Range around cow $r$'s mean daily yield | lb/day | 3.10 | `ci_lower`, `ci_upper` (`chapter3_yield_per_cow`) |

---

# Chapter 4 symbols

All weights are **dry matter**.

## Indexes, sets and counts

| Symbol | Name | Kind | Meaning | Unit | Used in | Table column |
|---|---|---|---|---|---|---|
| $i$ | Ingredient | index | One ingredient of the formula (identified by its code) | — | 4.1–4.9, P4.1 | `ingredient_code` |
| $n$ | Number of ingredients | value | Ingredients in the formula (Chapter 4 only) | count | 4.1, 4.7, 4.8 | — |
| $k$ | Scenario | set | Which weight is used: $k \in \{call, actual\}$ | — | 4.1, 4.2, 4.5, 4.7, 4.8 | prefix `call_` / `actual_`, or `dry_call_` / `dry_actual_` |
| $call$ | Called | set member | The weight the nutritionist's recipe asked for (target) | — | all | `call_*`, `dry_call_*` |
| $actual$ | Actual | set member | The weight actually loaded and delivered | — | all | `actual_*`, `dry_actual_*` |
| $j$ | Nutrient | set | Nutritional trait: $j \in \{CP, NDF, starch\}$ | — | 4.5–4.9 | `protein`, `andfom`, `starch` in column names |
| $CP$ | Crude protein | set member | Crude protein | — | 4.5–4.9 | `*protein*` |
| $NDF$ | Neutral detergent fiber | set member | Fiber. The code calls it **aNDFom** (`andfom`); the thesis calls it NDF | — | 4.5–4.9 | `*andfom*` |
| $starch$ | Starch | set member | Starch | — | 4.5–4.9 | `*starch*` |

## Values (from the data)

| Symbol | Name | Kind | Meaning | Unit | Used in | Table column |
|---|---|---|---|---|---|---|
| $W_i^k$ | Ingredient dry weight | value | Dry weight of ingredient $i$ under scenario $k$ (Chapter 4 only) | lb DM | 4.1, 4.2, 4.5, 4.8, P4.1 | `dry_call_weight`, `dry_actual_weight` |
| $NCP_{j,i}$ | Nutrient content percentage | value | Percentage of nutrient $j$ in ingredient $i$, from the latest lab analysis | % DM | 4.5 | `protein_pct`, `andfom_pct`, `starch_pct` |
| $R$ | Refusals | value | Dry feed refused (weighback) for the formula; added by this pipeline, not in the thesis | lb DM | P4.2, S4.4 | `refusals` |

## Results (calculated)

| Symbol | Name | Kind | Meaning | Unit | Created by | Table column |
|---|---|---|---|---|---|---|
| $BW^k$ | Batch weight | result | Total dry weight of the formula under scenario $k$ | lb DM | 4.1 | `dry_call_weight_sum`, `dry_actual_weight_sum` |
| $W_{\%,i}^k$ | Ingredient share | result | Ingredient $i$'s percentage of the batch under scenario $k$ | % DM | 4.2 | `call_pct_participation`, `actual_pct_participation`, `pct_participation` |
| $E_{W,i}$ | Ingredient weight error (share) | result | Relative difference between actual and called share of ingredient $i$ | % | 4.3 | `participation_difference_pct` |
| $E_{W,i}^{direct}$ | Ingredient weight error (direct) | result | Relative difference between actual and called weight of ingredient $i$ | % | P4.1 | `weight_difference_pct` |
| $E_{BW}$ | Batch weight error | result | Relative difference between actual and called batch weight | % | 4.4 | `error_by_weight_pct` |
| $I$ | Intake | result | Dry feed actually eaten: $BW^{actual} - R$; added by this pipeline | lb DM | P4.2 | `intake` |
| $ND_{j,i}^k$ | Ingredient nutrient delivery | result | Pounds of nutrient $j$ supplied by ingredient $i$ under scenario $k$ | lb | 4.5 | `call_protein`, `actual_protein`, ... (`chapter4_nutrient_delivery_by_ingredient`) |
| $E_{j,i}$ | Ingredient nutrient error | result | Relative difference between actual and called nutrient supplied by ingredient $i$ | % | 4.6 | `protein_error_pct`, `andfom_error_pct`, `starch_error_pct` |
| $ND_j^k$ | Formula nutrient total | result | Total pounds of nutrient $j$ in the formula under scenario $k$ | lb | 4.7 | `call_protein`, `actual_protein`, ... (`chapter4_nutrient_error_by_formula`) |
| $C_j^k$ | Formula nutrient concentration | result | Percentage of nutrient $j$ in the ration's dry matter under scenario $k$ | % DM | 4.8 | `call_protein_pct_dm`, `actual_protein_pct_dm`, ... |
| $E_j$ | Formula nutrient error | result | Relative difference between actual and called concentration of nutrient $j$ | % | 4.9 | `total_protein_error_pct`, `total_andfom_error_pct`, `total_starch_error_pct` |
