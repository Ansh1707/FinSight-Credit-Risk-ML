# Model Registry

This document is a lightweight model registry-style record for the saved FinSight final model. It is generated from existing artifacts and does not retrain the model.

## Registry Entry

| field | value |
| --- | --- |
| model_name | `FinSight Credit Risk LightGBM` |
| model_version | `0.13.0` |
| model_stage | `portfolio_ready_not_production_approved` |
| model_type | `lightgbm` |
| selection_metric | `validation_pr_auc` |
| threshold_strategy | `validation_top_10_percent_score_cutoff` |
| threshold | `0.6973716480146466` |
| top_k | `0.1` |
| rows_loaded | `307511` |
| feature_count | `76` |
| artifact_path | `models/credit_risk_model.pkl` |

## Validation Metrics

| field | value |
| --- | --- |
| roc_auc | `0.7799203369943319` |
| pr_auc | `0.2711740100132865` |
| precision | `0.2940985205657617` |
| recall | `0.36435045317220544` |
| f1_score | `0.3254767902123066` |
| recall_at_top_10pct | `0.36435045317220544` |
| ks_statistic | `0.4194457867434744` |

## Test Metrics

| field | value |
| --- | --- |
| roc_auc | `0.7764561203602978` |
| pr_auc | `0.2639813012708453` |
| precision | `0.2907662082514735` |
| recall | `0.3577039274924471` |
| f1_score | `0.3207802763478732` |
| recall_at_top_10pct | `0.35931520644511583` |
| ks_statistic | `0.41226513002671034` |

## MLflow Status

| field | value |
| --- | --- |
| status | `logged` |
| tracking_uri | `sqlite:///mlruns/mlflow.db` |
| experiment_name | `FinSight Credit Risk` |
| run_id | `2e99d5df17e244338c967c450c99bb78` |

## Governance References

- `reports/model_card.md`
- `reports/leakage_audit.md`
- `reports/fairness_proxy_analysis.md`
- `reports/governance_checklist.md`

## Production Status

This is a portfolio-ready model registry record. A real production registry would additionally require artifact storage controls, model approval workflow, deployment environment metadata, rollback links, monitoring ownership, and compliance sign-off.
