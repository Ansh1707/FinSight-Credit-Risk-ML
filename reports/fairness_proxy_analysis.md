# Fairness and Proxy-Risk Analysis

This report is a segment-performance and proxy-risk analysis for the saved credit-risk model. It is not a legal fairness certification, adverse-action review, or regulatory compliance audit.

## Scope

- Applicants scored: `307,511`
- Observed default rate: `8.07%`
- Global top-risk review policy: top `10%` of model scores
- Minimum segment size included: `500` applicants
- Segment source: `processed_encoded_proxy_categories`
- Segment source note: Raw application categories were not available locally, so encoded categorical feature proxies from `data/processed/model_features.parquet` were used for gender, education, family status, and occupation segments.

## Segments Reviewed

- `gender_proxy`: encoded `CODE_GENDER_idx` proxy from processed features.
- `age_band`: derived from processed `DAYS_BIRTH`.
- `income_band`: derived from processed `AMT_INCOME_TOTAL`.
- `education_type`: encoded `NAME_EDUCATION_TYPE_idx` proxy.
- `family_status`: encoded `NAME_FAMILY_STATUS_idx` proxy.
- `occupation_type`: encoded `OCCUPATION_TYPE_idx` proxy.

## Highest Top-10% Review Rates

| segment_type | segment_value | applicant_count | observed_default_rate | mean_default_probability | global_top10_review_rate | default_capture_rate_within_segment | non_default_review_rate | roc_auc | pr_auc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| occupation_type | OCCUPATION_TYPE_idx=13 | 2093 | 17.15 | 0.5591 | 32.11 | 65.46 | 25.2 | 0.784 | 0.4175 |
| age_band | 18-25 | 12233 | 12.29 | 0.5007 | 22.5 | 57.65 | 17.58 | 0.8003 | 0.3662 |
| age_band | 26-35 | 72429 | 10.66 | 0.4327 | 16.78 | 53.88 | 12.35 | 0.8269 | 0.3834 |
| occupation_type | OCCUPATION_TYPE_idx=14 | 1348 | 11.28 | 0.4238 | 16.47 | 52.63 | 11.87 | 0.8232 | 0.4014 |
| occupation_type | OCCUPATION_TYPE_idx=1 | 55186 | 10.58 | 0.4186 | 15.32 | 51.58 | 11.03 | 0.8319 | 0.3857 |
| occupation_type | OCCUPATION_TYPE_idx=5 | 18603 | 11.33 | 0.431 | 15.18 | 50.59 | 10.66 | 0.8202 | 0.3931 |
| occupation_type | OCCUPATION_TYPE_idx=10 | 5946 | 10.44 | 0.4164 | 15.02 | 51.21 | 10.8 | 0.8303 | 0.3799 |
| occupation_type | OCCUPATION_TYPE_idx=9 | 6721 | 10.74 | 0.4237 | 14.39 | 51.25 | 9.95 | 0.8318 | 0.3992 |
| family_status | NAME_FAMILY_STATUS_idx=1 | 45444 | 9.81 | 0.4016 | 14.09 | 50.08 | 10.17 | 0.8339 | 0.3768 |
| gender_proxy | CODE_GENDER_idx=1 | 105059 | 10.14 | 0.4101 | 14.03 | 50.05 | 9.96 | 0.8352 | 0.3795 |
| family_status | NAME_FAMILY_STATUS_idx=2 | 29775 | 9.94 | 0.4049 | 14.01 | 50.83 | 9.94 | 0.8389 | 0.3871 |
| occupation_type | OCCUPATION_TYPE_idx=2 | 32102 | 9.63 | 0.4038 | 13.2 | 45.76 | 9.73 | 0.8255 | 0.3548 |

## Largest Segment Gaps

| segment_type | metric | min | max | absolute_gap | max_to_min_ratio |
| --- | --- | --- | --- | --- | --- |
| age_band | default_capture_rate_within_segment | 0.122 | 0.576 | 0.455 | 4.743 |
| occupation_type | default_capture_rate_within_segment | 0.308 | 0.655 | 0.347 | 2.125 |
| occupation_type | mean_default_probability | 0.27 | 0.559 | 0.289 | 2.074 |
| age_band | mean_default_probability | 0.211 | 0.501 | 0.289 | 2.369 |
| occupation_type | global_top10_review_rate | 0.046 | 0.321 | 0.276 | 7.048 |
| family_status | default_capture_rate_within_segment | 0.277 | 0.508 | 0.231 | 1.832 |
| occupation_type | non_default_review_rate | 0.026 | 0.252 | 0.226 | 9.538 |
| age_band | global_top10_review_rate | 0.01 | 0.225 | 0.215 | 21.882 |
| age_band | non_default_review_rate | 0.006 | 0.176 | 0.17 | 28.997 |
| education_type | default_capture_rate_within_segment | 0.312 | 0.463 | 0.152 | 1.487 |
| education_type | mean_default_probability | 0.275 | 0.412 | 0.136 | 1.495 |
| occupation_type | observed_default_rate | 0.048 | 0.172 | 0.123 | 3.551 |

