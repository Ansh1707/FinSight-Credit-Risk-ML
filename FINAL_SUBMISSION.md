# FinSight Final Submission Note

## Project

FinSight — Explainable Credit Risk & Collections ML Platform

## Target Role

Data Scientist I, fintech credit-risk and collections analytics.

## One-Line Pitch

Built an end-to-end credit-risk and collections ML platform that uses SQL, PySpark, LightGBM, SHAP, FastAPI, monitoring, dashboard-ready outputs, and governance documentation to predict loan default risk and prioritize high-risk applicants for review.

## What To Share First

GitHub reviewers should start here:

1. `README.md`
2. `REVIEW_GUIDE.md`
3. `reports/final_case_study.md`
4. `reports/model_card.md`
5. `reports/final_project_audit.md`

## Best Evidence

- End-to-end pipeline from raw data validation to feature engineering, modeling, explainability, API serving, monitoring, dashboard outputs, and governance.
- SQL analysis layer under `sql/`.
- PySpark feature pipeline under `src/features/pyspark_feature_engineering.py`.
- Feature registry and timestamp-lineage report under `reports/feature_registry.md`.
- Reject inference methodology note under `reports/reject_inference_note.md`.
- Final tuned LightGBM model validation with ROC-AUC, PR-AUC, Recall@Top-10%, KS statistic, confusion matrix, calibration, and cross-validation.
- MLflow tracking script and model registry-style documentation for the existing final model artifacts.
- Business impact analysis showing the model-ranked top `10%` review queue captures `43.72%` of observed defaults, a `4.37x` lift over random review.
- SHAP reason codes and proxy-risk analysis.
- Leakage audit, model card, governance checklist, security policy, release checklist, and reviewer guide.

## Final Verified Results

| area | result |
| --- | --- |
| Final model | Tuned LightGBM classifier |
| Test ROC-AUC | `0.7765` |
| Test PR-AUC | `0.2640` |
| Test Recall@Top-10% | `0.3593` |
| Test KS statistic | `0.4123` |
| Cross-validation ROC-AUC mean | `0.7830` |
| Cross-validation PR-AUC mean | `0.2745` |
| Top 10% default capture | `43.72%` |
| Top 10% lift vs random | `4.37x` |
| Leakage audit | Passed with `0` forbidden target/identifier inputs |
| Model registry documentation | `reports/model_registry.md` |
| Feature registry documentation | `reports/feature_registry.md` |
| Reject inference methodology | `reports/reject_inference_note.md` |
| Local test suite | `36` tests passed |

## Repository Safety

The repository is safe to share because these artifacts are ignored and not committed:

- Raw data under `data/raw/`
- Processed data under `data/processed/`
- Trained model binaries under `models/`
- Large HTML monitoring reports under `reports/*.html`
- Virtual environments and Python caches

## How To Position This In An Interview

Emphasize that this is not just a model. It is a production-style data science workflow:

- Business framing before modeling.
- SQL and PySpark for scalable analysis and feature engineering.
- Ranking-focused validation because defaults are imbalanced.
- Calibration and leakage checks because credit-risk probabilities can affect policy decisions.
- SHAP explanations and reason codes for analyst usability.
- Collections priority scoring that translates ML into an operational queue.
- Monitoring and governance because real fintech models need lifecycle controls.

## Honest Production Caveats

- This is a portfolio prototype, not a production-approved lending system.
- The dataset is public and historical, not Navi production data.
- Formal fair-lending certification, adverse-action review, applied reject inference with compliant rejected-applicant outcomes, and compliance sign-off are not included.
- Historical aggregate features have documented timestamp-lineage assumptions; production use still needs source-system enforcement of those cutoffs.
- Live deployment would require authentication, logging, production-grade model registry controls, alerts, rollback, and incident ownership.

## Final Recommendation

Use this project as the flagship portfolio project for fintech Data Scientist I applications. It demonstrates the strongest signal when paired with a concise explanation of why PR-AUC, Recall@Top-10%, KS, calibration, leakage review, explainability, and monitoring matter in credit risk.
