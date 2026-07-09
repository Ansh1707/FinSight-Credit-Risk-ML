# Final Model Report

The final credit-risk model is a tuned LightGBM classifier trained on `data/processed/model_features.parquet`.

## Why LightGBM Was Chosen

LightGBM was selected because it was the strongest baseline by validation PR-AUC, which is more appropriate than accuracy for rare-default credit risk ranking. The final phase tuned important tree and regularization hyperparameters and retained the model with the best validation PR-AUC.

## Scope

- Full processed feature dataset used.
- Feature columns: `76`
- Split strategy: stratified 60% train, 20% validation, 20% test.
- Class imbalance handling: `scale_pos_weight` from the training split.
- Operational threshold: validation top `10%` risk cutoff at score `0.697372`.
- Model selection metric: validation PR-AUC.

## Final Validation and Test Metrics

| split | roc_auc | pr_auc | precision | recall | f1_score | recall_at_top_10pct | ks_statistic | brier_score | tn | fp | fn | tp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | 0.7799 | 0.2712 | 0.2941 | 0.3644 | 0.3255 | 0.3644 | 0.4194 | 0.1643 | 52195 | 4342 | 3156 | 1809 |
| test | 0.7765 | 0.264 | 0.2908 | 0.3577 | 0.3208 | 0.3593 | 0.4123 | 0.1645 | 52206 | 4332 | 3189 | 1776 |

## Hyperparameter Tuning Results

| candidate | validation_pr_auc | train_seconds | objective | scale_pos_weight | random_state | n_jobs | verbose | n_estimators | learning_rate | num_leaves | min_child_samples | subsample | colsample_bytree | reg_alpha | reg_lambda |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4 | 0.2712 | 19.55 | binary | 11.38710976837865 | 42 | -1 | -1 | 600 | 0.02 | 63 | 120 | 0.85 | 0.8 | 0.2 | 4.0 |
| 1 | 0.2707 | 9.21 | binary | 11.38710976837865 | 42 | -1 | -1 | 350 | 0.035 | 31 | 60 | 0.85 | 0.85 | 0.0 | 1.0 |
| 2 | 0.2701 | 11.3 | binary | 11.38710976837865 | 42 | -1 | -1 | 500 | 0.025 | 31 | 80 | 0.9 | 0.9 | 0.1 | 2.0 |
| 3 | 0.2695 | 12.35 | binary | 11.38710976837865 | 42 | -1 | -1 | 450 | 0.03 | 45 | 100 | 0.8 | 0.85 | 0.1 | 3.0 |

## Calibration Analysis

- Validation Brier score: `0.1643`
- Test Brier score: `0.1645`
- The calibration curve should be reviewed before using raw probabilities as customer-facing or policy thresholds. Ranking metrics are stronger than probability calibration at this stage.

## Business Interpretation

The model is suitable as a portfolio risk-ranking baseline: it identifies a top-risk applicant slice that captures a materially larger share of defaults than random selection. For lending or collections use, the score should feed review queues, monitoring, and explainability workflows rather than act as an automatic approval or rejection rule.

## Saved Artifacts

- `models/credit_risk_model.pkl`
- `reports/final_model_metrics.json`
- `reports/final_model_report.md`
- `reports/figures/final_model_roc_curve.png`
- `reports/figures/final_model_precision_recall_curve.png`
- `reports/figures/final_model_calibration_curve.png`
