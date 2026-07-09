# Feature Registry And Timestamp Lineage

This registry documents the final model feature groups, source tables, transformation logic, availability-time assumptions, leakage risk, and production controls. It is generated from the saved final model feature list when available and does not modify raw data or retrain models.

## Scope

- Registered model features: `76`
- Output CSV: `reports/feature_registry.csv`
- Output report: `reports/feature_registry.md`
- Model training: not performed.

## Feature Group Summary

| feature_group | leakage_risk | source_tables | feature_count |
| --- | --- | --- | --- |
| base_application_numeric | low | application_train.csv | 23 |
| derived_application_features | low | application_train.csv | 10 |
| encoded_application_categorical | low_to_medium_proxy_risk | application_train.csv | 11 |
| bureau_balance_history | medium | bureau.csv, bureau_balance.csv | 2 |
| bureau_credit_history | medium | bureau.csv | 9 |
| previous_application_history | medium | previous_application.csv | 7 |
| credit_card_balance_history | medium_high_timing_sensitive | credit_card_balance.csv | 5 |
| installment_repayment_history | medium_high_timing_sensitive | installments_payments.csv | 5 |
| pos_cash_balance_history | medium_high_timing_sensitive | POS_CASH_balance.csv | 4 |

## Timestamp-Lineage Summary

| feature_group | source_tables | transformation_logic | availability_time | leakage_risk | production_controls |
| --- | --- | --- | --- | --- | --- |
| base_application_numeric | application_train.csv | Direct selected numeric fields from the base application table. | Known at loan application submission time. | low | Validate schema, numeric ranges, missingness, and application timestamp; exclude identifiers and target from model inputs. |
| bureau_balance_history | bureau.csv, bureau_balance.csv | Join bureau_balance to bureau through SK_ID_BUREAU and aggregate monthly status counts and late-status counts to SK_ID_CURR. | Must include only monthly statuses visible before the current decision or collections scoring timestamp. | medium | Filter MONTHS_BALANCE/status snapshots by observation cutoff, validate bureau linkage integrity, and monitor late-status distribution drift. |
| bureau_credit_history | bureau.csv | Aggregate external bureau tradeline counts, active/closed status, overdue counts, credit recency, credit amount, and debt burden to SK_ID_CURR. | Must be restricted to bureau records available before the current loan decision or collections scoring timestamp. | medium | Apply source-record timestamp filters, validate bureau pull date, exclude post-application bureau updates, and monitor bureau-source refresh changes. |
| credit_card_balance_history | credit_card_balance.csv | Aggregate credit-card monthly observation count, average/max balance, average drawings, and max DPD to SK_ID_CURR. | Must include only credit-card snapshots known before the current decision or collections scoring timestamp. | medium_high_timing_sensitive | Filter balance snapshots by observation cutoff, exclude post-decision behavior, and monitor balance/drawing/DPD distribution drift. |
| derived_application_features | application_train.csv | Creates affordability ratios, age/employment transformations, external score aggregate statistics, and application-row missingness count. | Known or derivable at loan application submission time. | low | Freeze ratio definitions, handle zero denominators consistently, validate external-score source timing, and monitor null-rate drift. |
| encoded_application_categorical | application_train.csv | Fill missing categorical values with 'Missing' and encode with Spark StringIndexer using handleInvalid='keep'. | Known at loan application submission time. | low_to_medium_proxy_risk | Persist category mapping, handle unseen categories, monitor category drift, and review protected/proxy-sensitive fields with policy and compliance. |
| installment_repayment_history | installments_payments.csv | Create payment delay and payment ratio, then aggregate count, late count, average/max delay, and average payment ratio to SK_ID_CURR. | Must include only installments from loans observed before the current decision or collections scoring timestamp. | medium_high_timing_sensitive | Enforce observation cutoff by installment/payment date, exclude future repayment behavior, and separately test leakage around target-loan payments. |
| pos_cash_balance_history | POS_CASH_balance.csv | Aggregate POS cash monthly observation count, delinquency count, max DPD, and average remaining installments to SK_ID_CURR. | Must include only POS balance snapshots before the current decision or collections scoring timestamp. | medium_high_timing_sensitive | Filter monthly snapshots by observation date, exclude target-loan future performance, and monitor delinquency and remaining-installment drift. |
| previous_application_history | previous_application.csv | Aggregate prior application counts, approved/refused counts, mean credit, mean application amount, mean down payment, and mean decision recency. | Must include only applications decided before the current application or collections scoring timestamp. | medium | Filter by prior decision timestamp, exclude current-loan outcome, validate application identity links, and monitor refused/approved mix drift. |

## Timing-Sensitive Features

