# Baseline Modeling Summary

This report contains actual computed baseline model results from `data/processed/model_features.parquet`.

## Scope

- Full processed feature dataset used.
- Rows loaded: `307,511`
- Feature columns: `76`
- Default rate: `8.07%`
- Split strategy: stratified 60% train, 20% validation, 20% test.
- Imbalance handling: balanced class weights for Logistic Regression and Random Forest; `scale_pos_weight` for XGBoost and LightGBM.
- Accuracy is intentionally not used as the primary metric.

## Current Best Baseline

`lightgbm` is the current best baseline by validation PR-AUC (`0.2692`), with validation ROC-AUC `0.7793`, Recall@Top-10% `0.3684`, and KS `0.4179`.

PR-AUC is used for model selection because the default class is rare and the business problem is closer to ranking risky applicants than maximizing overall classification accuracy.

## Model Comparison

| model | split | roc_auc | pr_auc | precision | recall | f1_score | recall_at_top_10pct | ks_statistic | tn | fp | fn | tp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lightgbm | test | 0.775 | 0.2608 | 0.1811 | 0.6745 | 0.2855 | 0.3547 | 0.4108 | 41391 | 15147 | 1616 | 3349 |
| xgboost | test | 0.7722 | 0.2585 | 0.1779 | 0.6792 | 0.2819 | 0.3478 | 0.4086 | 40955 | 15583 | 1593 | 3372 |
| random_forest | test | 0.7524 | 0.2317 | 0.1778 | 0.6175 | 0.2762 | 0.3237 | 0.3739 | 42364 | 14174 | 1899 | 3066 |
| logistic_regression | test | 0.7549 | 0.2303 | 0.165 | 0.6864 | 0.266 | 0.3291 | 0.3846 | 39286 | 17252 | 1557 | 3408 |
| lightgbm | validation | 0.7793 | 0.2692 | 0.1826 | 0.6828 | 0.2881 | 0.3684 | 0.4179 | 41357 | 15180 | 1575 | 3390 |
| xgboost | validation | 0.7764 | 0.2665 | 0.1794 | 0.687 | 0.2845 | 0.3613 | 0.4133 | 40930 | 15607 | 1554 | 3411 |
| logistic_regression | validation | 0.7595 | 0.2467 | 0.1663 | 0.6931 | 0.2682 | 0.3333 | 0.3904 | 39284 | 17253 | 1524 | 3441 |
| random_forest | validation | 0.7574 | 0.2388 | 0.1806 | 0.6292 | 0.2806 | 0.3364 | 0.3883 | 42362 | 14175 | 1841 | 3124 |

## Saved Artifacts

- `reports/model_comparison.csv`
- `models/logistic_regression.joblib`
- `models/random_forest.joblib`
- `models/xgboost.joblib` if XGBoost is installed
- `models/lightgbm.joblib` if LightGBM is installed
- `models/baseline_metadata.json`
