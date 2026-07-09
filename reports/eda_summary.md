# EDA Summary

This report analyzes `data/raw/application_train.csv` only. Raw data is read from disk and is not modified.

## Scope

- Rows analyzed: `307,511`
- Columns analyzed: `124` including EDA-only derived age and employment fields
- Sampling: no sampling used; full `application_train.csv` was analyzed.
- Modeling: no model training was performed.

## Top 5 Business Findings

1. The portfolio is highly imbalanced: 24,825 of 307,511 applications defaulted, a 8.07% default rate. Modeling should therefore emphasize ranking, recall, PR-AUC, calibration, and top-K capture instead of accuracy.
2. The highest observed categorical segment is OCCUPATION_TYPE = Low-skill Laborers, with a 17.15% default rate across 2,093 applications. This is a useful candidate for underwriting policy review and collections prioritization, not a standalone decision rule.
3. 25 columns have at least 50% missing values. Many are housing or building attributes, so missingness itself may carry applicant profile signal but must be handled carefully in feature engineering.
4. External score bands show strong risk separation: EXT_SOURCE_3 band (-0.000473, 0.33] has a 16.38% default rate, while EXT_SOURCE_1 band (0.71, 0.963] has 3.04%. These variables should be checked for availability, stability, and leakage risk before modeling.
5. Age bands differ materially: the riskiest age band is (20.499, 32.0] with a 11.28% default rate. This supports segment-level risk monitoring, while any model use must still be reviewed for fairness and policy constraints.

## Target Imbalance

| target | count | share_percent |
| --- | --- | --- |
| 0 | 282686 | 91.93 |
| 1 | 24825 | 8.07 |

## Missing Values

| column | missing_count | missing_percent | dtype |
| --- | --- | --- | --- |
| COMMONAREA_AVG | 214865 | 69.87 | float64 |
| COMMONAREA_MEDI | 214865 | 69.87 | float64 |
| COMMONAREA_MODE | 214865 | 69.87 | float64 |
| NONLIVINGAPARTMENTS_AVG | 213514 | 69.43 | float64 |
| NONLIVINGAPARTMENTS_MEDI | 213514 | 69.43 | float64 |
| NONLIVINGAPARTMENTS_MODE | 213514 | 69.43 | float64 |
| FONDKAPREMONT_MODE | 210295 | 68.39 | str |
| LIVINGAPARTMENTS_AVG | 210199 | 68.35 | float64 |
| LIVINGAPARTMENTS_MEDI | 210199 | 68.35 | float64 |
| LIVINGAPARTMENTS_MODE | 210199 | 68.35 | float64 |
| FLOORSMIN_AVG | 208642 | 67.85 | float64 |
| FLOORSMIN_MEDI | 208642 | 67.85 | float64 |
| FLOORSMIN_MODE | 208642 | 67.85 | float64 |
| YEARS_BUILD_AVG | 204488 | 66.5 | float64 |
| YEARS_BUILD_MEDI | 204488 | 66.5 | float64 |
| YEARS_BUILD_MODE | 204488 | 66.5 | float64 |
| OWN_CAR_AGE | 202929 | 65.99 | float64 |
| LANDAREA_AVG | 182590 | 59.38 | float64 |
| LANDAREA_MEDI | 182590 | 59.38 | float64 |
| LANDAREA_MODE | 182590 | 59.38 | float64 |
| BASEMENTAREA_AVG | 179943 | 58.52 | float64 |
| BASEMENTAREA_MEDI | 179943 | 58.52 | float64 |
| BASEMENTAREA_MODE | 179943 | 58.52 | float64 |
| EXT_SOURCE_1 | 173378 | 56.38 | float64 |
| NONLIVINGAREA_AVG | 169682 | 55.18 | float64 |

## Numerical Credit-Risk Features

| feature | non_null | missing_percent | mean | median | p25 | p75 |
| --- | --- | --- | --- | --- | --- | --- |
| AMT_INCOME_TOTAL | 307511 | 0.0 | 168797.92 | 147150.0 | 112500.0 | 202500.0 |
| AMT_CREDIT | 307511 | 0.0 | 599026.0 | 513531.0 | 270000.0 | 808650.0 |
| AMT_ANNUITY | 307499 | 0.0 | 27108.57 | 24903.0 | 16524.0 | 34596.0 |
| AGE_YEARS | 307511 | 0.0 | 43.91 | 43.1 | 34.0 | 53.9 |
| EMPLOYMENT_YEARS | 252137 | 18.01 | 6.53 | 4.5 | 2.1 | 8.7 |
| EXT_SOURCE_1 | 134133 | 56.38 | 0.5 | 0.51 | 0.33 | 0.68 |
| EXT_SOURCE_2 | 306851 | 0.21 | 0.51 | 0.57 | 0.39 | 0.66 |
| EXT_SOURCE_3 | 246546 | 19.83 | 0.51 | 0.54 | 0.37 | 0.67 |

## Categorical Business Features

| feature | unique_values | missing_percent | top_value | top_value_share_percent |
| --- | --- | --- | --- | --- |
| NAME_CONTRACT_TYPE | 2 | 0.0 | Cash loans | 90.48 |
| CODE_GENDER | 3 | 0.0 | F | 65.83 |
| NAME_EDUCATION_TYPE | 5 | 0.0 | Secondary / secondary special | 71.02 |
| NAME_FAMILY_STATUS | 6 | 0.0 | Married | 63.88 |
| NAME_HOUSING_TYPE | 6 | 0.0 | House / apartment | 88.73 |
| OCCUPATION_TYPE | 18 | 31.35 | Laborers | 26.14 |

