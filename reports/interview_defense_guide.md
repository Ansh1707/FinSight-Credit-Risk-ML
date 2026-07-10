# FinSight Interview Defense Guide

This guide helps defend FinSight in a Navi Data Scientist I interview. Use it to answer quickly, stay honest about limitations, and connect technical decisions to fintech business value.

## 2-Minute Answer

FinSight is my end-to-end credit-risk and collections ML platform. I used the Home Credit Default Risk dataset to predict default probability, explain risk drivers, prioritize applicants for review or collections, expose predictions through FastAPI, and monitor the model.

Technically, I built data validation, EDA, SQL analysis, PySpark feature engineering, baseline and final modeling, SHAP explainability, collections scoring, API serving, batch scoring, monitoring, and dashboard-ready outputs.

The final LightGBM model achieved test ROC-AUC `0.7765`, PR-AUC `0.2640`, Recall@Top-10% `0.3593`, and KS `0.4123`. At a `10%` review capacity, it captured `43.72%` of observed defaults, which is a `4.37x` lift over random review.

The project is stronger than a typical notebook because I added governance: leakage audit, feature registry, calibration, MLflow-style registry docs, reject-inference note, fair-lending/proxy-risk review, challenger model, privacy-safe batch prediction logging, and a production readiness runbook.

## 5-Minute Answer

I framed the project around a real fintech workflow: a lender wants to rank applicants by default risk, explain the drivers, and prioritize review capacity. I intentionally did not make this a Kaggle submission project.

I used `application_train.csv` as the base table and aggregated bureau, bureau balance, previous application, installment, POS cash, and credit-card tables to applicant level using PySpark. I created features for affordability, employment stability, external credit scores, bureau history, previous applications, repayment behavior, and categorical application fields.

For modeling, I trained Logistic Regression, Random Forest, XGBoost, and LightGBM baselines and selected tuned LightGBM by validation PR-AUC. I used PR-AUC, Recall@Top-10%, and KS because the default class is imbalanced and the business task is ranking applicants for review, not maximizing accuracy.

The business translation is the top-decile review result: reviewing the top `10%` of applicants by model score captures `43.72%` of defaults, a `4.37x` lift versus random review. I also added SHAP reason codes so analysts can understand why an applicant is high risk.

I then added production-style controls: feature registry, timestamp-lineage assumptions, leakage audit, calibration report, monitoring report, FastAPI, batch scoring logs, model registry documentation, model card, governance checklist, fair-lending/proxy-risk review, less-sensitive challenger model, and production readiness runbook.

The honest limitation is that this is a public historical dataset. It is not production-approved and does not include real Navi data, legal fair-lending certification, adverse-action approval, or applied reject inference using compliant rejected-applicant outcomes.

## Deep-Dive Defense Map

| topic | crisp defense |
| --- | --- |
| Why this project | It maps directly to fintech lending: default risk, collections prioritization, explainability, monitoring, and governance. |
| Why not accuracy | Default is imbalanced; accuracy can be high while missing risky applicants. PR-AUC, Recall@Top-K, and KS are better for ranking. |
| Why LightGBM | It performed best by validation PR-AUC and handles nonlinear tabular risk patterns well. |
| Why Recall@Top-10% | It maps model output to review capacity: if a team can review 10% of applicants, how many defaults are captured? |
| Why SHAP | It turns model signals into explainable global drivers and applicant-level reason codes for analyst review. |
| Why feature registry | Credit-risk models need lineage: source table, transformation, availability time, leakage risk, and owner. |
| Why leakage audit | Historical repayment and bureau features can leak post-decision information if timestamps are not controlled. |
| Why reject inference note | The model is trained on observed accepted/booked applicants; rejected applicants lack repayment outcomes. |
| Why fair-lending review | Credit models can use protected or proxy-sensitive attributes; segment gaps need governance review. |
| Why challenger model | It quantifies the predictive cost of removing high-risk protected/proxy features. |
| Why batch logging | Production scores need request IDs, timestamps, model version, schema version, risk bands, and privacy-safe auditability. |
| Why runbook | A production model needs deployment, monitoring, rollback, incident response, retraining triggers, and sign-off. |

## Likely Interview Questions And Answers

### 1. Why did you use PR-AUC instead of accuracy?

Defaults are rare, so accuracy can look good even if the model fails to identify risky applicants. PR-AUC focuses on the positive default class, and Recall@Top-10% maps directly to review capacity. That is more relevant for lending and collections.

### 2. What does Recall@Top-10% mean here?

It means: if the business reviews the highest-scored `10%` of applicants, what fraction of all observed defaults are captured? In this project, the top `10%` captures `43.72%` of defaults in the business impact analysis.

### 3. Why is KS useful in credit risk?

KS measures separation between the cumulative score distributions of defaulters and non-defaulters. Credit-risk teams often use it because it directly summarizes rank separation. The final test KS is `0.4123`.

### 4. Why did LightGBM win?

LightGBM handled nonlinear interactions across affordability, bureau, repayment, and external score features better than simpler baselines. It was selected by validation PR-AUC, not accuracy.

### 5. How did you handle class imbalance?

The baseline and final models use class weighting or `scale_pos_weight` based on the training split. Evaluation focuses on PR-AUC, Recall@Top-K, KS, and confusion matrix rather than accuracy.

### 6. What are the strongest model metrics?

The final test metrics are ROC-AUC `0.7765`, PR-AUC `0.2640`, Recall@Top-10% `0.3593`, and KS `0.4123`. Cross-validation mean ROC-AUC is `0.7830` and mean PR-AUC is `0.2745`.

