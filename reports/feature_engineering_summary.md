# Feature Engineering Summary

This report describes the PySpark feature engineering pipeline. Raw data was read from `data/raw/` and was not modified.

## Run Scope

- Full mode used; all rows from `application_train.csv` were processed.
- Final dataset shape: `307,511` rows x `78` columns
- Output Parquet: `data/processed/model_features.parquet`
- Model training: not performed in this phase.

## Source Tables

- `application_train.csv` as the base applicant table
- `bureau.csv` aggregated to `SK_ID_CURR`
- `bureau_balance.csv` joined through bureau IDs and aggregated to `SK_ID_CURR`
- `previous_application.csv` aggregated to `SK_ID_CURR`
- `installments_payments.csv` aggregated to `SK_ID_CURR`
- `POS_CASH_balance.csv` aggregated to `SK_ID_CURR`
- `credit_card_balance.csv` aggregated to `SK_ID_CURR`

## Created Lending-Risk Features

- `loan_to_income_ratio`
- `credit_to_income_ratio`
- `annuity_to_income_ratio`
- `annuity_to_credit_ratio`
- `goods_price_to_credit_ratio`
- `employment_years`
- `age_years`
- `external_score_mean`
- `external_score_std`
- `missing_value_count`
- `bureau_credit_count`
- `bureau_active_credit_count`
- `bureau_closed_credit_count`
- `bureau_overdue_credit_count`
- `bureau_credit_day_overdue_max`
- `bureau_days_credit_mean`
- `bureau_credit_sum_mean`
- `bureau_credit_debt_sum`
- `bureau_credit_debt_to_credit_ratio`
- `bureau_balance_month_count`
- `bureau_balance_late_status_count`
- `previous_application_count`
- `previous_approved_count`
- `previous_refused_count`
- `previous_credit_mean`
- `previous_application_mean`
- `previous_down_payment_mean`
- `previous_days_decision_mean`
- `installment_payment_count`
- `installment_late_payment_count`
- `installment_avg_payment_delay_days`
- `installment_max_payment_delay_days`
- `installment_avg_payment_ratio`
- `pos_cash_month_count`
- `pos_cash_late_count`
- `pos_cash_max_dpd_def`
- `pos_cash_avg_installments_future`
- `credit_card_month_count`
- `credit_card_avg_balance`
- `credit_card_max_balance`
- `credit_card_avg_drawings`
- `credit_card_max_dpd`

## Missing-Value Handling

- Numeric feature nulls were filled with `0` after deriving `missing_value_count`.
- Selected categorical nulls were filled with `Missing` before indexing.
- The raw files were not modified.

## Prepared Feature Columns

- Numeric/model columns: `65`
- Encoded categorical index columns: `11`

### Encoded Categorical Columns

- `NAME_CONTRACT_TYPE_idx`
- `CODE_GENDER_idx`
- `FLAG_OWN_CAR_idx`
- `FLAG_OWN_REALTY_idx`
- `NAME_TYPE_SUITE_idx`
- `NAME_INCOME_TYPE_idx`
- `NAME_EDUCATION_TYPE_idx`
- `NAME_FAMILY_STATUS_idx`
- `NAME_HOUSING_TYPE_idx`
- `OCCUPATION_TYPE_idx`
- `ORGANIZATION_TYPE_idx`
