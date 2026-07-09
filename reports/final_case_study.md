# FinSight Final Case Study

## Problem Statement

FinSight simulates a fintech credit-risk workflow for predicting loan default, explaining applicant-level risk, and prioritizing collections actions. The business goal is to help lending and collections teams identify high-risk applicants, understand the drivers behind risk, and monitor whether model inputs and predictions remain stable over time.

The project is framed for a Data Scientist I role at Navi, where the work should show practical credit-risk modeling, SQL analysis, PySpark feature engineering, model validation, explainability, API deployment, monitoring, and business communication.

## Data Used

The project uses the Home Credit Default Risk dataset stored locally under `data/raw/`. Raw data is read only and ignored by Git.

Source tables used:

- `application_train.csv` as the base applicant table
- `bureau.csv`
- `bureau_balance.csv`
- `previous_application.csv`
- `installments_payments.csv`
- `POS_CASH_balance.csv`
- `credit_card_balance.csv`
- `HomeCredit_columns_description.csv`

The base application table contains `307,511` rows and `122` columns. The target is `TARGET`, where the positive class represents default. The observed default rate in the base table is `8.07%`, so the modeling workflow treats this as an imbalanced binary classification problem.

## Methodology

### Data Validation and EDA

The data-loading layer validates required raw files, detects the target column, summarizes shape, missingness, target distribution, and data types, and writes a schema report. EDA focuses on business patterns such as target imbalance, missing-value structure, income, credit amount, annuity burden, age, employment duration, external scores, and segment-level default rates.

### SQL Business Analysis

DuckDB is used to run business-readable SQL analyses over `application_train.csv`. The SQL layer computes default rates by income bucket, education type, credit amount bucket, occupation type, and combined high-risk segments. The analysis showed, for example, elevated default rates for Lower secondary education, Low-skill Laborers, and some lower-income credit segments.

### PySpark Feature Engineering

PySpark aggregates raw Home Credit tables to applicant level. The final model dataset contains `307,511` rows and `78` columns. Features include affordability ratios, employment and age transformations, external score aggregates, missingness counts, bureau credit history, prior application behavior, installment payment delay signals, POS delinquency signals, credit card balance signals, and encoded categorical fields.

### Modeling

The modeling pipeline uses stratified train/validation/test splits. Class imbalance is handled with balanced class weights or `scale_pos_weight`, depending on the model. Accuracy is intentionally not used as the main selection metric. Baselines include Logistic Regression, Random Forest, XGBoost, and LightGBM. LightGBM was selected as the final model because it had the strongest validation PR-AUC among the baselines.

### Explainability

SHAP is used for global and applicant-level explanation. Global SHAP identifies the model's most influential features, and applicant-level reason codes translate positive SHAP contributors into business-readable drivers such as low external credit score, annuity burden, prior refused application history, bureau debt burden, and repayment delay.

### Collections Scoring

The final model predictions are converted into four risk bands: Low Risk, Medium Risk, High Risk, and Critical Risk. A collections priority score combines default probability, normalized credit amount, and a risk-band weight so collections teams can rank cases by both risk and exposure.

### API, Monitoring, and Dashboard

FastAPI serves `/health`, `/predict`, `/explain`, and `/model_info` endpoints from the saved model. Monitoring simulates production with reference and current windows and checks data drift, prediction drift, missingness changes, and labeled performance. Dashboard-ready CSV files are generated for Power BI to support business-facing review.

## Model Validation

Final model: tuned LightGBM classifier.

| split | ROC-AUC | PR-AUC | Precision | Recall | F1 | Recall@Top-10% | KS | Brier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| validation | 0.7799 | 0.2712 | 0.2941 | 0.3644 | 0.3255 | 0.3644 | 0.4194 | 0.1643 |
| test | 0.7765 | 0.2640 | 0.2908 | 0.3577 | 0.3208 | 0.3593 | 0.4123 | 0.1645 |

The final model uses validation PR-AUC as the selection metric because the default class is rare and the business need is to rank risky applicants. The top-10% risk threshold captures a materially higher share of defaults than random review, making the model useful for prioritization workflows. Calibration should be reviewed before raw probabilities are used for hard policy decisions.