### 7. What is the business impact?

At `10%` review capacity, the model-ranked queue captures `43.72%` of observed defaults, which is `4.37x` random review. That translates model ranking into collections or manual review capacity.

### 8. How did you prevent data leakage?

I excluded target and identifier fields from model inputs and added a leakage audit. The audit found `0` forbidden target/identifier inputs and `0` high-risk outcome-keyword features. It flagged `32` historical aggregates as medium-risk timing assumptions that need production timestamp controls.

### 9. What are the biggest leakage risks?

Historical bureau, installment, POS cash, credit-card, and previous application aggregates are useful but timing-sensitive. In production, each source record must be filtered to only what was available before the decision or scoring timestamp.

### 10. What are the top risk drivers?

The SHAP report highlights external credit score aggregates, annuity burden, credit/goods price ratios, POS cash history, education encoding, repayment delay, and gender proxy signals. The proxy signals are useful for review but need governance before production use.

### 11. How do reason codes work?

SHAP reason codes map top positive feature contributions into business-readable explanations, such as low external credit score, high credit-to-income ratio, high annuity burden, short employment duration, missing bureau signal, prior repayment delay, or prior refused application history.

### 12. Can these reason codes be used for adverse action?

No, not as-is. They are analyst-facing portfolio reason codes. Customer-facing adverse-action reasons require legal and compliance approval.

### 13. What is reject inference, and why does it matter?

Reject inference addresses the fact that rejected applicants usually do not have observed repayment outcomes. The model is trained on accepted/booked applicants, so validation metrics are conditional on that observed population. I documented methods like parceling, fuzzy augmentation, bureau outcome matching, and controlled exploration, but I did not invent rejected-applicant labels.

### 14. What did the fair-lending/proxy-risk review find?

It found segment review-rate gaps across age, occupation, family status, and encoded gender proxy groups. For example, `OCCUPATION_TYPE_idx=13` had top-10% review rate `32.11%`, and encoded gender proxy `CODE_GENDER_idx=1` had `14.03%` versus `7.91%` for `CODE_GENDER_idx=0`. These are review triggers, not legal conclusions.

### 15. Why did you train a less-sensitive challenger model?

To quantify the tradeoff between predictive lift and proxy-risk exposure. The challenger removed `15` controlled features and used `61` lower-risk features. PR-AUC moved from `0.2640` to `0.2559`, and Recall@Top-10% moved from `0.3593` to `0.3488`. That is a modest performance loss for lower proxy-risk exposure.

### 16. Would you deploy the champion or challenger?

I would not deploy either without formal review. The champion has modestly better ranking, but the challenger reduces protected/proxy feature risk. A real lender should decide with business, risk, fair-lending, legal, and compliance stakeholders.

### 17. What did calibration show?

Raw LightGBM probabilities were not well calibrated. Platt/sigmoid calibration improved test Brier score to `0.0669` and ECE to `0.0062` while preserving ranking metrics. That matters if probabilities feed thresholds or portfolio planning.

### 18. How does monitoring work?

The monitoring script simulates reference and current windows, then checks feature drift, prediction drift, missingness changes, and labeled performance. The latest run found `0` features with PSI >= `0.2` and prediction PSI `0.000117`.

### 19. What would you monitor in production?

I would monitor schema failures, missingness, feature PSI, prediction PSI, score quantiles, segment review rates, reason-code distribution, calibration drift, PR-AUC, Recall@Top-K, KS, and business impact once labels mature.

### 20. What does the batch scoring layer add?

It validates the serving schema and writes privacy-safe prediction logs with request ID, batch ID, score timestamp, model metadata, schema version, hashed applicant ID, default probability, risk band, threshold flag, priority score, and reason-code fields.

### 21. Is the audit log safe to commit?

The sample is privacy-safe because it uses hashed applicant IDs and excludes raw model feature values and unhashed `SK_ID_CURR`. Real production logs should still live outside Git in secure storage.

### 22. What does the production readiness runbook cover?

It covers deployment steps, batch scoring operations, monitoring cadence, alert thresholds, rollback, incident severity, retraining triggers, ownership, and final pre-production sign-off.

### 23. What is the biggest limitation of the project?

It uses public historical data rather than real production lending data. Also, legal fair-lending certification, adverse-action approval, applied reject inference, source-system timestamp enforcement, and live monitoring are outside portfolio scope.

### 24. What would you improve next?

I would add a staging deployment, secured prediction logs, feature-store timestamp enforcement, formal fair-lending review with approved protected-class strategy, applied reject inference if compliant outcomes are available, and live monitoring with alert routing.

### 25. How does this map to Navi Data Scientist I?

It demonstrates credit-risk thinking, SQL, PySpark, model validation, explainability, monitoring, business translation, governance, and honest limitation framing. That combination is much closer to real fintech data science than a model-only notebook.

## Questions To Ask The Interviewer

- How does Navi evaluate credit-risk models beyond aggregate AUC?
- How do data science, credit risk, collections, and compliance collaborate on model thresholds?
- What monitoring signals are most important for Navi's lending models?
- How does Navi approach explainability and reason-code review?
- What does a strong first 90 days look like for a Data Scientist I on a fintech risk team?

## Closing Statement

The main value of FinSight is that it treats credit-risk modeling as a full lifecycle system. It starts with data and modeling, but it also covers explainability, collections impact, API serving, batch scoring, monitoring, governance, and production readiness. That is the kind of judgment I would bring to a fintech Data Scientist I role.
