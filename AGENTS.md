# AGENTS.md

## Role

You are helping build a portfolio-grade Data Science project for a junior Data Scientist role at Navi, a fintech company.

## Project Name

FinSight — Explainable Credit Risk & Collections ML Platform

## Main Goal

Build an end-to-end machine learning platform that predicts loan default probability, explains risk drivers, ranks customers for collections priority, serves predictions through an API, and generates monitoring reports for model/data drift.

## Target Skills to Demonstrate

* Python
* SQL
* PySpark
* pandas
* scikit-learn
* XGBoost or LightGBM
* SHAP explainability
* FastAPI
* Docker
* model validation
* model monitoring
* credit risk modeling
* collections prioritization
* business-focused data science

## Engineering Rules

* Use Python 3.10+.
* Write clean, modular, production-style code.
* Do not modify raw data files.
* Do not commit raw data or processed data.
* Save processed files under `data/processed/`.
* Save trained models under `models/`.
* Save reports under `reports/`.
* Use relative paths only.
* Avoid hard-coded local machine paths.
* Every major script should be runnable from the command line.

## Data Science Rules

* Do not use accuracy as the main metric.
* Track ROC-AUC, PR-AUC, Precision, Recall, F1-score, Recall@Top-K, KS statistic, confusion matrix, and calibration.
* Handle class imbalance properly.
* Check for data leakage before modeling.
* Use SHAP for explainability.
* Use PySpark for feature engineering.
* Use SQL for business analysis.
* Use Evidently or a lightweight fallback for monitoring.
* Do not invent fake metrics.

## Expected Repository Structure

FinSight-Credit-Risk-ML/
├── data/
│   ├── raw/
│   ├── processed/
├── notebooks/
├── src/
│   ├── data/
│   ├── features/
│   ├── models/
│   ├── explainability/
│   ├── business/
│   ├── monitoring/
│   └── api/
├── sql/
├── dashboard/
├── reports/
├── models/
├── tests/
├── README.md
├── PROJECT_BRIEF.md
├── ROADMAP.md
├── requirements.txt
├── Dockerfile
└── AGENTS.md

## Definition of Done

A task is complete only when:

* Code runs without syntax errors.
* Outputs are saved in the correct folders.
* README or related documentation is updated.
* Assumptions are documented.
* Results are reproducible.
* The implementation improves the project’s value for a fintech Data Scientist I role.
