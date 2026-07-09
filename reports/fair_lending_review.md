# Fair-Lending And Proxy-Risk Governance Review

This report is a formal governance review for the FinSight portfolio model. It converts existing segment-performance metrics and feature-registry metadata into fair-lending review questions, protected/proxy feature controls, and production approval requirements.

It is not a legal fair-lending certification, adverse-action compliance opinion, or regulatory approval. It does not retrain the model, modify raw data, infer protected-class membership, or invent labels.

## Review Scope

- Segment metrics source: `reports/fairness_proxy_metrics.csv`
- Feature registry source: `reports/feature_registry.csv`
- Segment rows reviewed: `41`
- Model features reviewed for proxy controls: `76`
- Population: observed Home Credit accepted/booked applicant records with known `TARGET`.
- Main policy lens: top-10% model-score review queue, not automatic approval or rejection.

## Compliance Boundary

- No legal certification is claimed.
- No adverse-action notice language is approved by this report.
- No protected class is inferred beyond available or encoded dataset proxies.
- Segment gaps are review triggers, not proof of discrimination or compliance failure.
- Production use requires fair-lending, policy, legal, risk, and model-governance sign-off.

## Segment-Risk Interpretation

The segment results show where the model concentrates review attention. These signals can be caused by true historical risk, historical policy selection, data quality, proxy effects, or model behavior. The correct senior data science interpretation is to route large gaps to review, not to treat them as standalone business rules.

### Highest Top-10% Review-Rate Segments

| segment_type | segment_value | applicant_count | observed_default_rate | mean_default_probability | global_top10_review_rate | non_default_review_rate |
| --- | --- | --- | --- | --- | --- | --- |
| occupation_type | OCCUPATION_TYPE_idx=13 | 2093 | 17.15 | 0.5591 | 32.11 | 25.2 |
| age_band | 18-25 | 12233 | 12.29 | 0.5007 | 22.5 | 17.58 |
| age_band | 26-35 | 72429 | 10.66 | 0.4327 | 16.78 | 12.35 |
| occupation_type | OCCUPATION_TYPE_idx=14 | 1348 | 11.28 | 0.4238 | 16.47 | 11.87 |
| occupation_type | OCCUPATION_TYPE_idx=1 | 55186 | 10.58 | 0.4186 | 15.32 | 11.03 |
| occupation_type | OCCUPATION_TYPE_idx=5 | 18603 | 11.33 | 0.431 | 15.18 | 10.66 |
| occupation_type | OCCUPATION_TYPE_idx=10 | 5946 | 10.44 | 0.4164 | 15.02 | 10.8 |
| occupation_type | OCCUPATION_TYPE_idx=9 | 6721 | 10.74 | 0.4237 | 14.39 | 9.95 |
| family_status | NAME_FAMILY_STATUS_idx=1 | 45444 | 9.81 | 0.4016 | 14.09 | 10.17 |
| gender_proxy | CODE_GENDER_idx=1 | 105059 | 10.14 | 0.4101 | 14.03 | 9.96 |

### Largest Segment Disparities

