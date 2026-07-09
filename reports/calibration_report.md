# Calibration Report

This report compares probability calibration methods for the saved final LightGBM model. Calibrators are fit on the validation split and evaluated on both validation and test splits. The ranking model is not retrained.

## Scope

- Rows used: `307,511`
- Feature columns: `76`
- Split strategy: same stratified 60% train, 20% validation, 20% test split as final modeling
- Sample size: full processed dataset

## Methods Compared

- `uncalibrated`: raw saved LightGBM probabilities.
- `platt_sigmoid`: logistic calibration fit on validation probabilities.
- `isotonic`: non-parametric isotonic calibration fit on validation probabilities.

## Metric Comparison

| method | split | brier_score | expected_calibration_error | roc_auc | pr_auc | recall_at_top_10pct | ks_statistic |
| --- | --- | --- | --- | --- | --- | --- | --- |
| uncalibrated | validation | 0.1643 | 0.2751 | 0.7799 | 0.2712 | 0.3644 | 0.4194 |
| uncalibrated | test | 0.1645 | 0.2742 | 0.7765 | 0.264 | 0.3593 | 0.4123 |
| platt_sigmoid | validation | 0.0666 | 0.0061 | 0.7799 | 0.2712 | 0.3644 | 0.4194 |
| platt_sigmoid | test | 0.0669 | 0.0062 | 0.7765 | 0.264 | 0.3593 | 0.4123 |
| isotonic | validation | 0.0662 | 0.0 | 0.7813 | 0.2645 | 0.3631 | 0.421 |
| isotonic | test | 0.0668 | 0.0023 | 0.776 | 0.254 | 0.3547 | 0.4121 |

## Validation-Only View

| method | split | brier_score | expected_calibration_error | roc_auc | pr_auc | recall_at_top_10pct | ks_statistic |
| --- | --- | --- | --- | --- | --- | --- | --- |
| uncalibrated | validation | 0.1643 | 0.2751 | 0.7799 | 0.2712 | 0.3644 | 0.4194 |
| platt_sigmoid | validation | 0.0666 | 0.0061 | 0.7799 | 0.2712 | 0.3644 | 0.4194 |
| isotonic | validation | 0.0662 | 0.0 | 0.7813 | 0.2645 | 0.3631 | 0.421 |

## Test Recommendation

The lowest test Brier score is from `isotonic` with Brier score `0.0668` and expected calibration error `0.0023`.

Ranking metrics should still be reviewed alongside calibration. For collections prioritization, ROC-AUC, PR-AUC, Recall@Top-10%, and KS remain important; for policy thresholds or customer-facing probabilities, calibrated probabilities are more appropriate than raw class-weighted model scores.

## Saved Outputs

- `reports/calibration_comparison.csv`
- `reports/calibration_report.md`
- `reports/figures/calibration_comparison.png`
