# FinSight Model Card

## Model Overview

| field | value |
| --- | --- |
| Project | FinSight — Explainable Credit Risk & Collections ML Platform |
| Model purpose | Credit default risk ranking and collections prioritization |
| Model type | Tuned LightGBM binary classifier |
| Target | `TARGET`, where `1` represents observed default |
| Training artifact | `models/credit_risk_model.pkl` |
| Feature dataset | `data/processed/model_features.parquet` |
| Registry record | `reports/model_registry.md` |
| Feature count | `76` model input features |
| Applicant rows | `307,511` |
| Selection metric | Validation PR-AUC |
| Operational cutoff | Validation top `10%` risk cutoff at score `0.697372` |

This model card documents the current portfolio version of FinSight. It is intended to show production-style model governance practices for a fintech data science workflow. It is not a regulatory approval document.

## Intended Use

FinSight is intended for:

- Ranking applicants or accounts by estimated default risk.
- Supporting manual credit-risk review and collections prioritization.
- Generating applicant-level reason codes for analyst review.
- Producing portfolio monitoring signals for drift, missingness, prediction movement, and labeled performance.
- Demonstrating reproducible data science work for a fintech Data Scientist I role.

Recommended operational interpretation: use the score as a decision-support and queue-prioritization signal, not as a fully automated approval, rejection, or adverse-action rule.

## Not Intended Use

FinSight is not intended for:

- Automatic loan approval or rejection without human, policy, and compliance review.
- Customer-facing adverse action notices.
- Legal fair-lending certification.
- Real production deployment on live customer data without additional controls.
- Estimating realized credit loss without exposure at default, loss given default, cure-rate, collections cost, and recovery assumptions.
- Scoring populations that differ materially from the Home Credit training population without drift and representativeness review.

## Training Data

The project uses the public Home Credit Default Risk dataset stored locally under `data/raw/`. Raw data is ignored by Git and is not modified by project scripts.

Source tables used:

- `application_train.csv`
- `bureau.csv`
- `bureau_balance.csv`
- `previous_application.csv`
- `installments_payments.csv`
- `POS_CASH_balance.csv`
- `credit_card_balance.csv`

The processed model table contains `307,511` applicant-level rows and `78` columns, including `TARGET` and `SK_ID_CURR` for labeling and auditability. The saved model uses `76` input features. The observed default rate is `8.07%`, so the task is treated as imbalanced binary classification.

The project does not use `application_test.csv` or `sample_submission.csv`; it creates its own stratified train, validation, and test splits from `application_train.csv`.

## Feature Groups

| feature group | examples | governance note |
| --- | --- | --- |
| Application affordability | `credit_to_income_ratio`, `annuity_to_income_ratio`, `annuity_to_credit_ratio` | Expected to be available at application time. |
| Applicant stability | `employment_years`, `age_years` | Requires stable transformation rules for unusual or missing employment values. |
| External credit signals | `EXT_SOURCE_1`, `EXT_SOURCE_2`, `EXT_SOURCE_3`, `external_score_mean`, `external_score_std` | Strong model drivers; must be monitored for vendor/source drift. |
| Missingness | `missing_value_count` | Useful signal but can reflect process or channel changes. |
| Bureau history | credit counts, overdue counts, debt-to-credit ratio | Medium leakage-risk timing assumption; production needs source timestamp filters. |
| Previous applications | prior counts, approved/refused counts, credit and down-payment summaries | Medium leakage-risk timing assumption. |
| Repayment behavior | installment delay, late payment, POS delinquency, credit card DPD | Highest timing-control concern; must exclude post-decision performance leakage. |
| Encoded categoricals | contract type, gender proxy, education, family status, housing, occupation | Requires category stability, unseen-category handling, and proxy-risk review. |

Forbidden model inputs:

- `TARGET`
- `SK_ID_CURR`
- `SK_ID_PREV`
- `SK_ID_BUREAU`

## Validation Metrics

Final model: tuned LightGBM classifier. Accuracy is intentionally not used as the main metric because defaults are rare and the main business use is risk ranking.

| split | ROC-AUC | PR-AUC | Precision | Recall | F1 | Recall@Top-10% | KS | Brier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| validation | 0.7799 | 0.2712 | 0.2941 | 0.3644 | 0.3255 | 0.3644 | 0.4194 | 0.1643 |
| test | 0.7765 | 0.2640 | 0.2908 | 0.3577 | 0.3208 | 0.3593 | 0.4123 | 0.1645 |

Cross-validation stability on the selected configuration:

| metric | mean | std | min | max |
| --- | ---: | ---: | ---: | ---: |
| ROC-AUC | 0.7830 | 0.0044 | 0.7782 | 0.7893 |
| PR-AUC | 0.2745 | 0.0074 | 0.2651 | 0.2854 |
| Recall@Top-10% | 0.3646 | 0.0074 | 0.3577 | 0.3772 |
| KS statistic | 0.4276 | 0.0104 | 0.4146 | 0.4419 |

Business impact at `10%` review capacity:

- Applicants reviewed: `30,752`
- Observed defaults captured: `10,853`
- Default capture rate: `43.72%`
- Lift vs random review: `4.37x`

## Calibration

