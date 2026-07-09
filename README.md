# FinSight: Explainable Credit Risk & Collections ML Platform

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![CI](https://img.shields.io/badge/CI-GitHub%20Actions-green)
![Model](https://img.shields.io/badge/Model-LightGBM-orange)
![API](https://img.shields.io/badge/API-FastAPI-teal)
![Status](https://img.shields.io/badge/Status-Portfolio%20Ready-brightgreen)

FinSight is an end-to-end fintech data science project for credit default prediction, explainable risk review, collections prioritization, API serving, model monitoring, and dashboard-ready reporting. It is designed as a portfolio project for a Navi Data Scientist I application.

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

## Modeling Approach

The project creates a stratified train/validation/test split and handles class imbalance using class weights or `scale_pos_weight`. Accuracy is not used as the primary metric because defaults are rare and the business task is risk ranking.

Baseline models trained:

- Logistic Regression
- Random Forest
- XGBoost
- LightGBM

LightGBM was selected as the final model because it produced the strongest validation PR-AUC among the baselines. The final model was tuned using validation PR-AUC as the selection metric.

## Final Metrics

Final model: tuned LightGBM classifier.

| split | ROC-AUC | PR-AUC | Precision | Recall | F1 | Recall@Top-10% | KS | Brier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| validation | 0.7799 | 0.2712 | 0.2941 | 0.3644 | 0.3255 | 0.3644 | 0.4194 | 0.1643 |
| test | 0.7765 | 0.2640 | 0.2908 | 0.3577 | 0.3208 | 0.3593 | 0.4123 | 0.1645 |

Operational threshold: validation top `10%` risk cutoff at score `0.697372`.

The model is best interpreted as a risk-ranking and prioritization model. Calibration should be reviewed before using raw probabilities for strict policy thresholds.

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
├── models/                   # trained model artifacts, ignored by Git
├── tests/
├── Dockerfile
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
python src/models/train_baseline.py
python src/models/train_final_model.py
python src/models/cross_validate_model.py
python src/models/calibrate_model.py
python src/explainability/shap_reason_codes.py
python src/business/collections_scoring.py
python src/business/business_impact.py
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
- Fair lending, regulatory compliance, and reject-inference analysis are outside this portfolio scope but would be required for production deployment.

## Current Status

The full portfolio workflow is implemented: scaffold, data validation, EDA, SQL analysis, PySpark feature engineering, baseline and final modeling, explainability, collections scoring, FastAPI serving, monitoring, dashboard-ready outputs, and final documentation.