| segment_type | metric | min_segment | min_value | max_segment | max_value | absolute_gap | max_to_min_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| age_band | default_capture_rate_within_segment | 65+ | 0.1215 | 18-25 | 0.5765 | 0.4549 | 4.7435 |
| occupation_type | default_capture_rate_within_segment | OCCUPATION_TYPE_idx=7 | 0.308 | OCCUPATION_TYPE_idx=13 | 0.6546 | 0.3466 | 2.1252 |
| occupation_type | mean_default_probability | OCCUPATION_TYPE_idx=7 | 0.2696 | OCCUPATION_TYPE_idx=13 | 0.5591 | 0.2895 | 2.0738 |
| age_band | mean_default_probability | 65+ | 0.2114 | 18-25 | 0.5007 | 0.2894 | 2.3689 |
| occupation_type | global_top10_review_rate | OCCUPATION_TYPE_idx=7 | 0.0456 | OCCUPATION_TYPE_idx=13 | 0.3211 | 0.2755 | 7.0485 |
| family_status | default_capture_rate_within_segment | NAME_FAMILY_STATUS_idx=4 | 0.2775 | NAME_FAMILY_STATUS_idx=2 | 0.5083 | 0.2308 | 1.8317 |
| occupation_type | non_default_review_rate | OCCUPATION_TYPE_idx=18 | 0.0264 | OCCUPATION_TYPE_idx=13 | 0.252 | 0.2256 | 9.5379 |
| age_band | global_top10_review_rate | 65+ | 0.0103 | 18-25 | 0.225 | 0.2148 | 21.8823 |
| age_band | non_default_review_rate | 65+ | 0.0061 | 18-25 | 0.1758 | 0.1697 | 28.9969 |
| education_type | default_capture_rate_within_segment | NAME_EDUCATION_TYPE_idx=1 | 0.3115 | NAME_EDUCATION_TYPE_idx=0 | 0.4632 | 0.1516 | 1.4867 |
| education_type | mean_default_probability | NAME_EDUCATION_TYPE_idx=1 | 0.2753 | NAME_EDUCATION_TYPE_idx=3 | 0.4116 | 0.1363 | 1.495 |
| occupation_type | observed_default_rate | OCCUPATION_TYPE_idx=7 | 0.0483 | OCCUPATION_TYPE_idx=13 | 0.1715 | 0.1232 | 3.551 |

## Protected And Proxy Feature Controls

The controls below separate standard credit-risk signals from features that need stronger governance because they are protected, policy-sensitive, or may proxy sensitive attributes.

### Control Decision Summary

| control_decision | sensitivity_class | feature_count |
| --- | --- | --- |
| allowed_with_monitoring | asset_or_wealth_proxy | 1 |
| allowed_with_monitoring | credit_capacity_with_proxy_risk | 7 |
| allowed_with_standard_controls | standard_credit_feature | 16 |
| allowed_with_timestamp_controls | historical_credit_behavior | 32 |
| enhanced_review_required | geographic_or_network_proxy | 7 |
| fair_lending_review_required | proxy_sensitive | 5 |
| restricted_pending_fair_lending_approval | protected_or_high_proxy | 1 |
| restricted_pending_policy_approval | protected_or_policy_sensitive | 2 |
| vendor_governance_required | third_party_score | 5 |

### Features Requiring Enhanced Review

