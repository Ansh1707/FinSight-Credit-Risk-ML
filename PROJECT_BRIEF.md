# PROJECT_BRIEF.md

## Project Title

FinSight — Explainable Credit Risk & Collections ML Platform

## Target Role

Data Scientist I at Navi.

## Why This Project Exists

The target job requires strong Python, SQL, pandas, scikit-learn, TensorFlow/PyTorch familiarity, PySpark/Scala as a plus, data analysis, visualization, machine learning, deep learning, probability, optimization, statistics, model validation, monitoring, and business impact in fintech domains such as lending, collections, KYC, UPI growth, and recommendations.

This project is designed to prove those skills through a realistic credit-risk and collections use case.

## Business Problem

A fintech lending company needs to predict which applicants are likely to default and prioritize high-risk customers for collections or manual review. The model must be accurate, explainable, monitored, and useful to business stakeholders.

## ML Problem

Binary classification:

* Input: customer/application-level loan data
* Output: probability of default
* Target: default / non-default

## Business Outputs

* Default probability
* Risk band: Low, Medium, High, Critical
* Top reason codes for each prediction
* Collections priority score
* Model performance report
* Drift monitoring report
* Dashboard for risk and business teams

## Core Skills to Demonstrate

* Python
* SQL
* PySpark
* pandas
* scikit-learn
* XGBoost or LightGBM
* optional PyTorch/TensorFlow model
* SHAP explainability
* FastAPI
* Docker
* Evidently monitoring
* Power BI or Streamlit dashboard
* Statistical validation
* Business-focused storytelling

## Main Success Metrics

Model metrics:

* ROC-AUC
* PR-AUC
* Recall
* Precision
* F1-score
* Recall@Top-K
* KS statistic
* Calibration curve

Business metrics:

* High-risk applicant identification
* Collections priority ranking
* Expected loss segmentation
* Business-readable reason codes

## Expected Final Resume Bullets

* Built FinSight, an end-to-end credit-risk and collections ML platform using PySpark, SQL, scikit-learn, XGBoost, SHAP, FastAPI, and Docker to predict loan default probability and prioritize high-risk applicants.
* Engineered lending-risk features including credit-to-income ratio, annuity burden, employment stability, external score aggregates, and missingness indicators using PySpark pipelines over application-level loan data.
* Validated classification models using ROC-AUC, PR-AUC, Recall@Top-K, KS statistic, calibration curves, and confusion-matrix analysis to select a production-ready credit-risk model.
* Added SHAP-based reason codes and a dashboard to explain applicant-level risk drivers for lending and collections decision-making.
* Implemented model monitoring to track data drift, prediction drift, feature quality, and model performance degradation across simulated monthly production batches.
