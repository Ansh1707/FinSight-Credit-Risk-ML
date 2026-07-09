# MLflow Experiment Summary

This report documents MLflow tracking for the existing FinSight final model artifacts. The script does not train or retrain any model.

## Status

| field | value |
| --- | --- |
| status | `mlflow_not_installed` |
| tracking_uri | `file:mlruns` |
| experiment_name | `FinSight Credit Risk` |
| run_id | `None` |

## Logged Content

- Final model parameters from `reports/final_model_metrics.json`
- Validation and test classification metrics
- Validation and test Brier scores
- Final model report, calibration report, cross-validation summary, business impact summary, explainability summary, fairness/proxy-risk analysis, leakage audit, and model card when present

## How To Run

```bash
python src/models/mlflow_tracking.py
```

Open the local MLflow UI after logging:

```bash
mlflow ui --backend-store-uri mlruns
```

## Local Environment Note

MLflow is not installed in the current environment, so the script wrote registry documentation but did not create an MLflow run. Install project requirements and rerun the command to create the local `mlruns/` tracking store.

## Registry Outputs

- `reports/model_registry.json`
- `reports/model_registry.md`
- `reports/mlflow_experiment_summary.md`

## Production Interpretation

This adds experiment tracking and registry-style documentation for portfolio reproducibility. A real production model registry would also include approval stages, access control, artifact retention, deployment links, rollback metadata, and model owner sign-off.
