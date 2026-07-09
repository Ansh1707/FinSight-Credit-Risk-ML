# Business Impact Summary

This report converts model-ranked default probabilities into business review-capacity scenarios. It uses actual `TARGET` labels, final model scores, and `AMT_CREDIT` as a credit-exposure proxy. It does not invent currency loss assumptions or claim realized collections recovery.

## Portfolio Context

- Applicants scored: `307,511`
- Observed defaults: `24,825`
- Observed default rate: `8.07%`
- Total credit exposure proxy: `184,207,084,196`

## Review Capacity Results

| review_rate_percent | applicants_reviewed | defaults_captured | default_capture_rate | lift_vs_random_default_capture | default_credit_exposure_capture_rate | expected_risk_exposure_capture_rate | avg_default_probability_reviewed | min_default_probability_reviewed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5.0 | 15376 | 6715 | 27.05 | 5.4099 | 24.06 | 9.83 | 0.8265 | 0.7738 |
| 10.0 | 30752 | 10853 | 43.72 | 4.3718 | 39.64 | 19.04 | 0.7813 | 0.7006 |
| 15.0 | 46127 | 14029 | 56.51 | 3.7674 | 52.27 | 27.73 | 0.7437 | 0.637 |
| 20.0 | 61503 | 16376 | 65.97 | 3.2983 | 62.27 | 36.0 | 0.7097 | 0.5789 |

## Key Interpretation

At a `10%` review capacity, the model-ranked queue reviews `30,752` applicants and captures `43.72%` of observed defaults. This is `4.37x` the default capture expected from a random review queue of the same size.

The exposure columns are decision-support proxies. In a real production deployment, expected loss would require additional assumptions such as exposure at default, loss given default, collections cost, cure rate, and customer contact capacity.

## Recommended Business Use

- Use the top-risk capacity table to choose review queue size based on team capacity.
- Pair default capture with credit exposure capture to balance risk and operational load.
- Treat the output as prioritization guidance, not an automatic adverse-action policy.
- Re-estimate impact after calibration, fairness review, and production monitoring.

## Saved Outputs

- `reports/business_impact_by_threshold.csv`
- `reports/business_impact_summary.md`