## Highest Default Rates Across Categorical Segments

| feature | segment | count | default_rate_percent | portfolio_lift |
| --- | --- | --- | --- | --- |
| OCCUPATION_TYPE | Low-skill Laborers | 2093 | 17.15 | 2.12 |
| NAME_HOUSING_TYPE | Rented apartment | 4881 | 12.31 | 1.53 |
| NAME_HOUSING_TYPE | With parents | 14840 | 11.7 | 1.45 |
| OCCUPATION_TYPE | Drivers | 18603 | 11.33 | 1.4 |
| OCCUPATION_TYPE | Waiters/barmen staff | 1348 | 11.28 | 1.4 |
| NAME_EDUCATION_TYPE | Lower secondary | 3816 | 10.93 | 1.35 |
| OCCUPATION_TYPE | Security staff | 6721 | 10.74 | 1.33 |
| OCCUPATION_TYPE | Laborers | 55186 | 10.58 | 1.31 |
| OCCUPATION_TYPE | Cooking staff | 5946 | 10.44 | 1.29 |
| CODE_GENDER | M | 105059 | 10.14 | 1.26 |
| NAME_FAMILY_STATUS | Civil marriage | 29775 | 9.94 | 1.23 |
| NAME_FAMILY_STATUS | Single / not married | 45444 | 9.81 | 1.21 |
| OCCUPATION_TYPE | Sales staff | 32102 | 9.63 | 1.19 |
| OCCUPATION_TYPE | Cleaning staff | 4653 | 9.61 | 1.19 |
| NAME_EDUCATION_TYPE | Secondary / secondary special | 218391 | 8.94 | 1.11 |
| NAME_HOUSING_TYPE | Municipal apartment | 11183 | 8.54 | 1.06 |
| NAME_EDUCATION_TYPE | Incomplete higher | 10277 | 8.48 | 1.05 |
| NAME_CONTRACT_TYPE | Cash loans | 278232 | 8.35 | 1.03 |
| NAME_FAMILY_STATUS | Separated | 19770 | 8.19 | 1.02 |
| NAME_HOUSING_TYPE | Co-op apartment | 1122 | 7.93 | 0.98 |
| OCCUPATION_TYPE | Realty agents | 751 | 7.86 | 0.97 |
| NAME_HOUSING_TYPE | House / apartment | 272868 | 7.8 | 0.97 |
| NAME_FAMILY_STATUS | Married | 196432 | 7.56 | 0.94 |
| OCCUPATION_TYPE | Secretaries | 1305 | 7.05 | 0.87 |
| CODE_GENDER | F | 202448 | 7.0 | 0.87 |

## Highest Default Rates Across Numeric Quantile Bands

| feature | band | count | default_rate_percent | portfolio_lift |
| --- | --- | --- | --- | --- |
| EXT_SOURCE_3 | (-0.000473, 0.33] | 49445 | 16.38 | 2.03 |
| EXT_SOURCE_2 | (-0.0009999183, 0.34] | 61371 | 15.21 | 1.88 |
| EXT_SOURCE_1 | (0.013600000000000001, 0.296] | 26827 | 14.58 | 1.81 |
| AGE_YEARS | (20.499, 32.0] | 61773 | 11.28 | 1.4 |
| EMPLOYMENT_YEARS | (-0.001, 1.7] | 52250 | 11.23 | 1.39 |
| EMPLOYMENT_YEARS | (1.7, 3.4] | 49351 | 10.67 | 1.32 |
| AMT_CREDIT | (432000.0, 604152.0] | 61552 | 10.05 | 1.25 |
| AMT_ANNUITY | (28062.0, 37516.5] | 61452 | 9.34 | 1.16 |
| AGE_YEARS | (32.0, 39.5] | 61932 | 9.33 | 1.16 |
| AMT_CREDIT | (254700.0, 432000.0] | 58098 | 9.17 | 1.14 |
| EXT_SOURCE_2 | (0.34, 0.512] | 61371 | 9.16 | 1.13 |
| EMPLOYMENT_YEARS | (3.4, 5.9] | 50252 | 9.05 | 1.12 |
| AMT_ANNUITY | (21865.5, 28062.0] | 61562 | 8.79 | 1.09 |
| EXT_SOURCE_3 | (0.33, 0.476] | 49746 | 8.75 | 1.08 |
| EXT_SOURCE_1 | (0.296, 0.438] | 26826 | 8.74 | 1.08 |
| AMT_INCOME_TOTAL | (135000.0, 162000.0] | 35453 | 8.68 | 1.08 |
| AMT_INCOME_TOTAL | (99000.0, 135000.0] | 85756 | 8.59 | 1.06 |
| AMT_ANNUITY | (14701.5, 21865.5] | 61494 | 8.58 | 1.06 |
| AMT_INCOME_TOTAL | (25649.999, 99000.0] | 63671 | 8.21 | 1.02 |
| AMT_INCOME_TOTAL | (162000.0, 225000.0] | 75513 | 8.06 | 1.0 |

## Figures

- `reports/figures/target_imbalance.png`
- `reports/figures/top_missing_values.png`
- `reports/figures/categorical_segment_default_rates.png`
- `reports/figures/external_score_default_rates.png`

## Business Interpretation

This EDA is intended to guide later feature engineering and validation. Segments with higher default rates are risk signals for monitoring and prioritization, but they should not be used as hard policy rules without fairness, stability, and leakage review. Missingness patterns should be treated as a feature-engineering question rather than cleaned away mechanically.