The features below are useful credit-risk signals, but production use requires timestamp controls to prove the source records existed before the decision or scoring timestamp.

| feature_name | feature_group | availability_time | leakage_risk | production_controls |
| --- | --- | --- | --- | --- |
| bureau_balance_late_status_count | bureau_balance_history | Must include only monthly statuses visible before the current decision or collections scoring timestamp. | medium | Filter MONTHS_BALANCE/status snapshots by observation cutoff, validate bureau linkage integrity, and monitor late-status distribution drift. |
| bureau_balance_month_count | bureau_balance_history | Must include only monthly statuses visible before the current decision or collections scoring timestamp. | medium | Filter MONTHS_BALANCE/status snapshots by observation cutoff, validate bureau linkage integrity, and monitor late-status distribution drift. |
| bureau_active_credit_count | bureau_credit_history | Must be restricted to bureau records available before the current loan decision or collections scoring timestamp. | medium | Apply source-record timestamp filters, validate bureau pull date, exclude post-application bureau updates, and monitor bureau-source refresh changes. |
| bureau_closed_credit_count | bureau_credit_history | Must be restricted to bureau records available before the current loan decision or collections scoring timestamp. | medium | Apply source-record timestamp filters, validate bureau pull date, exclude post-application bureau updates, and monitor bureau-source refresh changes. |
| bureau_credit_count | bureau_credit_history | Must be restricted to bureau records available before the current loan decision or collections scoring timestamp. | medium | Apply source-record timestamp filters, validate bureau pull date, exclude post-application bureau updates, and monitor bureau-source refresh changes. |
| bureau_credit_day_overdue_max | bureau_credit_history | Must be restricted to bureau records available before the current loan decision or collections scoring timestamp. | medium | Apply source-record timestamp filters, validate bureau pull date, exclude post-application bureau updates, and monitor bureau-source refresh changes. |
| bureau_credit_debt_sum | bureau_credit_history | Must be restricted to bureau records available before the current loan decision or collections scoring timestamp. | medium | Apply source-record timestamp filters, validate bureau pull date, exclude post-application bureau updates, and monitor bureau-source refresh changes. |
| bureau_credit_debt_to_credit_ratio | bureau_credit_history | Must be restricted to bureau records available before the current loan decision or collections scoring timestamp. | medium | Apply source-record timestamp filters, validate bureau pull date, exclude post-application bureau updates, and monitor bureau-source refresh changes. |
| bureau_credit_sum_mean | bureau_credit_history | Must be restricted to bureau records available before the current loan decision or collections scoring timestamp. | medium | Apply source-record timestamp filters, validate bureau pull date, exclude post-application bureau updates, and monitor bureau-source refresh changes. |
| bureau_days_credit_mean | bureau_credit_history | Must be restricted to bureau records available before the current loan decision or collections scoring timestamp. | medium | Apply source-record timestamp filters, validate bureau pull date, exclude post-application bureau updates, and monitor bureau-source refresh changes. |
| bureau_overdue_credit_count | bureau_credit_history | Must be restricted to bureau records available before the current loan decision or collections scoring timestamp. | medium | Apply source-record timestamp filters, validate bureau pull date, exclude post-application bureau updates, and monitor bureau-source refresh changes. |
| credit_card_avg_balance | credit_card_balance_history | Must include only credit-card snapshots known before the current decision or collections scoring timestamp. | medium_high_timing_sensitive | Filter balance snapshots by observation cutoff, exclude post-decision behavior, and monitor balance/drawing/DPD distribution drift. |
| credit_card_avg_drawings | credit_card_balance_history | Must include only credit-card snapshots known before the current decision or collections scoring timestamp. | medium_high_timing_sensitive | Filter balance snapshots by observation cutoff, exclude post-decision behavior, and monitor balance/drawing/DPD distribution drift. |
| credit_card_max_balance | credit_card_balance_history | Must include only credit-card snapshots known before the current decision or collections scoring timestamp. | medium_high_timing_sensitive | Filter balance snapshots by observation cutoff, exclude post-decision behavior, and monitor balance/drawing/DPD distribution drift. |
| credit_card_max_dpd | credit_card_balance_history | Must include only credit-card snapshots known before the current decision or collections scoring timestamp. | medium_high_timing_sensitive | Filter balance snapshots by observation cutoff, exclude post-decision behavior, and monitor balance/drawing/DPD distribution drift. |
| credit_card_month_count | credit_card_balance_history | Must include only credit-card snapshots known before the current decision or collections scoring timestamp. | medium_high_timing_sensitive | Filter balance snapshots by observation cutoff, exclude post-decision behavior, and monitor balance/drawing/DPD distribution drift. |
| installment_avg_payment_delay_days | installment_repayment_history | Must include only installments from loans observed before the current decision or collections scoring timestamp. | medium_high_timing_sensitive | Enforce observation cutoff by installment/payment date, exclude future repayment behavior, and separately test leakage around target-loan payments. |
| installment_avg_payment_ratio | installment_repayment_history | Must include only installments from loans observed before the current decision or collections scoring timestamp. | medium_high_timing_sensitive | Enforce observation cutoff by installment/payment date, exclude future repayment behavior, and separately test leakage around target-loan payments. |
| installment_late_payment_count | installment_repayment_history | Must include only installments from loans observed before the current decision or collections scoring timestamp. | medium_high_timing_sensitive | Enforce observation cutoff by installment/payment date, exclude future repayment behavior, and separately test leakage around target-loan payments. |
| installment_max_payment_delay_days | installment_repayment_history | Must include only installments from loans observed before the current decision or collections scoring timestamp. | medium_high_timing_sensitive | Enforce observation cutoff by installment/payment date, exclude future repayment behavior, and separately test leakage around target-loan payments. |
| installment_payment_count | installment_repayment_history | Must include only installments from loans observed before the current decision or collections scoring timestamp. | medium_high_timing_sensitive | Enforce observation cutoff by installment/payment date, exclude future repayment behavior, and separately test leakage around target-loan payments. |
| pos_cash_avg_installments_future | pos_cash_balance_history | Must include only POS balance snapshots before the current decision or collections scoring timestamp. | medium_high_timing_sensitive | Filter monthly snapshots by observation date, exclude target-loan future performance, and monitor delinquency and remaining-installment drift. |
| pos_cash_late_count | pos_cash_balance_history | Must include only POS balance snapshots before the current decision or collections scoring timestamp. | medium_high_timing_sensitive | Filter monthly snapshots by observation date, exclude target-loan future performance, and monitor delinquency and remaining-installment drift. |
| pos_cash_max_dpd_def | pos_cash_balance_history | Must include only POS balance snapshots before the current decision or collections scoring timestamp. | medium_high_timing_sensitive | Filter monthly snapshots by observation date, exclude target-loan future performance, and monitor delinquency and remaining-installment drift. |
| pos_cash_month_count | pos_cash_balance_history | Must include only POS balance snapshots before the current decision or collections scoring timestamp. | medium_high_timing_sensitive | Filter monthly snapshots by observation date, exclude target-loan future performance, and monitor delinquency and remaining-installment drift. |
| previous_application_count | previous_application_history | Must include only applications decided before the current application or collections scoring timestamp. | medium | Filter by prior decision timestamp, exclude current-loan outcome, validate application identity links, and monitor refused/approved mix drift. |
| previous_application_mean | previous_application_history | Must include only applications decided before the current application or collections scoring timestamp. | medium | Filter by prior decision timestamp, exclude current-loan outcome, validate application identity links, and monitor refused/approved mix drift. |
| previous_approved_count | previous_application_history | Must include only applications decided before the current application or collections scoring timestamp. | medium | Filter by prior decision timestamp, exclude current-loan outcome, validate application identity links, and monitor refused/approved mix drift. |
| previous_credit_mean | previous_application_history | Must include only applications decided before the current application or collections scoring timestamp. | medium | Filter by prior decision timestamp, exclude current-loan outcome, validate application identity links, and monitor refused/approved mix drift. |
| previous_days_decision_mean | previous_application_history | Must include only applications decided before the current application or collections scoring timestamp. | medium | Filter by prior decision timestamp, exclude current-loan outcome, validate application identity links, and monitor refused/approved mix drift. |
| previous_down_payment_mean | previous_application_history | Must include only applications decided before the current application or collections scoring timestamp. | medium | Filter by prior decision timestamp, exclude current-loan outcome, validate application identity links, and monitor refused/approved mix drift. |
| previous_refused_count | previous_application_history | Must include only applications decided before the current application or collections scoring timestamp. | medium | Filter by prior decision timestamp, exclude current-loan outcome, validate application identity links, and monitor refused/approved mix drift. |

## Production Feature Governance Requirements

- Maintain a feature registry with owner, source table, source columns, transformation, availability time, and leakage-risk rating.
- Enforce observation cutoffs for bureau, previous application, installment, POS cash, and credit-card records.
- Exclude identifiers and target fields from model inputs while preserving identifiers for joins and auditability.
- Version feature definitions and category encodings before deployment.
- Re-run `python src/features/feature_registry.py` and `python src/features/leakage_checks.py` after every feature change.

## Portfolio Interpretation

For this portfolio build, the registry closes the lineage documentation gap by making timing assumptions explicit. For real production lending, these assumptions would need source-system timestamps, policy sign-off, data contracts, feature-store ownership, and monitoring alerts.
