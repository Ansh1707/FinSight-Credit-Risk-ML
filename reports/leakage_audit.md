# Leakage Audit

This report checks the saved final model's feature list for obvious data leakage risks. It is a project governance check, not a replacement for a full production feature-lineage review.

## Automated Check Summary

- Model feature count: `76`
- Processed table column count: `78`
- Forbidden target/identifier features found: `0`
- Missing model features in processed table: `0`
- High-risk keyword features found: `0`
- Medium-risk historical aggregate features: `32`
- Manual-review features: `0`
- Automated leakage check passed: `True`

## Risk Level Counts

| risk_level | feature_count |
| --- | --- |
| low | 44 |
| medium | 32 |

## Features Requiring Human Review

| feature | risk_level | rationale |
| --- | --- | --- |
| bureau_credit_count | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| bureau_active_credit_count | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| bureau_closed_credit_count | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| bureau_overdue_credit_count | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| bureau_credit_day_overdue_max | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| bureau_days_credit_mean | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| bureau_credit_sum_mean | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| bureau_credit_debt_sum | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| bureau_credit_debt_to_credit_ratio | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| bureau_balance_month_count | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| bureau_balance_late_status_count | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| previous_application_count | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| previous_approved_count | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| previous_refused_count | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| previous_credit_mean | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| previous_application_mean | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| previous_down_payment_mean | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| previous_days_decision_mean | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| installment_payment_count | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| installment_late_payment_count | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| installment_avg_payment_delay_days | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| installment_max_payment_delay_days | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| installment_avg_payment_ratio | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| pos_cash_month_count | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| pos_cash_late_count | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| pos_cash_max_dpd_def | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| pos_cash_avg_installments_future | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| credit_card_month_count | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| credit_card_avg_balance | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| credit_card_max_balance | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| credit_card_avg_drawings | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |
| credit_card_max_dpd | medium | Historical bureau, previous application, repayment, POS, or credit card aggregate. Acceptable only if the source records pre-date the current application decision. |

## Explicitly Forbidden Features

These features must not be used as model inputs:

- `TARGET`
- `SK_ID_CURR`
- `SK_ID_PREV`
- `SK_ID_BUREAU`

The saved model feature list does not include these forbidden fields.

## Timing Assumptions

- Base application features are treated as available at application time.
- Derived affordability, age, employment, external-score, and missingness features are derived from application-time fields.
- Bureau, previous application, installment, POS cash, and credit-card aggregates are treated as historical inputs. They are acceptable only if all source records are known before the current loan decision or before the collections scoring timestamp.
- Repayment-delay features are especially important to validate in production because they can become leakage if they include performance after the target loan begins.

## Production Recommendations

- Add source-record timestamp filters for every historical table before production use.
- Maintain `reports/feature_registry.md` with availability time, source table, owner, and leakage-risk rating.
- Keep identifiers for joins and auditability, but exclude them from model training.
- Re-run `python src/features/feature_registry.py` and this leakage audit after every feature engineering change.

## Saved Output

- `reports/leakage_audit.md`
