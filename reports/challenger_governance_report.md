# Challenger Model Governance Report

This report compares the saved champion credit-risk model with a less-sensitive challenger model. The challenger removes features flagged as restricted or requiring enhanced fair-lending/proxy-risk review, then uses the same train/validation/test split strategy and actual computed metrics.

The workflow does not change the champion model, does not invent metrics, does not create labels, and does not claim legal fair-lending certification.

## Challenger Design

- Champion: saved full-feature LightGBM model from `models/credit_risk_model.pkl`.
- Challenger: LightGBM trained with protected/high-proxy and enhanced-review features removed.
- Removed controls: `restricted_pending_fair_lending_approval`, `restricted_pending_policy_approval`, `fair_lending_review_required`, and `enhanced_review_required`.
- Champion feature count: `76`
- Challenger feature count: `61`
- Removed feature count: `15`

## Performance And Business Comparison

| model_name | feature_count | test_pr_auc | test_recall_at_top_10pct | test_ks_statistic | test_brier_score | test_expected_calibration_error | top_10pct_default_capture_rate | top_10pct_lift_vs_random |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| champion_full_feature_model | 76 | 0.264 | 0.3593 | 0.4123 | 0.1645 | 0.2742 | 0.3593 | 3.5932 |
| less_sensitive_challenger_model | 61 | 0.2559 | 0.3488 | 0.4013 | 0.1678 | 0.2793 | 0.3488 | 3.4884 |

## Delta Interpretation

- PR-AUC change vs champion: `-0.0081`.
- Recall@Top-10% change vs champion: `-0.0105`.
- KS change vs champion: `-0.0109`.
- Top-10% default-capture change vs champion: `-0.0105`.
- Brier-score change vs champion: `0.0033`.

A lower-sensitive challenger is valuable when it materially reduces fair-lending/proxy-risk exposure with acceptable loss in ranking and business impact. A champion model remains preferable only if its predictive lift is large enough to justify stronger governance controls, challenger evidence, and formal approval.

## Removed Feature Controls

| control_decision | sensitivity_class | removed_feature_count |
| --- | --- | --- |
| enhanced_review_required | geographic_or_network_proxy | 7 |
| fair_lending_review_required | proxy_sensitive | 5 |
| restricted_pending_fair_lending_approval | protected_or_high_proxy | 1 |
| restricted_pending_policy_approval | protected_or_policy_sensitive | 2 |

## Removed Feature Detail

| feature_name | sensitivity_class | control_decision | rationale |
| --- | --- | --- | --- |
| DEF_30_CNT_SOCIAL_CIRCLE | geographic_or_network_proxy | enhanced_review_required | Regional or social-network signals can encode neighborhood or network proxies. |
| DEF_60_CNT_SOCIAL_CIRCLE | geographic_or_network_proxy | enhanced_review_required | Regional or social-network signals can encode neighborhood or network proxies. |
| OBS_30_CNT_SOCIAL_CIRCLE | geographic_or_network_proxy | enhanced_review_required | Regional or social-network signals can encode neighborhood or network proxies. |
| OBS_60_CNT_SOCIAL_CIRCLE | geographic_or_network_proxy | enhanced_review_required | Regional or social-network signals can encode neighborhood or network proxies. |
| REGION_POPULATION_RELATIVE | geographic_or_network_proxy | enhanced_review_required | Regional or social-network signals can encode neighborhood or network proxies. |
| REGION_RATING_CLIENT | geographic_or_network_proxy | enhanced_review_required | Regional or social-network signals can encode neighborhood or network proxies. |
| REGION_RATING_CLIENT_W_CITY | geographic_or_network_proxy | enhanced_review_required | Regional or social-network signals can encode neighborhood or network proxies. |
| NAME_EDUCATION_TYPE_idx | proxy_sensitive | fair_lending_review_required | Categorical socioeconomic or employment variables may proxy protected groups. |
| NAME_FAMILY_STATUS_idx | proxy_sensitive | fair_lending_review_required | Categorical socioeconomic or employment variables may proxy protected groups. |
| NAME_HOUSING_TYPE_idx | proxy_sensitive | fair_lending_review_required | Categorical socioeconomic or employment variables may proxy protected groups. |
| OCCUPATION_TYPE_idx | proxy_sensitive | fair_lending_review_required | Categorical socioeconomic or employment variables may proxy protected groups. |
| ORGANIZATION_TYPE_idx | proxy_sensitive | fair_lending_review_required | Categorical socioeconomic or employment variables may proxy protected groups. |
| CODE_GENDER_idx | protected_or_high_proxy | restricted_pending_fair_lending_approval | Gender is directly sensitive or high-risk proxy information. |
| DAYS_BIRTH | protected_or_policy_sensitive | restricted_pending_policy_approval | Age can be a protected or policy-sensitive attribute. |
| age_years | protected_or_policy_sensitive | restricted_pending_policy_approval | Age can be a protected or policy-sensitive attribute. |

## Governance Recommendation

Use this comparison as a model-risk discussion artifact. A production credit-risk team should review the challenger alongside the champion, less-sensitive challenger variants, calibration, reject-inference limits, business review capacity, adverse-action constraints, and compliance input before approving any automated policy use.

## Saved Outputs

- `reports/challenger_model_comparison.csv`
- `reports/challenger_governance_report.md`
- `reports/challenger_governance.json`
- `models/less_sensitive_challenger_model.pkl` (ignored by Git)
