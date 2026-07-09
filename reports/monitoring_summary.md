# Monitoring Summary

This monitoring run simulates production by splitting the processed feature table into a reference window and a current window. The final saved model scores both windows, and all monitoring values are computed from actual features, labels, and predictions.

## Implementation Path

- Evidently status: available (0.7.21) but custom fallback used
- A lightweight custom fallback report was generated to avoid version-specific Evidently API issues and to keep the report reproducible in this local environment.

## Window Sizes

- Reference rows: `153,755`
- Current rows: `153,756`

## Key Checks

- Features with PSI >= 0.2: `0`
- Features with missingness-rate change >= 5%: `0`
- Prediction PSI: `0.000117`
- Reference default rate: `0.0813`
- Current default rate: `0.0802`

## Prediction Drift

| reference_prediction_mean | current_prediction_mean | prediction_mean_change | prediction_psi | reference_top_decile_mean | current_top_decile_mean |
| --- | --- | --- | --- | --- | --- |
| 0.356251 | 0.355971 | -0.00028 | 0.000117 | 0.70169 | 0.699511 |

## Model Performance by Window

| window | roc_auc | pr_auc | precision | recall | f1_score | recall_at_top_10pct | ks_statistic | tn | fp | fn | tp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| reference | 0.84551 | 0.355531 | 0.353696 | 0.449904 | 0.396041 | 0.439661 | 0.542033 | 130986 | 10273 | 6874 | 5622 |
| current | 0.843179 | 0.348983 | 0.346055 | 0.439046 | 0.387044 | 0.434098 | 0.533426 | 131198 | 10229 | 6916 | 5413 |

## Top Feature Drift Signals

| feature | reference_mean | current_mean | mean_change | psi | drift_flag |
| --- | --- | --- | --- | --- | --- |
| annuity_to_income_ratio | 0.180912 | 0.180934 | 2.3e-05 | 0.000214 | False |
| EXT_SOURCE_3 | 0.409717 | 0.409432 | -0.000285 | 0.000192 | False |
| HOUR_APPR_PROCESS_START | 12.058671 | 12.068166 | 0.009495 | 0.000188 | False |
| AMT_CREDIT | 599892.124923 | 598159.880122 | -1732.244801 | 0.000171 | False |
| EXT_SOURCE_1 | 0.217792 | 0.220255 | 0.002463 | 0.000163 | False |
| credit_card_max_dpd | 0.253358 | 0.187524 | -0.065833 | 0.000161 | False |
| bureau_credit_count | 4.763604 | 4.766624 | 0.003019 | 0.000157 | False |
| external_score_std | 0.099928 | 0.100754 | 0.000827 | 0.000151 | False |
| credit_card_month_count | 10.551884 | 10.442259 | -0.109625 | 0.00013 | False |
| missing_value_count | 29.789139 | 29.73696 | -0.052179 | 0.000129 | False |
| AMT_GOODS_PRICE | 538923.035199 | 536895.930695 | -2027.104503 | 0.000127 | False |
| installment_avg_payment_ratio | 1.375967 | 1.247156 | -0.128811 | 0.000122 | False |
| AMT_ANNUITY | 27140.930792 | 27074.101528 | -66.829265 | 0.000122 | False |
| installment_payment_count | 37.819973 | 37.569799 | -0.250174 | 0.00012 | False |
| installment_avg_payment_delay_days | -10.622501 | -10.624345 | -0.001844 | 0.000117 | False |
| external_score_mean | 0.508964 | 0.508969 | 4e-06 | 0.000117 | False |
| bureau_credit_day_overdue_max | 4.219804 | 3.95928 | -0.260525 | 0.000116 | False |
| DAYS_REGISTRATION | -4976.131742 | -4996.108848 | -19.977105 | 0.000115 | False |
| previous_days_decision_mean | -871.262074 | -869.478883 | 1.783191 | 0.000113 | False |
| goods_price_to_credit_ratio | 0.900305 | 0.899446 | -0.000859 | 0.000111 | False |

## Missingness Drift

| feature | reference_missing_rate | current_missing_rate | missing_rate_change | missingness_flag |
| --- | --- | --- | --- | --- |
| CNT_CHILDREN | 0.0 | 0.0 | 0.0 | False |
| previous_application_mean | 0.0 | 0.0 | 0.0 | False |
| installment_avg_payment_ratio | 0.0 | 0.0 | 0.0 | False |
| installment_max_payment_delay_days | 0.0 | 0.0 | 0.0 | False |
| installment_avg_payment_delay_days | 0.0 | 0.0 | 0.0 | False |
| installment_late_payment_count | 0.0 | 0.0 | 0.0 | False |
| installment_payment_count | 0.0 | 0.0 | 0.0 | False |
| previous_days_decision_mean | 0.0 | 0.0 | 0.0 | False |
| previous_down_payment_mean | 0.0 | 0.0 | 0.0 | False |
| previous_credit_mean | 0.0 | 0.0 | 0.0 | False |
| AMT_INCOME_TOTAL | 0.0 | 0.0 | 0.0 | False |
| previous_refused_count | 0.0 | 0.0 | 0.0 | False |
| previous_approved_count | 0.0 | 0.0 | 0.0 | False |
| previous_application_count | 0.0 | 0.0 | 0.0 | False |
| bureau_balance_late_status_count | 0.0 | 0.0 | 0.0 | False |
| bureau_balance_month_count | 0.0 | 0.0 | 0.0 | False |
| bureau_credit_debt_to_credit_ratio | 0.0 | 0.0 | 0.0 | False |
| bureau_credit_debt_sum | 0.0 | 0.0 | 0.0 | False |
| pos_cash_month_count | 0.0 | 0.0 | 0.0 | False |
| pos_cash_late_count | 0.0 | 0.0 | 0.0 | False |

## Production Interpretation

In production, the reference window would be a stable training or recent-good period, and the current window would be the latest batch of scored applicants. Drift alerts should trigger data-quality review, score-distribution review, and possibly model recalibration or retraining analysis. This report is descriptive monitoring and does not retrain the model.
