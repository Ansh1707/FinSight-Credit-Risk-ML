# Collections Scoring Summary

This report converts final model predictions into business-friendly risk bands and a collections priority score. Predictions are generated from the saved final model and processed applicant-level features.

## Scoring Formula

For each applicant:

`collections_priority_score = 100 * default_probability * (0.70 + 0.30 * normalized_credit_amount) * risk_band_weight`

Where:

- `default_probability` is the final model score.
- `normalized_credit_amount` is min-max scaled `AMT_CREDIT` across the scored portfolio.
- `risk_band_weight` is `0.75` for Low Risk, `1.00` for Medium Risk, `1.30` for High Risk, and `1.60` for Critical Risk.

This formula prioritizes applicants with high predicted default risk, larger credit exposure, and more severe risk bands.

## Risk Band Rules

- Low Risk: probability < 0.25
- Medium Risk: 0.25 <= probability < 0.50
- High Risk: 0.50 <= probability < 0.70
- Critical Risk: probability >= 0.70

## Portfolio Risk Band Summary

| risk_band | applicant_count | avg_default_probability | avg_credit_amount | avg_priority_score | max_priority_score |
| --- | --- | --- | --- | --- | --- |
| Low Risk | 125098 | 0.1422 | 633601.8635 | 7.9374 | 18.44 |
| Medium Risk | 97954 | 0.3646 | 610548.1603 | 27.0545 | 44.06 |
| High Risk | 53578 | 0.5953 | 555538.1614 | 57.123 | 80.98 |
| Critical Risk | 30881 | 0.781 | 497862.7693 | 91.6985 | 121.36 |

## Top Priority Sample

| SK_ID_CURR | default_probability | risk_band | credit_amount | collections_priority_score | top_reason_codes |
| --- | --- | --- | --- | --- | --- |
| 265745 | 0.8619 | Critical Risk | 2448000.0 | 121.36 | Reason codes not available in SHAP sample |
| 110403 | 0.8249 | Critical Risk | 2961000.0 | 121.22 | Reason codes not available in SHAP sample |
| 367208 | 0.8781 | Critical Risk | 1971072.0 | 118.62 | Reason codes not available in SHAP sample |
| 449691 | 0.8742 | Critical Risk | 1971072.0 | 118.09 | Reason codes not available in SHAP sample |
| 335680 | 0.897 | Critical Risk | 1615968.0 | 117.35 | Reason codes not available in SHAP sample |
| 279112 | 0.8818 | Critical Risk | 1795500.0 | 117.26 | Reason codes not available in SHAP sample |
| 438132 | 0.8672 | Critical Risk | 1971072.0 | 117.15 | Reason codes not available in SHAP sample |
| 414746 | 0.8724 | Critical Risk | 1890000.0 | 117.0 | Reason codes not available in SHAP sample |
| 280858 | 0.8787 | Critical Risk | 1800000.0 | 116.9 | Reason codes not available in SHAP sample |
| 364859 | 0.9398 | Critical Risk | 1078200.0 | 116.89 | Reason codes not available in SHAP sample |

## Business Use

Collections teams can use the priority score to rank follow-up queues. Risk bands make the score easier to operationalize, while SHAP reason codes provide context for why a customer appears risky when that customer was included in the SHAP sample. The score should support prioritization and review, not automatic adverse action.

## Saved Output

- `reports/collections_priority_sample.csv`
- `reports/collections_summary.md`