Calibration was evaluated using validation-fitted Platt/sigmoid and isotonic transforms, then measured on the test split.

| method | test Brier | test ECE | test ROC-AUC | test PR-AUC | test Recall@Top-10% |
| --- | ---: | ---: | ---: | ---: | ---: |
| Uncalibrated | 0.1645 | 0.2742 | 0.7765 | 0.2640 | 0.3593 |
| Platt/sigmoid | 0.0669 | 0.0062 | 0.7765 | 0.2640 | 0.3593 |
| Isotonic | 0.0668 | 0.0023 | 0.7760 | 0.2540 | 0.3547 |

Platt/sigmoid is the preferred balanced option for probability reporting because it materially improves calibration while preserving ranking metrics. Isotonic has the lowest test Brier score but weakens PR-AUC and Recall@Top-10%.

## Explainability

SHAP is used for global feature importance and applicant-level reason codes. The current SHAP run uses a `5,000` applicant sample for local runtime practicality.

Top global drivers from the saved explainability report:

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

Example reason-code themes include low external credit score, annuity burden risk signal, prior refused application history, high bureau debt burden, credit exposure risk signal, and prior repayment delay.

## Fairness And Proxy-Risk Findings

The current project includes segment-performance and proxy-risk analysis across age, income, and encoded categorical proxies. It is not a legal fair-lending audit.

Current findings:

- Highest top-10% review-rate segment: `OCCUPATION_TYPE_idx=13` at `32.11%`, with observed default rate `17.15%`.
- Age band `18-25` has top-10% review rate `22.50%` and observed default rate `12.29%`.
- Encoded gender proxy `CODE_GENDER_idx=1` has top-10% review rate `14.03%`, compared with `7.91%` for `CODE_GENDER_idx=0`.

Production use would require fair-lending review, protected-class handling strategy, policy review, reject-inference analysis, and compliance sign-off.

## Leakage Audit

The saved final model feature list passed the automated leakage audit:

- Model features checked: `76`
- Processed table columns: `78`
- Forbidden target or identifier inputs found: `0`
- Model features missing from processed table: `0`
- High-risk outcome-keyword features found: `0`
- Medium-risk historical aggregate features: `32`
- Manual-review features: `0`

The medium-risk historical aggregates are acceptable for this portfolio build, but production use requires source-record timestamp filters and feature-lineage proof that every signal is available before the decision or collections scoring timestamp.

## Monitoring Plan

Current simulated monitoring compares a reference window and current window from the processed data.

Latest monitoring results:

- Reference rows: `153,755`
- Current rows: `153,756`
- Features with PSI >= 0.2: `0`
- Features with missingness-rate change >= 5%: `0`
- Prediction PSI: `0.000117`
- Reference ROC-AUC: `0.8455`
- Current ROC-AUC: `0.8432`
- Current PR-AUC: `0.3490`
- Current Recall@Top-10%: `0.4341`

Production monitoring should include:

- Batch-level schema validation.
- Feature missingness and distribution drift checks.
- Prediction distribution drift checks.
- Segment-level score and review-rate monitoring.
- Labeled performance monitoring when outcomes mature.
- Calibration monitoring for probability quality.
- Alert thresholds and documented retraining triggers.

## Limitations

- The dataset is public and historical, not live production data.
- The model is trained on accepted historical applicants only; reject inference is not addressed.
- Monitoring is simulated rather than based on live serving logs.
- SHAP explanations are sampled for runtime practicality.
- Encoded categorical proxies require stronger production treatment for unseen categories and protected/proxy features.
- Calibration improves probability quality, but policy thresholds still require business, risk, and compliance review.
- No formal fair-lending certification, adverse-action review, or regulatory validation has been performed.
- Historical repayment and bureau features require timestamp controls before production use.

## Deployment Readiness

Current status: portfolio-ready prototype, not production-approved.

Required before production:

- Approve intended and prohibited use cases.
- Validate feature availability time for all historical aggregates.
- Add feature registry entries with owner, source, availability time, and leakage-risk rating.
- Complete fair-lending and compliance review.
- Select calibrated probability policy and threshold strategy.
- Validate API schema, error handling, and batch scoring behavior under realistic load.
- Add model versioning and rollback plan.
- Add monitoring alerts, ownership, and escalation process.
- Define retraining, recalibration, and retirement criteria.

## Experiment Tracking And Registry

The project includes `src/models/mlflow_tracking.py` to log existing final model parameters, metrics, and report artifacts to MLflow without retraining. It also writes lightweight model registry-style records:

- `reports/mlflow_experiment_summary.md`
- `reports/model_registry.md`
- `reports/model_registry.json`

The local `mlruns/` store is ignored by Git. A real production registry would add approval stages, artifact access control, deployment references, rollback metadata, model owner sign-off, and compliance review.

## Artifact References

- `reports/final_model_report.md`
- `reports/final_model_metrics.json`
- `reports/cross_validation_summary.md`
- `reports/calibration_report.md`
- `reports/fairness_proxy_analysis.md`
- `reports/leakage_audit.md`
- `reports/explainability_summary.md`
- `reports/business_impact_summary.md`
- `reports/monitoring_summary.md`
- `reports/governance_checklist.md`
- `reports/mlflow_experiment_summary.md`
- `reports/model_registry.md`