The selected LightGBM configuration was also checked with stratified 5-fold cross-validation on the full processed dataset. Cross-validation mean metrics were ROC-AUC `0.7830`, PR-AUC `0.2745`, Recall@Top-10% `0.3646`, and KS statistic `0.4276`. The low fold-to-fold variation supports the model's use as a stable ranking baseline, while still leaving room for calibration, fairness, and cost-sensitive threshold work before production deployment.

Calibration analysis compared raw LightGBM probabilities against Platt/sigmoid and isotonic calibration fitted on the validation split. On the test split, Platt/sigmoid improved Brier score from `0.1645` to `0.0669` and expected calibration error from `0.2742` to `0.0062` while preserving ROC-AUC, PR-AUC, and Recall@Top-10%. Isotonic produced the lowest test Brier score at `0.0668`, but slightly reduced PR-AUC and Recall@Top-10%, so Platt/sigmoid is the cleaner balanced choice for calibrated probability reporting.

## Business Impact

FinSight turns a credit-risk model into a business workflow:

- Credit teams can inspect default drivers and high-risk segments.
- Collections teams receive ranked applicant queues with risk bands and priority scores.
- Data scientists can reproduce feature engineering, training, validation, explanation, and monitoring from command-line scripts.
- Stakeholders can review Power BI-ready dashboard files showing portfolio risk, model performance, SHAP drivers, and monitoring health.

Portfolio risk-band output from the collections layer:

| risk band | applicants | avg default probability | avg priority score |
| --- | ---: | ---: | ---: |
| Low Risk | 125,098 | 0.1422 | 7.9374 |
| Medium Risk | 97,954 | 0.3646 | 27.0545 |
| High Risk | 53,578 | 0.5953 | 57.1230 |
| Critical Risk | 30,881 | 0.7810 | 91.6985 |

Business impact analysis evaluates model-ranked review queues at different capacity levels. At a `10%` review capacity, the queue contains `30,752` applicants and captures `10,853` observed defaults, or `43.72%` of all defaults. That is `4.37x` the capture expected from random review at the same capacity. At a `20%` review capacity, the queue captures `65.97%` of observed defaults. These values are based on actual labels and model scores, while `AMT_CREDIT` is used only as an exposure proxy rather than a realized loss estimate.

Fairness and proxy-risk analysis was added to inspect segment-level model behavior. The current run used processed encoded category proxies because raw application category files were not available locally. The highest top-10% review-rate segment was `OCCUPATION_TYPE_idx=13` at `32.11%`, and age band `18-25` had a top-10% review rate of `22.50%`. Encoded gender proxy `CODE_GENDER_idx=1` had a top-10% review rate of `14.03%` versus `7.91%` for `CODE_GENDER_idx=0`. These gaps should be treated as review signals, not conclusions of bias or compliance failure.

Monitoring output shows stable simulated production windows for this run:

- Features with PSI >= 0.2: `0`
- Features with missingness-rate change >= 5%: `0`
- Prediction PSI: `0.000117`
- Current window ROC-AUC: `0.8432`
- Current window PR-AUC: `0.3490`

## Limitations

- The dataset is public and historical, not live production data.
- The monitoring phase simulates production using a historical split rather than real serving logs.
- SHAP explanations are generated on a sample to keep local runtime practical.
- Categorical encoding uses index-style preparation; further production work should validate category stability and unseen-category handling.
- Probability calibration needs additional review before probabilities are used as policy thresholds.
- The project does not include reject inference, adverse action compliance review, formal fair-lending certification, or production cost optimization.
- Fairness analysis is proxy-based and not a legal fair-lending audit.

## Future Improvements

- Add robust automated tests around feature contracts, prediction schemas, and monitoring thresholds.
- Add a Streamlit dashboard or a Power BI template file on top of the dashboard-ready CSV outputs.
- Extend proxy fairness checks into a formal fair-lending review workflow with governance and compliance input.
- Add probability calibration experiments and cost-sensitive threshold optimization.
- Add model registry-style versioning and batch scoring logs.
- Extend monitoring with production event logs, alert thresholds, and scheduled retraining recommendations.
- Add CI checks before GitHub pushes to run formatting, compile checks, and smoke tests.
