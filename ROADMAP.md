# ROADMAP.md

## Project Roadmap and Completion Status

FinSight is complete as a portfolio-grade end-to-end credit-risk and collections ML project. Each phase is runnable from the VS Code terminal and saves outputs to the expected project folders.

## Phase 1: Project Scaffold - Complete

- Created production-style folder structure.
- Added package-level `__init__.py` files.
- Configured `.gitignore` for raw data, processed data, model artifacts, large HTML reports, virtual environments, and Python caches.

## Phase 2: Data Loading - Complete

- Validates required Home Credit raw files under `data/raw/`.
- Uses `application_train.csv` as the base table.
- Detects `TARGET`, target imbalance, missingness, and data types.
- Output: `reports/data_schema_summary.md`.

## Phase 3: EDA - Complete

- Analyzes target imbalance, missing values, numeric risk features, categorical segments, and default-rate differences.
- Output: `reports/eda_summary.md` and figures under `reports/figures/`.

## Phase 4: SQL Analysis - Complete

- Uses DuckDB for lending business analysis.
- Creates SQL queries for default rate by income, education, credit amount, occupation, and high-risk customer segments.
- Output: `reports/sql_analysis_summary.md`.

## Phase 5: PySpark Feature Engineering - Complete

- Aggregates bureau, bureau balance, previous application, installment, POS cash, and credit card tables to applicant level.
- Creates affordability, stability, bureau, repayment, missingness, and encoded categorical features.
- Adds an automated leakage audit for final model features, forbidden identifiers, and historical-feature timing risk.
- Output: `data/processed/model_features.parquet` and `reports/feature_engineering_summary.md`.
- Governance output: `reports/leakage_audit.md`.

## Phase 6: Baseline Modeling - Complete

- Trains Logistic Regression, Random Forest, XGBoost, and LightGBM when available.
- Handles class imbalance with class weights or `scale_pos_weight`.
- Output: `reports/model_comparison.csv`, `reports/baseline_modeling_summary.md`, and baseline model artifacts under `models/`.

## Phase 7: Final Model Validation - Complete

- Selects tuned LightGBM by validation PR-AUC.
- Evaluates ROC-AUC, PR-AUC, Precision, Recall, F1, Recall@Top-10%, KS statistic, confusion matrix, and calibration.
- Adds stratified 5-fold cross-validation to check champion-model stability.
- Adds Platt/sigmoid and isotonic calibration comparison.
- Adds proxy fairness and segment-performance analysis.
- Output: `models/credit_risk_model.pkl`, `reports/final_model_metrics.json`, `reports/final_model_report.md`, `reports/cross_validation_results.csv`, `reports/cross_validation_summary.md`, `reports/calibration_comparison.csv`, `reports/calibration_report.md`, `reports/fairness_proxy_metrics.csv`, and `reports/fairness_proxy_analysis.md`.

## Phase 8: Explainability - Complete

- Generates SHAP global feature importance and applicant-level reason codes.
- Output: `reports/explainability_summary.md`, `reports/sample_reason_codes.csv`, `reports/figures/shap_summary.png`, and `reports/figures/shap_bar.png`.

## Phase 9: Collections Scoring - Complete

- Converts predicted default probabilities into Low, Medium, High, and Critical risk bands.
- Creates a collections priority score using probability, normalized credit amount, and risk-band weight.
- Adds review-capacity business impact analysis using actual labels and credit-exposure proxies.
- Output: `reports/collections_priority_sample.csv`, `reports/collections_summary.md`, `reports/business_impact_by_threshold.csv`, and `reports/business_impact_summary.md`.

## Phase 10: API Deployment - Complete

- Builds FastAPI endpoints for health, prediction, explanation, and model metadata.
- Adds Docker support.
- Output: `src/api/`, `Dockerfile`, and `reports/api_summary.md`.

## Phase 11: Monitoring - Complete

- Simulates reference and current production windows.
- Monitors feature drift, prediction drift, missingness changes, and labeled model performance.
- Output: `reports/monitoring_summary.md`, `reports/monitoring_report.html`, and `reports/drift_report.html`.

## Phase 12: Dashboard - Complete

- Creates Power BI-ready CSV outputs from actual model, collections, explainability, and monitoring artifacts.
- Output: `dashboard/dashboard_data/` and `reports/dashboard_summary.md`.

## Phase 13: Final Documentation - Complete

- Polishes README for recruiter and GitHub review.
- Adds a final project case study.
- Documents final metrics, architecture, run commands, limitations, and resume bullets.
- Output: `README.md` and `reports/final_case_study.md`.

## Phase 14: Model Governance - Complete

- Adds a professional model card with intended use, prohibited use, training data, feature groups, validation metrics, calibration, explainability, proxy-risk findings, leakage audit, monitoring plan, limitations, and deployment readiness.
- Adds a governance and deployment checklist covering data controls, feature timing, validation, fairness review, API deployment, monitoring, rollback, retraining, and sign-off.
- Output: `reports/model_card.md` and `reports/governance_checklist.md`.

## Phase 15: GitHub Review Readiness - Complete

