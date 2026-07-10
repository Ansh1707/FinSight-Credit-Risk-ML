# FinSight Executive Summary

## One-Line Pitch

FinSight is an end-to-end credit-risk and collections ML platform that predicts loan default risk, explains applicant-level drivers, prioritizes review queues, serves scores through an API, monitors drift, and documents model governance for a fintech Data Scientist I role.

## 2-Minute Recruiter Pitch

I built FinSight to show the full workflow a fintech data scientist needs beyond a notebook model. The project uses the Home Credit Default Risk dataset to predict default probability and turn that score into useful business outputs for lending and collections teams.

The workflow includes SQL analysis, PySpark feature engineering, LightGBM modeling, SHAP explainability, collections priority scoring, FastAPI serving, batch scoring, monitoring, dashboard-ready outputs, and production-style governance documentation.

The final tuned LightGBM model reaches test ROC-AUC `0.7765`, PR-AUC `0.2640`, Recall@Top-10% `0.3593`, and KS `0.4123`. At a `10%` review capacity, the model-ranked queue captures `43.72%` of observed defaults, a `4.37x` lift over random review.

What makes it portfolio-ready for Navi is the fintech framing: I did not optimize for accuracy, I handled imbalance, added calibration, leakage checks, SHAP reason codes, monitoring, reject-inference documentation, fair-lending/proxy-risk review, challenger-model governance, batch prediction logging, and a production readiness runbook.

## 5-Minute Hiring Manager Pitch

FinSight starts with a lending business problem: a digital lender needs to identify higher-risk applicants, explain the reason for risk, and prioritize limited review or collections capacity.

The data layer validates the Home Credit raw files and keeps raw data out of Git. EDA and SQL analysis explore default behavior by income, education, credit amount, occupation, and other lending-relevant segments. The feature layer uses PySpark to aggregate application, bureau, bureau balance, previous application, installment, POS cash, and credit-card tables to an applicant-level modeling table.

The modeling layer uses a stratified train/validation/test split and evaluates Logistic Regression, Random Forest, XGBoost, and LightGBM. LightGBM is selected by validation PR-AUC because this is an imbalanced ranking problem, not an accuracy problem. The final model is validated with ROC-AUC, PR-AUC, Precision, Recall, F1, Recall@Top-10%, KS, confusion matrix, cross-validation, and calibration.

The business layer converts predictions into risk bands and a collections priority score. The strongest business result is that the model-ranked top `10%` queue captures `43.72%` of observed defaults, or `4.37x` random capture at the same capacity.

The explainability layer uses SHAP for global feature importance and applicant-level reason codes. The API layer exposes local FastAPI endpoints for health, prediction, explanation, batch prediction, and model metadata. Batch scoring adds request IDs, batch IDs, score timestamps, model version, schema validation, hashed applicant IDs, risk bands, priority scores, and reason-code fields.

The governance layer is where the project becomes stronger than a normal Kaggle project. It includes a feature registry with timestamp-lineage assumptions, leakage audit, model card, MLflow/registry-style documentation, reject-inference methodology, fair-lending/proxy-risk review, protected/proxy feature controls, a less-sensitive challenger model comparison, and a production readiness runbook covering deployment, monitoring, alert thresholds, rollback, incident response, retraining triggers, ownership, and sign-off.

The honest limitation is that this is a public historical dataset, not Navi production data. It is portfolio-ready, not production-approved. Real deployment would require live data contracts, legal fair-lending certification, adverse-action approval, secure infrastructure, production monitoring, and compliance sign-off.

## Deep-Dive Narrative

### Business Problem

The project is framed around credit risk and collections prioritization. The goal is not simply to predict a label; it is to help a lender decide which applicants or accounts deserve review attention, why the model thinks they are risky, and how the model would be monitored and governed.

### Data And Feature Engineering

The dataset is the Home Credit Default Risk dataset. The base label is `TARGET`, where `1` means observed default. Raw and processed data are ignored by Git.

PySpark builds the applicant-level feature table with `307,511` rows and `78` columns. The final model uses `76` input features. Feature groups include affordability ratios, applicant stability, external credit score aggregates, missingness, bureau history, previous application history, repayment behavior, POS cash behavior, credit-card behavior, and encoded categoricals.

### Modeling And Validation

The final champion model is tuned LightGBM selected by validation PR-AUC. Accuracy is intentionally not the main metric because default is rare and the use case is ranking and prioritization.

| metric | value |
| --- | ---: |
| Test ROC-AUC | `0.7765` |
| Test PR-AUC | `0.2640` |
| Test Recall@Top-10% | `0.3593` |
| Test KS statistic | `0.4123` |
| Cross-validation ROC-AUC mean | `0.7830` |
| Cross-validation PR-AUC mean | `0.2745` |
| Platt/sigmoid test Brier score | `0.0669` |
| Platt/sigmoid test ECE | `0.0062` |

### Business Impact

At `10%` review capacity, the model reviews `30,752` applicants and captures `10,853` observed defaults. That is `43.72%` of all defaults and `4.37x` the expected capture from random review. This converts model ranking into a business capacity story.

### Explainability

SHAP is used for global feature importance and applicant-level reason codes. Reason-code examples include low external credit score, high credit-to-income ratio, short employment duration, high annuity burden, missing bureau signal, prior repayment delay, and prior refused application history.

### Governance And Production Readiness

The project includes:

- `reports/model_card.md`
- `reports/governance_checklist.md`
- `reports/feature_registry.md`
- `reports/leakage_audit.md`
- `reports/reject_inference_note.md`
- `reports/fair_lending_review.md`
- `reports/proxy_feature_controls.csv`
- `reports/challenger_governance_report.md`
- `reports/batch_scoring_summary.md`
- `reports/production_readiness_runbook.md`

The less-sensitive challenger removes `15` controlled features and uses `61` lower-risk features. Its test PR-AUC is `0.2559` and Recall@Top-10% is `0.3488`, compared with champion PR-AUC `0.2640` and Recall@Top-10% `0.3593`. That shows a modest predictive tradeoff for lower proxy-risk exposure.

## Strongest Evidence

| evidence | why it matters |
| --- | --- |
| PySpark feature engineering | Shows scalable multi-table lending feature work |
| SQL analysis | Shows ability to analyze lending risk outside Python notebooks |
| PR-AUC, Recall@Top-10%, KS | Shows rare-event ranking validation instead of accuracy chasing |
| Business impact at 10% review capacity | Connects ML to collections team capacity |
| SHAP reason codes | Makes model output explainable to analysts |
| Leakage audit and feature registry | Shows production-style feature governance |
| Reject inference note | Shows awareness of accepted-applicant bias |
| Fair-lending/proxy-risk review | Shows regulated-finance judgment without overstating certification |
| Challenger model | Quantifies predictive lift versus proxy-risk controls |
| Batch scoring audit sample | Shows how predictions would be logged safely |
| Production readiness runbook | Shows lifecycle thinking beyond training |

## Honest Limitations

- This is a portfolio prototype, not a production-approved lending system.
- The dataset is public and historical, not Navi production data.
- Rejected-applicant outcomes are unavailable, so reject inference is documented but not applied.
- Formal legal fair-lending certification and adverse-action approval are outside scope.
- Historical aggregate features require enforced timestamp cutoffs in production.
- Monitoring is simulated, not based on live production windows.
- API deployment is local/demo-grade and would need authentication, logging infrastructure, and access controls.

## Resume Positioning

Use this project as the flagship fintech ML project. The strongest resume angle is not only that a model was trained, but that the project covers credit-risk modeling, collections prioritization, explainability, monitoring, governance, and production readiness.