| feature_name | feature_group | sensitivity_class | control_decision | rationale | production_control |
| --- | --- | --- | --- | --- | --- |
| DAYS_BIRTH | base_application_numeric | protected_or_policy_sensitive | restricted_pending_policy_approval | Age can be a protected or policy-sensitive attribute. | Use only where legally permitted and policy-approved; monitor score, review-rate, and reason-code differences by age band. |
| DEF_30_CNT_SOCIAL_CIRCLE | base_application_numeric | geographic_or_network_proxy | enhanced_review_required | Regional or social-network signals can encode neighborhood or network proxies. | Require proxy-risk review, adverse-impact monitoring, and documented justification against less sensitive alternatives. |
| DEF_60_CNT_SOCIAL_CIRCLE | base_application_numeric | geographic_or_network_proxy | enhanced_review_required | Regional or social-network signals can encode neighborhood or network proxies. | Require proxy-risk review, adverse-impact monitoring, and documented justification against less sensitive alternatives. |
| OBS_30_CNT_SOCIAL_CIRCLE | base_application_numeric | geographic_or_network_proxy | enhanced_review_required | Regional or social-network signals can encode neighborhood or network proxies. | Require proxy-risk review, adverse-impact monitoring, and documented justification against less sensitive alternatives. |
| OBS_60_CNT_SOCIAL_CIRCLE | base_application_numeric | geographic_or_network_proxy | enhanced_review_required | Regional or social-network signals can encode neighborhood or network proxies. | Require proxy-risk review, adverse-impact monitoring, and documented justification against less sensitive alternatives. |
| REGION_POPULATION_RELATIVE | base_application_numeric | geographic_or_network_proxy | enhanced_review_required | Regional or social-network signals can encode neighborhood or network proxies. | Require proxy-risk review, adverse-impact monitoring, and documented justification against less sensitive alternatives. |
| REGION_RATING_CLIENT | base_application_numeric | geographic_or_network_proxy | enhanced_review_required | Regional or social-network signals can encode neighborhood or network proxies. | Require proxy-risk review, adverse-impact monitoring, and documented justification against less sensitive alternatives. |
| REGION_RATING_CLIENT_W_CITY | base_application_numeric | geographic_or_network_proxy | enhanced_review_required | Regional or social-network signals can encode neighborhood or network proxies. | Require proxy-risk review, adverse-impact monitoring, and documented justification against less sensitive alternatives. |
| age_years | derived_application_features | protected_or_policy_sensitive | restricted_pending_policy_approval | Age can be a protected or policy-sensitive attribute. | Use only where legally permitted and policy-approved; monitor score, review-rate, and reason-code differences by age band. |
| CODE_GENDER_idx | encoded_application_categorical | protected_or_high_proxy | restricted_pending_fair_lending_approval | Gender is directly sensitive or high-risk proxy information. | Exclude or require formal fair-lending, policy, legal, and compliance approval before any underwriting or collections policy use. |
| NAME_EDUCATION_TYPE_idx | encoded_application_categorical | proxy_sensitive | fair_lending_review_required | Categorical socioeconomic or employment variables may proxy protected groups. | Require documented business necessity, alternative-feature review, segment monitoring, and approval before production use. |
| NAME_FAMILY_STATUS_idx | encoded_application_categorical | proxy_sensitive | fair_lending_review_required | Categorical socioeconomic or employment variables may proxy protected groups. | Require documented business necessity, alternative-feature review, segment monitoring, and approval before production use. |
| NAME_HOUSING_TYPE_idx | encoded_application_categorical | proxy_sensitive | fair_lending_review_required | Categorical socioeconomic or employment variables may proxy protected groups. | Require documented business necessity, alternative-feature review, segment monitoring, and approval before production use. |
| OCCUPATION_TYPE_idx | encoded_application_categorical | proxy_sensitive | fair_lending_review_required | Categorical socioeconomic or employment variables may proxy protected groups. | Require documented business necessity, alternative-feature review, segment monitoring, and approval before production use. |
| ORGANIZATION_TYPE_idx | encoded_application_categorical | proxy_sensitive | fair_lending_review_required | Categorical socioeconomic or employment variables may proxy protected groups. | Require documented business necessity, alternative-feature review, segment monitoring, and approval before production use. |

Full feature-level controls are saved to `reports/proxy_feature_controls.csv`.

## Required Production Controls

- Document intended use as ranking/manual-review support, not automated rejection.
- Decide whether gender, age, education, occupation, family, housing, organization, region, and social-circle fields are excluded, restricted, or approved.
- Re-run segment analysis after any feature-removal challenger model.
- Evaluate less-sensitive challenger feature sets and compare PR-AUC, Recall@Top-K, KS, calibration, and business impact.
- Review adverse-action reason-code language before any customer-facing use.
- Monitor segment-level score distribution, top-decile review rate, non-default review rate, and reason-code distribution.
- Combine this review with reject-inference analysis before making through-the-door underwriting claims.
- Record business, risk, compliance, legal, data governance, and MLOps approvals before production deployment.

## Limitations

- The analysis uses available dataset proxies and cannot establish legal protected-class membership.
- Rejected-applicant outcomes are not available; accepted-applicant bias remains documented separately.
- Encoded category values may not map cleanly to human-readable categories if raw mappings are unavailable.
- Segment differences may reflect historical credit-risk differences, historical policy bias, or both.
- This review is evidence for portfolio governance maturity, not a substitute for a lender's formal compliance process.

## Saved Outputs

- `reports/fair_lending_review.md`
- `reports/proxy_feature_controls.csv`
- `reports/fair_lending_governance.json`
