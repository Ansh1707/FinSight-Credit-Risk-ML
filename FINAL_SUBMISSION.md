# FinSight Final Submission Note

## Project

FinSight — Explainable Credit Risk & Collections ML Platform

## One-Line Pitch

Built an end-to-end credit-risk and collections ML platform that uses SQL, PySpark, LightGBM, SHAP, FastAPI, monitoring, dashboard-ready outputs, and governance documentation to predict loan default risk and prioritize high-risk applicants for review.


## Best Evidence

- End-to-end pipeline from raw data validation to feature engineering, modeling, explainability, API serving, monitoring, dashboard outputs, and governance.
- Recruiter-facing executive summary and interview defense guide.
- GitHub polish checklist for rendering, safety, links, commands, and final push readiness.
- GitHub repository presentation check with recommended description, topics, visibility status, and README first-screen review.
- SQL analysis layer under `sql/`.
- PySpark feature pipeline under `src/features/pyspark_feature_engineering.py`.
- Feature registry and timestamp-lineage report under `reports/feature_registry.md`.
- Reject inference methodology note under `reports/reject_inference_note.md`.
- Fair-lending governance review and protected/proxy feature controls under `reports/fair_lending_review.md` and `reports/proxy_feature_controls.csv`.
- Less-sensitive challenger model comparison under `reports/challenger_governance_report.md`.
- Batch scoring and privacy-safe prediction logging under `reports/batch_scoring_summary.md` and `reports/prediction_audit_log_sample.csv`.
- Production readiness runbook under `reports/production_readiness_runbook.md`.
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
| Fair-lending governance review | `reports/fair_lending_review.md` |
| Challenger model governance | `reports/challenger_governance_report.md` |
| Batch scoring audit sample | `reports/prediction_audit_log_sample.csv` |
| Production readiness runbook | `reports/production_readiness_runbook.md` |
| Executive summary | `reports/executive_summary.md` |
| Interview defense guide | `reports/interview_defense_guide.md` |
| GitHub polish checklist | `reports/github_polish_checklist.md` |
| GitHub repository presentation | `reports/github_repository_presentation.md` |
| Local test suite | `46` tests passed |

## Repository Safety

The repository is safe to share because these artifacts are ignored and not committed:

- Raw data under `data/raw/`
- Processed data under `data/processed/`
- Trained model binaries under `models/`
- Large HTML monitoring reports under `reports/*.html`
- Production log folders under `logs/` and `reports/production_logs/`
- Virtual environments and Python caches



## Honest Production Caveats

- This is a portfolio prototype, not a production-approved lending system.
- The dataset is public and historical, not Navi production data.
- Formal legal fair-lending certification, adverse-action compliance approval, applied reject inference with compliant rejected-applicant outcomes, and compliance sign-off are not included.
- Historical aggregate features have documented timestamp-lineage assumptions; production use still needs source-system enforcement of those cutoffs.
- Live deployment would require authentication, secure production log storage, production-grade model registry controls, executed alert routing, incident drills, rollback validation, and approval records.

## Final Recommendation

Use this project as the flagship portfolio project for fintech Data Scientist I applications. It demonstrates the strongest signal when paired with a concise explanation of why PR-AUC, Recall@Top-10%, KS, calibration, leakage review, explainability, and monitoring matter in credit risk.
