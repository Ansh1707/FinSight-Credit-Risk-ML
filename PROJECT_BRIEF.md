# PROJECT_BRIEF.md

## Project Title

FinSight — Explainable Credit Risk & Collections ML Platform

## Target Role

Data Scientist I at Navi.

## Business Problem

A fintech lending company needs to predict which loan applicants are likely to default and prioritize high-risk customers for manual review or collections. The model must be accurate, explainable, monitored, and useful to business stakeholders.

## ML Problem

Binary classification.

Input:

* customer/application-level loan data
* bureau history
* previous application data
* repayment behavior data

Output:

* probability of default
* risk band
* reason codes
* collections priority score

## Dataset

Use the Home Credit Default Risk dataset.

Assume these files are stored locally under `data/raw/`:

* application_train.csv
* HomeCredit_columns_description.csv
* bureau.csv
* bureau_balance.csv
* previous_application.csv
* installments_payments.csv
* POS_CASH_balance.csv
* credit_card_balance.csv

Do not use `application_test.csv` or `sample_submission.csv`. This is not a Kaggle submission project. Use `application_train.csv` and create our own train/validation/test split.

## Expected Outputs

* EDA report
* SQL business analysis
* PySpark feature engineering pipeline
* model comparison report
* trained credit-risk model
* SHAP reason codes
* collections priority scoring module
* FastAPI inference service
* model monitoring reports
* dashboard or dashboard-ready output
* final README with resume-ready explanation

## Final Project Outputs

The implemented project produces:

* `data/processed/model_features.parquet` with `307,511` applicant rows and `78` columns
* `models/credit_risk_model.pkl` as the final tuned LightGBM model
* `reports/final_model_metrics.json` and `reports/final_model_report.md`
* SHAP plots and applicant-level reason codes under `reports/`
* collections priority outputs under `reports/collections_priority_sample.csv`
* FastAPI service under `src/api/`
* monitoring reports under `reports/monitoring_summary.md`, `reports/monitoring_report.html`, and `reports/drift_report.html`
* Power BI-ready dashboard data under `dashboard/dashboard_data/`

## Success Metrics

Model metrics:

* ROC-AUC
* PR-AUC
* Precision
* Recall
* F1-score
* Recall@Top-K
* KS statistic
* calibration curve

Business outputs:

* risk bands
* top default drivers
* high-risk applicant segments
* collections priority ranking
* monitoring summary

## Final Resume Goal

The final project should support resume bullets showing PySpark, SQL, credit risk modeling, model validation, explainability, FastAPI deployment, and model monitoring.

## Final Model Snapshot

The final tuned LightGBM model was selected by validation PR-AUC.

| split | ROC-AUC | PR-AUC | Precision | Recall | F1 | Recall@Top-10% | KS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| validation | 0.7799 | 0.2712 | 0.2941 | 0.3644 | 0.3255 | 0.3644 | 0.4194 |
| test | 0.7765 | 0.2640 | 0.2908 | 0.3577 | 0.3208 | 0.3593 | 0.4123 |

These metrics are actual computed results from the saved project reports. Accuracy is intentionally not used as the main metric.

## Cross-Validation Snapshot

The final LightGBM configuration was checked with stratified 5-fold validation on the full processed dataset.

| metric | mean | std | min | max |
| --- | ---: | ---: | ---: | ---: |
| ROC-AUC | 0.7830 | 0.0044 | 0.7782 | 0.7893 |
| PR-AUC | 0.2745 | 0.0074 | 0.2651 | 0.2854 |
| Recall@Top-10% | 0.3646 | 0.0074 | 0.3577 | 0.3772 |
| KS statistic | 0.4276 | 0.0104 | 0.4146 | 0.4419 |

## Calibration Snapshot

Calibration was evaluated by fitting Platt/sigmoid and isotonic transforms on the validation split and evaluating on the test split.

| method | test Brier | test ECE | test ROC-AUC | test PR-AUC | test Recall@Top-10% |
| --- | ---: | ---: | ---: | ---: | ---: |
| Uncalibrated | 0.1645 | 0.2742 | 0.7765 | 0.2640 | 0.3593 |
| Platt/sigmoid | 0.0669 | 0.0062 | 0.7765 | 0.2640 | 0.3593 |
| Isotonic | 0.0668 | 0.0023 | 0.7760 | 0.2540 | 0.3547 |

Platt/sigmoid calibration is the preferred balanced option for calibrated probability reporting because it improves Brier score and expected calibration error while preserving the model's ranking metrics.