- Adds a reviewer guide so recruiters and interviewers can evaluate the project quickly without running the full pipeline.
- Adds a release checklist for GitHub safety, local quality checks, portfolio evidence, presentation, and interview readiness.
- Output: `REVIEW_GUIDE.md` and `RELEASE_CHECKLIST.md`.

## Phase 16: Repository Maintenance - Complete

- Adds license, changelog, contributing guide, security policy, pull request template, and issue templates.
- Documents how to make safe changes without committing raw data, processed data, model binaries, secrets, or unsupported production claims.
- Output: `LICENSE`, `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, `.github/PULL_REQUEST_TEMPLATE.md`, and `.github/ISSUE_TEMPLATE/`.

## Phase 17: Final Handoff And Audit - Complete

- Adds a concise final submission note for sharing the project with recruiters and interviewers.
- Adds a strict final project audit with rating, completion checklist, metric evidence, business evidence, governance evidence, repository safety audit, Navi role fit, and remaining production gaps.
- Output: `FINAL_SUBMISSION.md` and `reports/final_project_audit.md`.

## Phase 18: MLflow Tracking And Registry Documentation - Complete

- Adds optional MLflow logging for existing final model parameters, metrics, and report artifacts without retraining.
- Adds lightweight model registry-style JSON and Markdown documentation.
- Ignores local `mlruns/` tracking output in Git.
- Output: `src/models/mlflow_tracking.py`, `reports/mlflow_experiment_summary.md`, `reports/model_registry.md`, and `reports/model_registry.json`.

## Phase 19: Feature Registry And Timestamp Lineage - Complete

- Adds a generated feature registry covering source tables, source columns, transformation logic, join keys, aggregation levels, availability-time assumptions, leakage risk, owners, and production controls.
- Separates low-risk application-time features from proxy-risk categorical encodings and timing-sensitive historical aggregate features.
- Output: `src/features/feature_registry.py`, `reports/feature_registry.csv`, and `reports/feature_registry.md`.

## Phase 20: Reject Inference Methodology - Complete

- Adds a portfolio-safe reject inference methodology note without creating rejected-applicant labels or retraining models.
- Documents accepted-applicant bias, missing rejected outcomes, interpretation impact, and production methods such as parceling, fuzzy augmentation, bureau outcome matching, controlled exploration, and two-stage selection modeling.
- Output: `src/models/reject_inference.py`, `reports/reject_inference_note.md`, and `reports/reject_inference_methodology.json`.

## Phase 21: Fair-Lending And Proxy-Risk Governance - Complete

- Adds a formal portfolio fair-lending and proxy-risk governance review without claiming legal certification.
- Converts existing segment metrics and feature-registry metadata into protected/proxy feature controls, segment-risk interpretation, production controls, and sign-off requirements.
- Documents restricted, review-required, monitoring-required, timestamp-controlled, and vendor-governance-required feature classes.
- Output: `src/models/fair_lending_governance.py`, `reports/fair_lending_review.md`, `reports/proxy_feature_controls.csv`, and `reports/fair_lending_governance.json`.

## Phase 22: Challenger Model Governance - Complete

- Adds a less-sensitive challenger model workflow that removes restricted and enhanced-review protected/proxy features.
- Compares champion and challenger models with actual PR-AUC, Recall@Top-10%, KS, calibration, and top-10% business impact metrics.
- Documents the tradeoff between predictive lift and fair-lending/proxy-risk exposure without inventing metrics or changing the champion model.
- Output: `src/models/challenger_governance.py`, `reports/challenger_model_comparison.csv`, `reports/challenger_governance_report.md`, and `reports/challenger_governance.json`.

## Phase 23: Batch Scoring And Prediction Logging - Complete

- Adds production-style batch scoring using the saved final model without retraining.
- Validates the serving schema before scoring and documents required features, output columns, audit-log columns, and privacy controls.
- Writes privacy-safe prediction and audit samples with request IDs, batch ID, score timestamp, model metadata, schema version, hashed applicant ID, risk band, priority score, and reason-code fields.
- Output: `src/api/batch_score.py`, `reports/batch_scoring_sample.csv`, `reports/prediction_audit_log_sample.csv`, `reports/batch_scoring_schema.json`, and `reports/batch_scoring_summary.md`.

## Phase 24: Production Readiness Runbook - Complete

- Adds an operator-facing production readiness runbook for pre-production review.
- Covers deployment steps, batch scoring operations, monitoring cadence, alert thresholds, rollback plan, incident response, retraining triggers, ownership, and final sign-off.
- Adds a machine-readable checklist with required owners, approval gates, alert thresholds, and privacy controls.
- Output: `reports/production_readiness_runbook.md` and `reports/production_readiness_checklist.json`.

## Final Manual Checks Before GitHub Push

```bash
source .venv/bin/activate
python -m compileall src dashboard tests
python src/models/predict.py --input data/processed/model_features.parquet --limit 5
uvicorn src.api.main:app --reload
```

Before committing, verify ignored files with:

```bash
git status --ignored
```

Raw data, processed data, trained models, HTML reports, virtual environments, and Python caches should remain untracked or ignored.
