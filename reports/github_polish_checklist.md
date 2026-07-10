# FinSight GitHub Polish Checklist

## Purpose

This checklist verifies that FinSight is safe, readable, and portfolio-ready before sharing the GitHub repository with recruiters, hiring managers, or Navi Data Scientist I interviewers.

## Final Reviewer Path

Use this order for the cleanest first impression:

1. `README.md`
2. `reports/executive_summary.md`
3. `reports/interview_defense_guide.md`
4. `REVIEW_GUIDE.md`
5. `FINAL_SUBMISSION.md`
6. `reports/final_project_audit.md`
7. `reports/model_card.md`
8. `reports/governance_checklist.md`
9. `reports/production_readiness_runbook.md`

## README Rendering Checks

- [x] README starts with a clear project title and status badges.
- [x] Reviewer quick links are visible near the top.
- [x] Architecture is shown in a Markdown text diagram.
- [x] Tables are used for final metrics, calibration, business impact, and risk-band summaries.
- [x] Local commands are fenced with `bash` or `text`.
- [x] The README includes honest limitations and does not claim production approval.
- [x] The README links to recruiter-facing and governance artifacts.

Manual GitHub check:

```bash
git status --short
```

Then open the repository page and confirm that the README preview renders the badges, tables, code blocks, architecture text diagram, and reviewer links cleanly.

## Repository Safety Checks

- [x] Raw data under `data/raw/` is ignored.
- [x] Processed data under `data/processed/` is ignored.
- [x] Trained model artifacts under `models/` are ignored.
- [x] MLflow local tracking output under `mlruns/` is ignored.
- [x] Large HTML reports under `reports/*.html` are ignored.
- [x] Virtual environments are ignored.
- [x] Python caches and notebook checkpoints are ignored.
- [x] Local production log folders are ignored.
- [x] No raw data, processed data, models, or MLflow run artifacts are tracked by Git.

Verification commands:

```bash
git status --ignored --short
git ls-files data models mlruns reports/*.html .venv
```

Expected result: ignored artifacts may appear with `!!`, and `git ls-files` should return no tracked raw data, processed data, model artifacts, MLflow runs, HTML monitoring reports, or virtual environment files.

## Final Link And Artifact Checks

- [x] Reviewer quick links point to existing files.
- [x] Governance artifacts listed in README exist.
- [x] Dashboard-ready CSV files exist under `dashboard/dashboard_data/`.
- [x] GitHub workflow, issue templates, pull request template, license, security policy, contributing guide, and changelog are present.
- [x] Hygiene tests check expected project files, README sections, `.gitignore` safety, and local Markdown/report references.

Verification commands:

```bash
make check
git diff --check
```

## Command Snippet Checks

Primary commands documented for reviewers:

```bash
python src/data/load_data.py
python src/data/eda_utils.py
python src/data/create_duckdb.py
python src/features/pyspark_feature_engineering.py
python src/features/feature_registry.py
python src/features/leakage_checks.py
python src/models/train_baseline.py
python src/models/train_final_model.py
python src/models/mlflow_tracking.py
python src/models/reject_inference.py
python src/models/fair_lending_governance.py
python src/models/challenger_governance.py
python src/models/cross_validate_model.py
python src/models/calibrate_model.py
python src/models/fairness_analysis.py
python src/explainability/shap_reason_codes.py
python src/business/collections_scoring.py
python src/business/business_impact.py
python src/api/batch_score.py --input data/processed/model_features.parquet --limit 1000
uvicorn src.api.main:app --reload
python src/monitoring/evidently_monitoring.py
python dashboard/build_dashboard_data.py
```

Reviewer note: commands that depend on `data/raw/`, `data/processed/`, or `models/credit_risk_model.pkl` require local artifacts that are intentionally ignored by Git.

## Portfolio Presentation Checks

- [x] Project positioning is clear: credit risk, collections, explainability, monitoring, governance, and API serving.
- [x] Metrics are actual generated results, not placeholders.
- [x] Accuracy is not used as the main model metric.
- [x] Business impact is expressed through review capacity, default capture, and lift.
- [x] Limitations are explicit: public data, simulated monitoring, accepted-applicant bias, reject inference not applied, fair-lending review not legal certification, and production timestamp controls still required.
- [x] Interview preparation exists in 2-minute, 5-minute, and deep-dive formats.

## Push-Ready Checklist

Run this final sequence before sharing:

```bash
git status --short
make check
git diff --check
git status --ignored --short
git ls-files data models mlruns reports/*.html .venv
```

Before pushing, confirm:

- [ ] Only intentional documentation, code, or test files are staged.
- [ ] No ignored data/model/HTML/venv artifacts are force-added.
- [ ] `make check` passes locally.
- [ ] `git diff --check` reports no whitespace errors.
- [ ] README renders cleanly on GitHub after push.
- [ ] Repository description and topics are set on GitHub.
- [ ] Private repository access is granted to intended reviewers, or the repository is made public when ready.

## Final GitHub Topic Suggestions

Recommended topics:

- `credit-risk`
- `machine-learning`
- `fintech`
- `pyspark`
- `fastapi`
- `shap`
- `model-monitoring`
- `mlflow`
- `lightgbm`
- `model-governance`

## Final Positioning Statement

FinSight is ready to present as a portfolio-grade, production-style credit-risk and collections ML platform. It demonstrates not only modeling, but also feature engineering, SQL analysis, explainability, business prioritization, API serving, monitoring, audit logging, governance, and interview-ready communication.
