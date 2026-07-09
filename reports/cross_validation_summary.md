# Cross-Validation Summary

This report evaluates the final tuned LightGBM configuration with stratified K-fold validation. It is a stability check around the selected champion model, not a new model-selection exercise.

## Scope

- Rows used: `307,511`
- Feature columns: `76`
- Folds: `5`
- Top-K policy: top `10%` of validation scores per fold
- Sample size: full processed dataset

## Stability Summary

| metric | mean | std | min | max |
| --- | --- | --- | --- | --- |
| roc_auc | 0.783 | 0.0044 | 0.7782 | 0.7893 |
| pr_auc | 0.2745 | 0.0074 | 0.2651 | 0.2854 |
| precision | 0.2943 | 0.006 | 0.2887 | 0.3045 |
| recall | 0.3646 | 0.0074 | 0.3577 | 0.3772 |
| f1_score | 0.3257 | 0.0067 | 0.3195 | 0.337 |
| recall_at_top_10pct | 0.3646 | 0.0074 | 0.3577 | 0.3772 |
| ks_statistic | 0.4276 | 0.0104 | 0.4146 | 0.4419 |

## Fold-Level Results

| fold | validation_rows | validation_default_rate | roc_auc | pr_auc | precision | recall_at_top_10pct | ks_statistic | top_10pct_threshold | train_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 61503 | 0.0807 | 0.7814 | 0.2768 | 0.2931 | 0.3631 | 0.4241 | 0.7062 | 20.17 |
| 2 | 61502 | 0.0807 | 0.7806 | 0.2728 | 0.2933 | 0.3633 | 0.4239 | 0.7051 | 20.35 |
| 3 | 61502 | 0.0807 | 0.7855 | 0.2724 | 0.2917 | 0.3613 | 0.4333 | 0.7006 | 20.04 |
| 4 | 61502 | 0.0807 | 0.7782 | 0.2651 | 0.2887 | 0.3577 | 0.4146 | 0.7035 | 19.19 |
| 5 | 61502 | 0.0807 | 0.7893 | 0.2854 | 0.3045 | 0.3772 | 0.4419 | 0.7037 | 20.23 |

## Business Interpretation

Cross-validation checks whether the selected LightGBM model is stable across different stratified slices of the applicant population. For a credit-risk ranking workflow, PR-AUC, Recall@Top-10%, and KS stability matter more than accuracy because the default class is rare and the business action is prioritizing the riskiest applicants for review.

## Saved Outputs

- `reports/cross_validation_results.csv`
- `reports/cross_validation_summary.md`
