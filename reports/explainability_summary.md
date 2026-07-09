# Explainability Summary

This report explains the saved final LightGBM credit-risk model using SHAP. Reason codes are generated only from positive applicant-level SHAP contributions, meaning each listed reason increased the model score for that applicant.

## Scope

- Total processed rows available: `307,511`
- SHAP sample size: `5,000`
- Model loaded from `models/credit_risk_model.pkl`
- Features loaded from `data/processed/model_features.parquet`

## Top Global Risk Drivers

| feature | mean_abs_shap | mean_shap |
| --- | --- | --- |
| external_score_mean | 0.48368 | -0.021683 |
| annuity_to_credit_ratio | 0.123492 | -0.000229 |
| CODE_GENDER_idx | 0.123329 | -0.005748 |
| goods_price_to_credit_ratio | 0.120168 | -0.001549 |
| pos_cash_avg_installments_future | 0.119669 | -0.001792 |
| NAME_EDUCATION_TYPE_idx | 0.09531 | -0.00189 |
| pos_cash_month_count | 0.093901 | -0.004323 |
| installment_max_payment_delay_days | 0.092362 | 0.000561 |
| EXT_SOURCE_1 | 0.091881 | 0.006329 |
| AMT_ANNUITY | 0.08858 | 0.009782 |
| previous_down_payment_mean | 0.080468 | -0.002711 |
| EXT_SOURCE_3 | 0.078118 | 0.003137 |
| installment_payment_count | 0.07365 | -0.001092 |
| previous_refused_count | 0.070119 | -0.00033 |
| FLAG_OWN_CAR_idx | 0.06994 | 0.01073 |

## Sample Applicant Reason Codes

| SK_ID_CURR | default_probability | reason_code_1 | reason_feature_1 | reason_code_2 | reason_feature_2 | reason_code_3 | reason_feature_3 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 406244 | 0.9287 | Low external credit score | external_score_mean | Credit exposure risk signal | goods_price_to_credit_ratio | Annuity burden risk signal | annuity_to_credit_ratio |
| 238626 | 0.9251 | Low external credit score | external_score_mean | Annuity burden risk signal | annuity_to_credit_ratio | Low external credit score | EXT_SOURCE_3 |
| 218200 | 0.9106 | Low external credit score | external_score_mean | Low external credit score | EXT_SOURCE_2 | Prior refused application history | previous_refused_count |
| 146601 | 0.9098 | Low external credit score | external_score_mean | Credit exposure risk signal | goods_price_to_credit_ratio | Prior refused application history | previous_refused_count |
| 188110 | 0.9097 | Low external credit score | external_score_mean | POS repayment profile signal | pos_cash_avg_installments_future | Prior repayment delay | bureau_overdue_credit_count |
| 213011 | 0.9074 | Low external credit score | external_score_mean | Credit exposure risk signal | goods_price_to_credit_ratio | High bureau debt burden | bureau_credit_debt_to_credit_ratio |
| 296505 | 0.9008 | Low external credit score | external_score_mean | Annuity burden risk signal | annuity_to_credit_ratio | Prior repayment delay | pos_cash_max_dpd_def |
| 338430 | 0.8978 | Low external credit score | external_score_mean | High bureau debt burden | bureau_credit_debt_to_credit_ratio | Annuity burden risk signal | annuity_to_credit_ratio |
| 304366 | 0.8964 | Low external credit score | external_score_mean | Low external credit score | EXT_SOURCE_2 | Credit exposure risk signal | goods_price_to_credit_ratio |
| 272726 | 0.8958 | Low external credit score | external_score_mean | Annuity burden risk signal | annuity_to_credit_ratio | High bureau debt burden | bureau_credit_debt_to_credit_ratio |

## Business Interpretation

Global SHAP importance identifies the variables the model relies on most across the sampled portfolio. Applicant-level reason codes translate the largest positive SHAP contributors into review-friendly explanations such as affordability burden, external score weakness, limited bureau signal, or prior repayment delay. These explanations should support review, monitoring, and collections prioritization; they are not standalone approval or rejection rules.

## Saved Outputs

- `reports/figures/shap_summary.png`
- `reports/figures/shap_bar.png`
- `reports/sample_reason_codes.csv`
- `reports/explainability_summary.md`