## Full Segment Metrics

| segment_type | segment_value | applicant_count | observed_default_rate | mean_default_probability | global_top10_review_rate | default_capture_rate_within_segment | non_default_review_rate | roc_auc | pr_auc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| age_band | 36-45 | 84261 | 8.41 | 0.3575 | 10.14 | 43.27 | 7.1 | 0.8444 | 0.3574 |
| age_band | 26-35 | 72429 | 10.66 | 0.4327 | 16.78 | 53.88 | 12.35 | 0.8269 | 0.3834 |
| age_band | 46-55 | 70190 | 7.05 | 0.328 | 7.29 | 38.84 | 4.9 | 0.852 | 0.3476 |
| age_band | 56-65 | 60522 | 5.42 | 0.2847 | 3.48 | 24.5 | 2.27 | 0.8449 | 0.2856 |
| age_band | 18-25 | 12233 | 12.29 | 0.5007 | 22.5 | 57.65 | 17.58 | 0.8003 | 0.3662 |
| age_band | 65+ | 7876 | 3.66 | 0.2114 | 1.03 | 12.15 | 0.61 | 0.8552 | 0.2555 |
| education_type | NAME_EDUCATION_TYPE_idx=0 | 218391 | 8.94 | 0.382 | 11.76 | 46.32 | 8.37 | 0.8378 | 0.3628 |
| education_type | NAME_EDUCATION_TYPE_idx=1 | 74863 | 5.36 | 0.2753 | 4.74 | 31.15 | 3.25 | 0.8551 | 0.2945 |
| education_type | NAME_EDUCATION_TYPE_idx=2 | 10277 | 8.48 | 0.3753 | 10.03 | 42.2 | 7.05 | 0.8401 | 0.3519 |
| education_type | NAME_EDUCATION_TYPE_idx=3 | 3816 | 10.93 | 0.4116 | 12.45 | 46.04 | 8.33 | 0.835 | 0.4095 |
| family_status | NAME_FAMILY_STATUS_idx=0 | 196432 | 7.56 | 0.3427 | 8.95 | 41.62 | 6.28 | 0.846 | 0.3408 |
| family_status | NAME_FAMILY_STATUS_idx=1 | 45444 | 9.81 | 0.4016 | 14.09 | 50.08 | 10.17 | 0.8339 | 0.3768 |
| family_status | NAME_FAMILY_STATUS_idx=2 | 29775 | 9.94 | 0.4049 | 14.01 | 50.83 | 9.94 | 0.8389 | 0.3871 |
| family_status | NAME_FAMILY_STATUS_idx=3 | 19770 | 8.19 | 0.3566 | 9.43 | 41.67 | 6.55 | 0.8418 | 0.3568 |
| family_status | NAME_FAMILY_STATUS_idx=4 | 16088 | 5.82 | 0.3 | 4.51 | 27.75 | 3.08 | 0.8465 | 0.2967 |
| gender_proxy | CODE_GENDER_idx=0 | 202448 | 7.0 | 0.3281 | 7.91 | 38.96 | 5.57 | 0.8461 | 0.3308 |
| gender_proxy | CODE_GENDER_idx=1 | 105059 | 10.14 | 0.4101 | 14.03 | 50.05 | 9.96 | 0.8352 | 0.3795 |
| income_band | 100k-150k | 91591 | 8.62 | 0.3746 | 11.48 | 45.69 | 8.26 | 0.8398 | 0.3546 |
| income_band | 200k-300k | 65176 | 7.55 | 0.3395 | 8.55 | 40.34 | 5.95 | 0.8464 | 0.3414 |
| income_band | 150k-200k | 64307 | 8.45 | 0.3648 | 10.44 | 44.79 | 7.27 | 0.8426 | 0.3604 |
| income_band | <100k | 63698 | 8.2 | 0.3643 | 10.57 | 45.38 | 7.46 | 0.8411 | 0.358 |
| income_band | 300k+ | 22739 | 5.95 | 0.2819 | 5.36 | 33.78 | 3.56 | 0.8673 | 0.3347 |
| occupation_type | OCCUPATION_TYPE_idx=0 | 96391 | 6.51 | 0.3168 | 6.45 | 35.19 | 4.45 | 0.8465 | 0.3203 |
| occupation_type | OCCUPATION_TYPE_idx=1 | 55186 | 10.58 | 0.4186 | 15.32 | 51.58 | 11.03 | 0.8319 | 0.3857 |
| occupation_type | OCCUPATION_TYPE_idx=2 | 32102 | 9.63 | 0.4038 | 13.2 | 45.76 | 9.73 | 0.8255 | 0.3548 |
| occupation_type | OCCUPATION_TYPE_idx=3 | 27570 | 6.3 | 0.3191 | 7.52 | 38.55 | 5.43 | 0.8533 | 0.3163 |
| occupation_type | OCCUPATION_TYPE_idx=4 | 21371 | 6.21 | 0.2926 | 5.64 | 35.69 | 3.65 | 0.8651 | 0.3522 |
| occupation_type | OCCUPATION_TYPE_idx=5 | 18603 | 11.33 | 0.431 | 15.18 | 50.59 | 10.66 | 0.8202 | 0.3931 |
| occupation_type | OCCUPATION_TYPE_idx=6 | 11380 | 6.16 | 0.3123 | 7.08 | 36.66 | 5.14 | 0.8375 | 0.29 |
| occupation_type | OCCUPATION_TYPE_idx=7 | 9813 | 4.83 | 0.2696 | 4.56 | 30.8 | 3.22 | 0.8521 | 0.2716 |
| occupation_type | OCCUPATION_TYPE_idx=8 | 8537 | 6.7 | 0.3308 | 8.15 | 44.23 | 5.56 | 0.8558 | 0.3531 |
| occupation_type | OCCUPATION_TYPE_idx=9 | 6721 | 10.74 | 0.4237 | 14.39 | 51.25 | 9.95 | 0.8318 | 0.3992 |
| occupation_type | OCCUPATION_TYPE_idx=10 | 5946 | 10.44 | 0.4164 | 15.02 | 51.21 | 10.8 | 0.8303 | 0.3799 |
| occupation_type | OCCUPATION_TYPE_idx=11 | 4653 | 9.61 | 0.3944 | 12.74 | 45.64 | 9.25 | 0.825 | 0.3752 |
| occupation_type | OCCUPATION_TYPE_idx=12 | 2652 | 6.6 | 0.3379 | 7.69 | 33.14 | 5.89 | 0.808 | 0.2494 |
| occupation_type | OCCUPATION_TYPE_idx=13 | 2093 | 17.15 | 0.5591 | 32.11 | 65.46 | 25.2 | 0.784 | 0.4175 |
| occupation_type | OCCUPATION_TYPE_idx=14 | 1348 | 11.28 | 0.4238 | 16.47 | 52.63 | 11.87 | 0.8232 | 0.4014 |
| occupation_type | OCCUPATION_TYPE_idx=15 | 1305 | 7.05 | 0.3288 | 7.43 | 33.7 | 5.44 | 0.8149 | 0.2688 |
| occupation_type | OCCUPATION_TYPE_idx=16 | 751 | 7.86 | 0.36 | 9.45 | 38.98 | 6.94 | 0.8393 | 0.2823 |
| occupation_type | OCCUPATION_TYPE_idx=17 | 563 | 6.39 | 0.2899 | 7.28 | 41.67 | 4.93 | 0.9074 | 0.4215 |
| occupation_type | OCCUPATION_TYPE_idx=18 | 526 | 6.46 | 0.3069 | 5.89 | 52.94 | 2.64 | 0.8857 | 0.4473 |

## Interpretation

Segment differences can reflect true historical default-rate differences, data quality patterns, model behavior, or social/proxy bias. A production lending model would require deeper fair-lending review, policy review, feature governance, reject-inference analysis, and legal/compliance sign-off.

For this portfolio project, the value is that segment performance is measured explicitly rather than hidden behind aggregate ROC-AUC or PR-AUC.

## Saved Outputs

- `reports/fairness_proxy_metrics.csv`
- `reports/fairness_proxy_analysis.md`
