# FinSight Reviewer Guide

This guide is for recruiters, hiring managers, and data science interviewers who want to review FinSight quickly without running the full local pipeline.

## Fast Review Path

Read these files in order:

1. `README.md` — project overview, architecture, metrics, run commands, and resume bullets.
2. `FINAL_SUBMISSION.md` — concise final project handoff and sharing note.
3. `reports/final_project_audit.md` — strict final audit, rating, checklist, and production caveats.
4. `reports/final_case_study.md` — business story, methodology, validation, impact, and limitations.
5. `reports/model_card.md` — model governance, intended use, validation, calibration, fairness/proxy-risk, leakage, and monitoring.
6. `reports/governance_checklist.md` — production-readiness controls and sign-off checklist.
7. `reports/business_impact_summary.md` — review-capacity and collections-priority business interpretation.

## What This Project Demonstrates

| area | evidence |
| --- | --- |
| Credit-risk framing | README, project brief, final case study |
| SQL analysis | `sql/` and `reports/sql_analysis_summary.md` |
| PySpark feature engineering | `src/features/pyspark_feature_engineering.py` |
| Feature lineage | `src/features/feature_registry.py`, `reports/feature_registry.md` |
| Reject inference | `src/models/reject_inference.py`, `reports/reject_inference_note.md` |
| Imbalanced classification | `src/models/train_baseline.py`, `src/models/train_final_model.py` |
| Experiment tracking | `src/models/mlflow_tracking.py`, `reports/mlflow_experiment_summary.md` |
| Validation beyond accuracy | final report, cross-validation report, calibration report |
| Explainability | SHAP reason codes and plots |
| Business prioritization | collections scoring and business impact reports |
| API serving | FastAPI app and Dockerfile |
| Monitoring | drift and performance monitoring reports |
| Governance | model card, leakage audit, proxy-risk analysis, governance checklist |
| Engineering hygiene | tests, Makefile, CI workflow, `.gitignore` |
| Final handoff | final submission note and final project audit |

## Key Results To Notice

- Final model: tuned LightGBM classifier.
- Test ROC-AUC: `0.7765`.
- Test PR-AUC: `0.2640`.
- Test Recall@Top-10%: `0.3593`.
- Test KS statistic: `0.4123`.
- Cross-validation mean ROC-AUC: `0.7830`.
- Cross-validation mean PR-AUC: `0.2745`.
- Model registry-style documentation: `reports/model_registry.md`.
- Feature registry and timestamp-lineage documentation: `reports/feature_registry.md`.
- At `10%` review capacity, the model captures `43.72%` of observed defaults, a `4.37x` lift over random review.
- Leakage audit passed with `0` forbidden target or identifier fields in the model input list.
- Monitoring simulation found `0` features with PSI >= `0.2` and prediction PSI `0.000117`.
- Final strict project audit rating: `99/100`.

These are actual generated project results, not placeholder metrics.

## What Is Intentionally Not In Git

The following are intentionally ignored:

- Raw Home Credit CSV files under `data/raw/`.
- Processed Parquet files under `data/processed/`.
- Trained model binaries under `models/`.
- Large HTML monitoring reports under `reports/*.html`.
- Local virtual environments and Python cache files.

This keeps the repository safe to publish while preserving reproducible code and generated summaries.

## Local Verification Commands

For a lightweight code-quality check:

```bash
make check
```

For a full local project run after placing raw data under `data/raw/`:

```bash
python src/data/load_data.py
python src/data/eda_utils.py
python src/data/create_duckdb.py
python src/features/pyspark_feature_engineering.py
python src/features/leakage_checks.py
python src/models/train_baseline.py
python src/models/train_final_model.py
python src/models/cross_validate_model.py
python src/models/calibrate_model.py
python src/models/fairness_analysis.py
python src/explainability/shap_reason_codes.py
python src/business/collections_scoring.py
python src/business/business_impact.py
python src/monitoring/evidently_monitoring.py
python dashboard/build_dashboard_data.py
```

To run the API locally:

```bash
uvicorn src.api.main:app --reload
```

Open `http://127.0.0.1:8000/docs`.

## Interview Talking Points

- Why PR-AUC, Recall@Top-10%, and KS are more useful than accuracy for rare-default risk ranking.
- How class imbalance is handled with class weights or `scale_pos_weight`.
- How PySpark aggregates multiple raw lending tables to applicant level.
- Why leakage checks are necessary for historical repayment and bureau features.
- Why calibration matters before using raw probabilities as policy thresholds.
- How SHAP reason codes support analyst review but do not replace compliance-approved adverse-action logic.
- How proxy-risk analysis surfaces segment gaps without claiming legal fairness certification.
- How monitoring would work with real production windows and matured labels.

## Honest Limitations

- The dataset is public and historical, not live Navi data.
- The model is trained on accepted historical applicants only; reject inference methodology is documented but not applied because rejected-applicant outcomes are unavailable.
- Monitoring is simulated with historical splits.
- Formal fair-lending certification, adverse-action review, and compliance sign-off are outside the portfolio scope.
- Historical aggregate features need production timestamp controls before real deployment.

## Best Short Summary

FinSight is a production-style credit-risk and collections ML platform that goes beyond model training. It shows the full data science workflow: business framing, SQL and PySpark feature engineering, imbalanced model validation, calibration, explainability, collections prioritization, API serving, monitoring, dashboard outputs, leakage review, and governance documentation.
