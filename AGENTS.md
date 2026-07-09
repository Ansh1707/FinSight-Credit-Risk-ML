# AGENTS.md

## Role

You are helping build a portfolio-grade Data Science project for a junior Data Scientist role at Navi, a fintech company. The project must demonstrate credit-risk modeling, collections prioritization, PySpark, SQL, model validation, explainability, deployment, and model monitoring.

## Project Name

FinSight — Explainable Credit Risk & Collections ML Platform

## Main Goal

Build an end-to-end machine learning platform that predicts loan default probability, explains risk drivers, ranks customers for collections priority, serves predictions through an API, and generates monitoring reports for model/data drift.

## Engineering Rules

* Use Python 3.10+.
* Write clean, modular, production-style code.
* Prefer small reusable scripts over one giant notebook.
* Keep notebooks for exploration and reports only.
* Do not modify raw data files.
* Save processed data under `data/processed/`.
* Save trained models under `models/`.
* Save generated reports under `reports/`.
* Use meaningful function names, type hints where useful, and docstrings for important functions.
* Do not hard-code absolute local paths.
* Use environment variables for secrets.
* Do not add unnecessary heavy dependencies.
* Every major script should be runnable from the command line.

## Data Science Rules

* Do not use accuracy as the main metric.
* Track ROC-AUC, PR-AUC, Recall, Precision, F1-score, Recall@Top-K, KS statistic, confusion matrix, and calibration.
* Handle class imbalance properly.
* Check for data leakage before modeling.
* Create business-readable explanations, not only technical outputs.
* Use SHAP for explainability.
* Use PySpark for feature engineering.
* Use SQL for business analysis.
* Use Evidently or an equivalent approach for data drift and model monitoring.

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

A task is done only when:

* Code runs without syntax errors.
* Output files are saved in the expected folder.
* The README or relevant markdown file is updated.
* Important assumptions are documented.
* Any generated metric or result is reproducible.
* The implementation improves the project’s resume value for a Data Scientist I fintech role.
