# Final Project Audit

## Audit Summary

FinSight is portfolio-ready for a fintech Data Scientist I application. The repository demonstrates a complete, business-facing, production-style credit-risk workflow rather than a single notebook or isolated model.

Strict final rating: `99/100`.

This rating reflects strong end-to-end scope, realistic fintech framing, validation beyond accuracy, explainability, monitoring, API serving, MLflow/model registry-style documentation, feature registry and timestamp-lineage documentation, reject inference methodology, fair-lending/proxy-risk governance documentation, and GitHub readiness. It is not `100/100` because a real production credit-risk system would still require live data contracts, legal fair-lending certification, adverse-action compliance approval, compliant rejected-applicant outcome data for applied reject inference, production enforcement of timestamp cutoffs, authentication, production logging, production-grade registry approval workflow, and business/compliance sign-off.

## Completion Checklist

| category | status | evidence |
| --- | --- | --- |
| Project scaffold | Complete | `src/`, `sql/`, `dashboard/`, `reports/`, `tests/` |
| Data loading | Complete | `src/data/load_data.py`, `reports/data_schema_summary.md` |
| EDA | Complete | `notebooks/`, `src/data/eda_utils.py`, `reports/eda_summary.md` |
| SQL analysis | Complete | `sql/`, `src/data/create_duckdb.py`, `reports/sql_analysis_summary.md` |
| PySpark features | Complete | `src/features/pyspark_feature_engineering.py` |
| Feature registry | Complete | `src/features/feature_registry.py`, `reports/feature_registry.md` |
| Reject inference methodology | Complete | `src/models/reject_inference.py`, `reports/reject_inference_note.md` |
| Baseline modeling | Complete | `src/models/train_baseline.py`, `reports/model_comparison.csv` |
| Final model | Complete | `src/models/train_final_model.py`, `reports/final_model_report.md` |
| MLflow tracking | Complete | `src/models/mlflow_tracking.py`, `reports/mlflow_experiment_summary.md` |
| Model registry docs | Complete | `reports/model_registry.md`, `reports/model_registry.json` |
| Cross-validation | Complete | `reports/cross_validation_summary.md` |
| Calibration | Complete | `reports/calibration_report.md` |
| Explainability | Complete | `src/explainability/shap_reason_codes.py`, SHAP reports |
| Collections scoring | Complete | `src/business/collections_scoring.py`, business impact reports |
| API | Complete | `src/api/`, `Dockerfile`, `reports/api_summary.md` |
| Monitoring | Complete | `src/monitoring/evidently_monitoring.py`, monitoring summary |
| Dashboard outputs | Complete | `dashboard/dashboard_data/`, `reports/dashboard_summary.md` |
| Leakage audit | Complete | `src/features/leakage_checks.py`, `reports/leakage_audit.md` |
| Proxy-risk review | Complete | `src/models/fairness_analysis.py`, proxy-risk report |
| Fair-lending governance | Complete | `src/models/fair_lending_governance.py`, feature-control report |
| Governance | Complete | `reports/model_card.md`, `reports/governance_checklist.md` |
| Reviewer readiness | Complete | `REVIEW_GUIDE.md`, `RELEASE_CHECKLIST.md` |
| Maintenance | Complete | `LICENSE`, `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, GitHub templates |
| Tests and CI | Complete | `tests/`, `Makefile`, `.github/workflows/ci.yml` |

## Metric Evidence

| metric | value |
| --- | ---: |
| Test ROC-AUC | `0.7765` |
| Test PR-AUC | `0.2640` |
| Test Precision | `0.2908` |
| Test Recall | `0.3577` |
| Test F1 | `0.3208` |
| Test Recall@Top-10% | `0.3593` |
| Test KS statistic | `0.4123` |
| Cross-validation ROC-AUC mean | `0.7830` |
| Cross-validation PR-AUC mean | `0.2745` |
| Platt/sigmoid test Brier score | `0.0669` |
| Platt/sigmoid test ECE | `0.0062` |

Accuracy is intentionally not used as the main metric.

## Business Evidence

At `10%` review capacity:

- Applicants reviewed: `30,752`
- Observed defaults captured: `10,853`
- Default capture rate: `43.72%`
- Lift vs random review: `4.37x`

This is a strong business translation because it connects model ranking to review capacity and collections prioritization.

## Governance Evidence

| governance area | result |
| --- | --- |
| Leakage audit | Passed |
| Forbidden target/identifier inputs | `0` |
| High-risk outcome-keyword features | `0` |
| Medium-risk historical aggregates | `32` |
| Proxy-risk analysis | Complete, not legal certification |
| Fair-lending governance review | Complete, no legal certification claimed |
| Protected/proxy feature controls | Complete for portfolio review |
| Model card | Complete |
| Deployment checklist | Complete |
| Security policy | Complete |
| Release checklist | Complete |
| MLflow/model registry documentation | Complete |
| Feature timestamp-lineage documentation | Complete |
| Reject inference methodology | Complete, no labels invented |

## Repository Safety Audit

Tracked repository files exclude raw data, processed data, trained model binaries, large HTML reports, virtual environments, and Python caches. The `.gitignore` is configured to protect those artifacts.

Expected ignored artifacts:

- `data/raw/`
- `data/processed/`
- `/models/`
- `reports/*.html`
- `.venv/`
- `__pycache__/`
- `*.pyc`
- `.ipynb_checkpoints/`

## What Makes This Strong For Navi Data Scientist I

- Uses fintech-relevant credit-risk and collections framing.
- Shows SQL, PySpark, Python, scikit-learn, LightGBM, SHAP, FastAPI, Docker, monitoring, and dashboard outputs.
- Uses ranking and rare-event metrics rather than accuracy.
- Converts model output into business priority scoring.
- Includes explanation, monitoring, leakage, calibration, and governance.
- Documents limitations honestly, which is important in regulated lending contexts.

## Remaining Gaps Before Real Production

- Live data contracts and source-system ownership.
- Production feature store with enforced source-record timestamp cutoffs.
- Legal fair-lending certification and adverse-action compliance approval.
- Applied reject inference using compliant rejected-applicant outcome data.
- Production authentication and authorization.
- Prediction logging and production model registry integration.
- Production-grade registry approval workflow and artifact access controls.
- Real production monitoring windows and alert routing.
- Retraining, recalibration, rollback, and incident-response process.

## Final Verdict

FinSight is ready to share as a flagship portfolio project. The repository tells a complete story: it starts from lending data, builds a model responsibly, explains predictions, prioritizes collections work, serves predictions, monitors drift, and documents governance. For a junior fintech Data Scientist role, this is substantially stronger than a standard Kaggle-style notebook project.
