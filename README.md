# FinSight: Explainable Credit Risk & Collections ML Platform

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![CI](https://img.shields.io/badge/CI-GitHub%20Actions-green)
![Model](https://img.shields.io/badge/Model-LightGBM-orange)
![API](https://img.shields.io/badge/API-FastAPI-teal)
![Status](https://img.shields.io/badge/Status-Portfolio%20Ready-brightgreen)

FinSight is an end-to-end fintech data science project for credit default prediction, explainable risk review, collections prioritization, API serving, model monitoring, and dashboard-ready reporting. It is designed as a portfolio project for a Navi Data Scientist I application.

## Reviewer Quick Links

- `REVIEW_GUIDE.md` — fast path for recruiters and interviewers.
- `FINAL_SUBMISSION.md` — concise final project handoff and sharing note.
- `reports/final_case_study.md` — end-to-end business case study.
- `reports/final_project_audit.md` — strict final audit, rating, checklist, and production caveats.
- `reports/model_card.md` — model card with validation, calibration, explainability, proxy-risk, leakage, and monitoring.
- `reports/governance_checklist.md` — production-readiness and deployment controls.
- `reports/fair_lending_review.md` — formal fair-lending/proxy-risk governance review without legal-certification claims.
- `RELEASE_CHECKLIST.md` — final GitHub safety and presentation checklist.
- `CHANGELOG.md` — release-history style summary of project maturity milestones.

## Business Problem

Digital lenders need to identify applicants who are likely to default, understand why they are risky, and prioritize high-risk accounts for review or collections. A useful credit-risk workflow needs more than a model score: it needs feature pipelines, validation, explainability, monitoring, and business-facing outputs.

FinSight answers:

> Which applicants are most likely to default, what risk drivers explain the prediction, and how should collections teams prioritize action?

## Solution Overview

The project uses the Home Credit Default Risk dataset to build a production-style machine learning workflow:

- validate raw lending data without modifying it
- analyze default behavior with Python and SQL
- engineer applicant-level features with PySpark
- train and validate baseline and final classifiers
- explain global and applicant-level risk with SHAP
- convert predictions into collections risk bands and priority scores
- serve predictions through FastAPI
- monitor drift, missingness, prediction movement, and performance
- generate dashboard-ready CSV files for Power BI

## Architecture

```text
data/raw/*.csv
    |
    v
src/data/load_data.py              -> reports/data_schema_summary.md
src/data/eda_utils.py              -> reports/eda_summary.md, reports/figures/
src/data/create_duckdb.py + sql/   -> reports/sql_analysis_summary.md
    |
    v
src/features/pyspark_feature_engineering.py
    -> data/processed/model_features.parquet
    -> reports/feature_engineering_summary.md
    |
    v
src/models/train_baseline.py       -> reports/model_comparison.csv, models/*.joblib
src/models/train_final_model.py    -> models/credit_risk_model.pkl, final metrics
    |
    +--> src/explainability/shap_reason_codes.py -> SHAP plots, reason codes
    +--> src/business/collections_scoring.py     -> risk bands, priority queue
    +--> src/api/main.py                         -> FastAPI prediction service
    +--> src/monitoring/evidently_monitoring.py  -> drift and quality reports
    +--> dashboard/build_dashboard_data.py       -> Power BI-ready CSV files
```

## Dataset

The project uses the Home Credit Default Risk dataset stored locally under `data/raw/`. Raw data is ignored by Git and is never modified by project scripts.

Expected local files:

- `application_train.csv`
- `HomeCredit_columns_description.csv`
- `bureau.csv`
- `bureau_balance.csv`
- `previous_application.csv`
- `installments_payments.csv`
- `POS_CASH_balance.csv`
- `credit_card_balance.csv`

The base table is `application_train.csv`, with `TARGET` as the binary default label. The processed model table contains `307,511` applicants and `78` columns.

## Feature Engineering Summary

PySpark is used to aggregate multiple Home Credit tables to applicant level (`SK_ID_CURR`). The pipeline creates lending-risk features including:

- affordability ratios: `credit_to_income_ratio`, `annuity_to_income_ratio`, `annuity_to_credit_ratio`
- applicant stability: `employment_years`, `age_years`
- external credit signal aggregates: `external_score_mean`, `external_score_std`
- missingness signal: `missing_value_count`
- bureau history: credit counts, overdue counts, debt-to-credit ratio
- previous application history: prior counts, approved/refused counts, down payment and credit summaries
- repayment behavior: installment delay, late payment count, POS delinquency, credit card balance and DPD signals
- encoded categorical variables for contract type, gender, education, family status, housing type, occupation, and related applicant attributes

Numeric nulls are filled after creating `missing_value_count`; selected categorical nulls are encoded as `Missing`.

## Feature Registry And Timestamp Lineage

Generate the feature registry and timestamp-lineage documentation:

```bash
python src/features/feature_registry.py
```

The command writes:

- `reports/feature_registry.csv`
- `reports/feature_registry.md`

The registry documents `76` final model features across application, derived affordability/stability, encoded categorical, bureau, bureau balance, previous application, installment repayment, POS cash, and credit-card feature groups. For each group it records source tables, source columns, transformation logic, join key, aggregation level, availability-time assumptions, leakage risk, owner, and production controls.

Key governance outcome: application-time features are low leakage risk, encoded categorical features require proxy-risk review, and historical bureau/repayment/balance aggregates require source-record timestamp cutoffs before production use.

## Modeling Approach

The project creates a stratified train/validation/test split and handles class imbalance using class weights or `scale_pos_weight`. Accuracy is not used as the primary metric because defaults are rare and the business task is risk ranking.

Baseline models trained:

- Logistic Regression
- Random Forest
- XGBoost
- LightGBM

LightGBM was selected as the final model because it produced the strongest validation PR-AUC among the baselines. The final model was tuned using validation PR-AUC as the selection metric.

## MLflow Tracking And Model Registry

Create MLflow tracking records and registry-style documentation from existing final model artifacts:

```bash
python src/models/mlflow_tracking.py
```

This command does not retrain the model. It reads `reports/final_model_metrics.json`, logs parameters, metrics, and report artifacts to MLflow when MLflow is installed, and always writes:

- `reports/mlflow_experiment_summary.md`
- `reports/model_registry.md`
- `reports/model_registry.json`

Local MLflow UI:

```bash
mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db
```

The local `mlruns/` tracking store is ignored by Git. The script uses a local SQLite backend at `sqlite:///mlruns/mlflow.db` to avoid MLflow's deprecated filesystem tracking backend.

## Final Metrics

Final model: tuned LightGBM classifier.

| split | ROC-AUC | PR-AUC | Precision | Recall | F1 | Recall@Top-10% | KS | Brier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| validation | 0.7799 | 0.2712 | 0.2941 | 0.3644 | 0.3255 | 0.3644 | 0.4194 | 0.1643 |
| test | 0.7765 | 0.2640 | 0.2908 | 0.3577 | 0.3208 | 0.3593 | 0.4123 | 0.1645 |

Operational threshold: validation top `10%` risk cutoff at score `0.697372`.

The model is best interpreted as a risk-ranking and prioritization model. Calibration should be reviewed before using raw probabilities for strict policy thresholds.

## Reject Inference Methodology

Generate the reject inference methodology note:

```bash
python src/models/reject_inference.py
```

The command writes:

- `reports/reject_inference_note.md`
- `reports/reject_inference_methodology.json`

This analysis does not invent rejected-applicant labels and does not retrain the model. It explains accepted-applicant bias, why rejected-applicant outcomes are missing, how that affects interpretation, and which production methods would be considered before real lending deployment, including parceling, fuzzy augmentation, bureau outcome matching, controlled exploration, and two-stage selection modeling.

## Cross-Validation

Run stratified K-fold validation around the selected LightGBM configuration:

```bash
python src/models/cross_validate_model.py
```

The command writes `reports/cross_validation_results.csv` and `reports/cross_validation_summary.md`. This phase checks whether ROC-AUC, PR-AUC, Recall@Top-10%, and KS are stable across folds.

Actual 5-fold stability results:

| metric | mean | std | min | max |
| --- | ---: | ---: | ---: | ---: |
| ROC-AUC | 0.7830 | 0.0044 | 0.7782 | 0.7893 |
| PR-AUC | 0.2745 | 0.0074 | 0.2651 | 0.2854 |
| Recall@Top-10% | 0.3646 | 0.0074 | 0.3577 | 0.3772 |
| KS statistic | 0.4276 | 0.0104 | 0.4146 | 0.4419 |

## Calibration

Compare raw final-model probabilities against Platt/sigmoid and isotonic calibration:

```bash
python src/models/calibrate_model.py
```

The command writes `reports/calibration_comparison.csv`, `reports/calibration_report.md`, and `reports/figures/calibration_comparison.png`. This phase separates ranking quality from probability quality, which matters in credit-risk settings where probabilities may feed policy thresholds or portfolio planning.

Actual test-set calibration results:

| method | Brier | ECE | ROC-AUC | PR-AUC | Recall@Top-10% |
| --- | ---: | ---: | ---: | ---: | ---: |
| Uncalibrated | 0.1645 | 0.2742 | 0.7765 | 0.2640 | 0.3593 |
| Platt/sigmoid | 0.0669 | 0.0062 | 0.7765 | 0.2640 | 0.3593 |
| Isotonic | 0.0668 | 0.0023 | 0.7760 | 0.2540 | 0.3547 |

Platt/sigmoid calibration is the most balanced option because it materially improves probability calibration while preserving the final model's ranking metrics. Isotonic has the lowest test Brier score but slightly weakens PR-AUC and Recall@Top-10%.

## Fairness And Proxy-Risk Analysis

Run segment-level performance and proxy-risk checks:

```bash
python src/models/fairness_analysis.py
```

The command writes `reports/fairness_proxy_metrics.csv` and `reports/fairness_proxy_analysis.md`. This is not a legal fairness certification; it is a portfolio-grade segment-performance review across age bands, income bands, and encoded categorical proxies for gender, education, family status, and occupation.

Key findings from the current run:

- Highest top-10% review-rate segment: `OCCUPATION_TYPE_idx=13` at `32.11%`, with observed default rate `17.15%`.
- Age band `18-25` has top-10% review rate `22.50%` and observed default rate `12.29%`.
- Encoded gender proxy `CODE_GENDER_idx=1` has top-10% review rate `14.03%` versus `7.91%` for `CODE_GENDER_idx=0`.
- Segment gaps should trigger deeper fair-lending, policy, and feature-governance review before production use.

## Fair-Lending Governance Review

Generate the formal fair-lending and proxy-risk governance review:

```bash
python src/models/fair_lending_governance.py
```

The command writes:

- `reports/fair_lending_review.md`
- `reports/proxy_feature_controls.csv`
- `reports/fair_lending_governance.json`

This review uses the existing segment metrics and feature registry to document protected/proxy feature controls, segment-risk interpretation, production sign-off requirements, and compliance-ready limitations. It does not claim legal fair-lending certification, does not approve adverse-action language, does not infer protected-class membership, and does not retrain the model.

Current control summary: `76` model features reviewed; `1` gender proxy feature restricted pending fair-lending approval; `2` age-related features restricted pending policy approval; `5` categorical socioeconomic/employment proxies requiring fair-lending review; `7` region/social-network proxies requiring enhanced review; `32` historical credit-behavior features requiring timestamp controls.

## Challenger Model Governance

Train and compare a less-sensitive challenger model:

```bash
python src/models/challenger_governance.py
```

The command writes:

- `reports/challenger_model_comparison.csv`
- `reports/challenger_governance_report.md`
- `reports/challenger_governance.json`
- `models/less_sensitive_challenger_model.pkl` locally, ignored by Git

The challenger removes `15` features flagged as restricted, fair-lending-review-required, or enhanced-review proxy features. It keeps `61` lower-risk model features and compares against the saved champion model using actual computed PR-AUC, Recall@Top-10%, KS, Brier score, expected calibration error, and top-10% business capture.

Current result: the challenger reduced protected/proxy exposure with a modest performance tradeoff. Test PR-AUC moved from `0.2640` to `0.2559`, Recall@Top-10% moved from `0.3593` to `0.3488`, and KS moved from `0.4123` to `0.4013`. This is governance evidence for discussing whether the champion's predictive lift justifies stronger fair-lending controls.

## Leakage Audit

Run a feature leakage audit against the saved final model feature list:

```bash
python src/features/leakage_checks.py
```

The command writes `reports/leakage_audit.md`. The audit verifies that target and identifier fields are excluded from the model feature list, classifies historical aggregate features as medium-risk timing assumptions, and documents which features require human review before production use.

Current audit result: `passed`. The saved model uses `76` input features; `0` forbidden target/identifier fields were found, `0` model features were missing from the processed table, `0` high-risk outcome-keyword features were found, and `32` historical aggregate features were flagged as medium-risk timing assumptions. Those medium-risk features should have source-record timestamp filters before production use.

## Explainability

SHAP is used for global feature importance and applicant-level reason codes. The explainability script samples `5,000` processed applicants for SHAP analysis and only generates reason codes from positive SHAP contributions.

Top global model drivers from the SHAP run include:

- `external_score_mean`
- `annuity_to_credit_ratio`
- `CODE_GENDER_idx`
- `goods_price_to_credit_ratio`
- `pos_cash_avg_installments_future`
- `NAME_EDUCATION_TYPE_idx`
- `pos_cash_month_count`
- `installment_max_payment_delay_days`
- `EXT_SOURCE_1`
- `AMT_ANNUITY`

Example business reason codes include low external credit score, annuity burden risk signal, prior refused application history, high bureau debt burden, and prior repayment delay.

## Collections Scoring Logic

The collections module converts model predictions into risk bands and a priority score.

Risk bands:

- Low Risk: probability < 0.25
- Medium Risk: 0.25 <= probability < 0.50
- High Risk: 0.50 <= probability < 0.70
- Critical Risk: probability >= 0.70

Priority score:

```text
collections_priority_score =
100 * default_probability * (0.70 + 0.30 * normalized_credit_amount) * risk_band_weight
```

Risk band weights:

- Low Risk: `0.75`
- Medium Risk: `1.00`
- High Risk: `1.30`
- Critical Risk: `1.60`

Portfolio risk-band output:

| risk band | applicants | avg default probability | avg priority score |
| --- | ---: | ---: | ---: |
| Low Risk | 125,098 | 0.1422 | 7.9374 |
| Medium Risk | 97,954 | 0.3646 | 27.0545 |
| High Risk | 53,578 | 0.5953 | 57.1230 |
| Critical Risk | 30,881 | 0.7810 | 91.6985 |

## Business Impact Evaluation

Estimate how many defaults and how much credit-exposure proxy the model-ranked queue captures at different review capacities:

```bash
python src/business/business_impact.py
```

The command writes `reports/business_impact_by_threshold.csv` and `reports/business_impact_summary.md`. It uses actual labels and `AMT_CREDIT` as an exposure proxy, without inventing loss-given-default or recovery-rate assumptions.

Actual review-capacity results:

| review capacity | applicants reviewed | defaults captured | default capture rate | lift vs random |
| --- | ---: | ---: | ---: | ---: |
| Top 5% | 15,376 | 6,715 | 27.05% | 5.41x |
| Top 10% | 30,752 | 10,853 | 43.72% | 4.37x |
| Top 15% | 46,127 | 14,029 | 56.51% | 3.77x |
| Top 20% | 61,503 | 16,376 | 65.97% | 3.30x |

At a 10% review capacity, the model-ranked queue captures `43.72%` of observed defaults, compared with about `10%` expected from random review.

## API Instructions

Start the FastAPI service locally:

```bash
uvicorn src.api.main:app --reload
```

Open the local API documentation:

```text
http://127.0.0.1:8000/docs
```

Endpoints:

- `GET /`
- `GET /health`
- `POST /predict`
- `POST /batch_predict`
- `POST /explain`
- `GET /model_info`

Docker:

```bash
docker build -t finsight-credit-risk .
docker run -p 8000:8000 finsight-credit-risk
```

The API loads `models/credit_risk_model.pkl`; it does not retrain the model.

## Batch Scoring And Prediction Logging

Run production-style batch scoring and privacy-safe audit-log generation:

```bash
python src/api/batch_score.py --input data/processed/model_features.parquet --limit 1000
```

The command writes:

- `reports/batch_scoring_sample.csv`
- `reports/prediction_audit_log_sample.csv`
- `reports/batch_scoring_schema.json`
- `reports/batch_scoring_summary.md`

The batch scoring layer validates the serving schema, logs model name, model version, model stage, feature count, schema version, request IDs, batch ID, score timestamp, risk band, operational threshold flag, collections priority score, and reason-code fields. The committed audit sample is privacy-safe: applicant identifiers are hashed, raw model feature values are not written, and production log folders are ignored by Git.

Current sample run: `1,000` rows scored, `76` required features validated, `0` missing required features, `0` non-numeric required features, and schema validation status `passed`.

## Monitoring Summary

The monitoring phase simulates production by splitting the processed dataset into a reference window and a current window, scoring both windows with the saved model, and comparing feature distributions, missingness, prediction distributions, and labeled performance.

Monitoring results:

- Reference rows: `153,755`
- Current rows: `153,756`
- Features with PSI >= 0.2: `0`
- Features with missingness-rate change >= 5%: `0`
- Prediction PSI: `0.000117`
- Reference ROC-AUC: `0.8455`
- Current ROC-AUC: `0.8432`
- Current PR-AUC: `0.3490`
- Current Recall@Top-10%: `0.4341`

The implementation uses a lightweight custom fallback report because it is stable in the local environment. Evidently is available, but the fallback avoids version-specific API issues.

## Model Governance

FinSight includes a professional model card and deployment governance checklist:

- `reports/model_card.md`
- `reports/governance_checklist.md`
- `reports/fair_lending_review.md`
- `reports/proxy_feature_controls.csv`
- `reports/challenger_governance_report.md`
- `reports/challenger_model_comparison.csv`
- `reports/batch_scoring_summary.md`
- `reports/prediction_audit_log_sample.csv`

The model card documents intended use, prohibited use, training data, feature groups, validation metrics, calibration, SHAP explainability, proxy-risk findings, leakage audit results, monitoring plan, limitations, and deployment readiness. The governance checklist translates those sections into concrete production controls for data, features, model validation, fairness review, API deployment, monitoring, rollback, and sign-off. The fair-lending review adds segment-risk interpretation and protected/proxy feature controls without claiming legal certification. The batch scoring artifacts show how prediction logging would capture model metadata and audit fields without exposing raw feature values.

Current governance position: FinSight is a portfolio-ready production-style prototype. It is not production-approved for automated credit decisions without business, risk, legal, compliance, data governance, and MLOps review.

## Dashboard Instructions

This repo currently uses Power BI-ready CSV outputs instead of Streamlit. Streamlit is not required for the project to be portfolio-ready.

Build dashboard files:

```bash
python dashboard/build_dashboard_data.py
```

Generated files under `dashboard/dashboard_data/`:

- `kpi_summary.csv`
- `risk_band_distribution.csv`
- `collections_priority.csv`
- `model_performance.csv`
- `top_model_features.csv`
- `high_risk_segments.csv`
- `monitoring_summary.csv`

Recommended dashboard pages:

- Executive KPIs
- Default risk distribution
- Risk band distribution
- Collections priority queue
- High-risk applicant segments
- Model performance
- Top model features
- Monitoring and drift summary

## Project Structure

```text
FinSight_Credit_Risk_ML/
├── data/
│   ├── raw/                  # local raw CSVs, ignored by Git
│   └── processed/            # derived datasets, ignored by Git
├── notebooks/                # EDA notebooks
├── src/
│   ├── data/                 # data loading, EDA, SQL/DuckDB setup
│   ├── features/             # PySpark feature engineering
│   ├── models/               # training, metrics, prediction utility
│   ├── explainability/       # SHAP and reason codes
│   ├── business/             # collections scoring
│   ├── monitoring/           # drift and quality reports
│   └── api/                  # FastAPI app
├── sql/                      # business SQL queries
├── dashboard/                # dashboard data builder and CSV outputs
├── reports/                  # markdown, CSV, figures, and HTML reports
│   ├── final_project_audit.md
│   ├── model_card.md
│   └── governance_checklist.md
├── models/                   # trained model artifacts, ignored by Git
├── tests/
├── .github/                  # CI, issue templates, PR template
├── Dockerfile
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
├── FINAL_SUBMISSION.md
├── REVIEW_GUIDE.md
├── RELEASE_CHECKLIST.md
├── PROJECT_BRIEF.md
├── ROADMAP.md
└── README.md
```

## How To Run

Create and activate the environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run each phase from the VS Code terminal:

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

Useful checks:

```bash
python -m compileall src dashboard tests
python src/models/predict.py --input data/processed/model_features.parquet --limit 5
```

## Repository Quality

The repository includes lightweight CI and local quality commands for GitHub readiness:

```bash
make check
```

This runs:

- `python -m compileall src dashboard tests`
- `pytest -q`

GitHub Actions runs the same checks on pushes and pull requests to `main`.
The test suite covers repository hygiene, raw-data validation helpers, model metrics,
collections scoring logic, prediction utilities, and FastAPI endpoints with a mocked
model service so CI does not require private raw data or trained model artifacts.

## Repository Maintenance

The repo includes standard GitHub maintenance files:

- `LICENSE`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/ISSUE_TEMPLATE/`

These files document how the project should be reviewed, changed, and shared without exposing raw data, model artifacts, secrets, or unsupported production claims.

## Governance Artifacts

For senior-review or interview discussion, start with:

- `FINAL_SUBMISSION.md`
- `REVIEW_GUIDE.md`
- `reports/final_project_audit.md`
- `reports/feature_registry.md`
- `reports/reject_inference_note.md`
- `reports/fair_lending_review.md`
- `reports/proxy_feature_controls.csv`
- `reports/challenger_governance_report.md`
- `reports/challenger_model_comparison.csv`
- `reports/batch_scoring_summary.md`
- `reports/batch_scoring_schema.json`
- `reports/prediction_audit_log_sample.csv`
- `reports/mlflow_experiment_summary.md`
- `reports/model_registry.md`
- `reports/model_card.md`
- `reports/governance_checklist.md`
- `reports/final_case_study.md`
- `reports/leakage_audit.md`
- `reports/fairness_proxy_analysis.md`
- `RELEASE_CHECKLIST.md`
- `CHANGELOG.md`

## Resume-Ready Impact Bullets

- Built FinSight, an end-to-end credit-risk and collections ML platform using PySpark, SQL, scikit-learn, XGBoost/LightGBM, SHAP, FastAPI, and Docker to predict loan default probability and prioritize high-risk applicants.
- Engineered lending-risk features including credit-to-income ratio, annuity burden, employment stability, external score aggregates, repayment behavior, and bureau-history signals using PySpark pipelines.
- Validated models using ROC-AUC, PR-AUC, Recall@Top-K, KS statistic, calibration curves, and confusion-matrix analysis to select a production-ready credit-risk model.
- Added SHAP-based reason codes and dashboard-ready risk outputs to explain applicant-level default drivers for lending and collections decisions.
- Implemented monitoring reports to track data drift, prediction drift, feature quality, and model performance degradation across simulated production batches.

## Limitations

- The project uses the public Home Credit dataset, not live Navi data or production credit bureau feeds.
- Monitoring is simulated by splitting historical processed data into reference and current windows.
- SHAP applicant-level reason codes are generated for a sample to keep local runtime practical.
- Raw probabilities need further calibration and policy review before use as automated decision thresholds.
- Formal legal fair-lending certification, adverse-action compliance approval, regulatory sign-off, and applied reject inference with compliant rejected-applicant outcomes are outside this portfolio scope but would be required for production deployment.

## Current Status

The full portfolio workflow is implemented: scaffold, data validation, EDA, SQL analysis, PySpark feature engineering, baseline and final modeling, explainability, collections scoring, FastAPI serving, monitoring, dashboard-ready outputs, fair-lending/proxy-risk governance, repository maintenance, reviewer handoff, and final audit documentation.
