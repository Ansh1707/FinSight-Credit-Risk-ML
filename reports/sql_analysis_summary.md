# SQL Analysis Summary

This report is generated with DuckDB from `data/raw/application_train.csv`. Raw data is read only and is not modified.

## Top Business Findings

1. Income segmentation shows the highest default rate in the 100k-150k bucket at 8.62%, compared with 5.95% in 300k+. This supports affordability-focused monitoring.
2. Education type has clear risk separation: Lower secondary has a 10.93% default rate across 3,816 applicants.
3. Credit amount buckets are not monotonic; the highest bucket-level default rate is 9.46% for 500k-750k. Ticket size should be combined with income, annuity burden, and bureau behavior instead of used alone.
4. Occupation segmentation highlights Low-skill Laborers as the highest-risk occupation group with a 17.15% default rate across 2,093 applicants.
5. The highest combined high-risk segment is Income < 100k, Credit 250k-500k, Secondary / secondary special, Laborers, gender M, with a 15.68% default rate across 1,084 applicants. This is useful for portfolio monitoring and collections prioritization, not as a hard approval rule.

## Default Rate by Income Bucket

| income_bucket | applicant_count | default_count | default_rate_percent |
| --- | --- | --- | --- |
| < 100k | 63698 | 5225.0 | 8.2 |
| 100k-150k | 91591 | 7894.0 | 8.62 |
| 150k-200k | 64307 | 5432.0 | 8.45 |
| 200k-300k | 65176 | 4921.0 | 7.55 |
| 300k+ | 22739 | 1353.0 | 5.95 |

## Default Rate by Education Type

| education_type | applicant_count | default_count | default_rate_percent |
| --- | --- | --- | --- |
| Lower secondary | 3816 | 417.0 | 10.93 |
| Secondary / secondary special | 218391 | 19524.0 | 8.94 |
| Incomplete higher | 10277 | 872.0 | 8.48 |
| Higher education | 74863 | 4009.0 | 5.36 |
| Academic degree | 164 | 3.0 | 1.83 |

## Default Rate by Credit Amount Bucket

| credit_amount_bucket | applicant_count | default_count | default_rate_percent |
| --- | --- | --- | --- |
| < 250k | 59198 | 4220.0 | 7.13 |
| 250k-500k | 90135 | 8385.0 | 9.3 |
| 500k-750k | 65094 | 6159.0 | 9.46 |
| 750k-1M | 43099 | 3129.0 | 7.26 |
| 1M+ | 49985 | 2932.0 | 5.87 |

## Default Rate by Occupation Type

| occupation_type | applicant_count | default_count | default_rate_percent |
| --- | --- | --- | --- |
| Low-skill Laborers | 2093 | 359.0 | 17.15 |
| Drivers | 18603 | 2107.0 | 11.33 |
| Waiters/barmen staff | 1348 | 152.0 | 11.28 |
| Security staff | 6721 | 722.0 | 10.74 |
| Laborers | 55186 | 5838.0 | 10.58 |
| Cooking staff | 5946 | 621.0 | 10.44 |
| Sales staff | 32102 | 3092.0 | 9.63 |
| Cleaning staff | 4653 | 447.0 | 9.61 |
| Realty agents | 751 | 59.0 | 7.86 |
| Secretaries | 1305 | 92.0 | 7.05 |
| Medicine staff | 8537 | 572.0 | 6.7 |
| Private service staff | 2652 | 175.0 | 6.6 |
| Missing | 96391 | 6278.0 | 6.51 |
| IT staff | 526 | 34.0 | 6.46 |
| HR staff | 563 | 36.0 | 6.39 |
| Core staff | 27570 | 1738.0 | 6.3 |
| Managers | 21371 | 1328.0 | 6.21 |
| High skill tech staff | 11380 | 701.0 | 6.16 |
| Accountants | 9813 | 474.0 | 4.83 |

## High-Risk Customer Segments

| income_segment | credit_segment | education_type | occupation_type | gender | applicant_count | default_count | default_rate_percent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Income < 100k | Credit 250k-500k | Secondary / secondary special | Laborers | M | 1084 | 170.0 | 15.68 |
| Income < 100k | Credit >= 500k | Secondary / secondary special | Laborers | M | 702 | 107.0 | 15.24 |
| Income 100k-150k | Credit 250k-500k | Secondary / secondary special | Laborers | M | 3137 | 475.0 | 15.14 |
| Income < 100k | Credit 250k-500k | Secondary / secondary special | Cooking staff | F | 526 | 79.0 | 15.02 |
| Income 100k-150k | Credit 250k-500k | Secondary / secondary special | Drivers | M | 1545 | 208.0 | 13.46 |
| Income 100k-150k | Credit >= 500k | Secondary / secondary special | Drivers | M | 1736 | 229.0 | 13.19 |
| Income 100k-150k | Credit >= 500k | Secondary / secondary special | Security staff | M | 577 | 76.0 | 13.17 |
| Income >= 150k | Credit 250k-500k | Secondary / secondary special | Drivers | M | 2624 | 345.0 | 13.15 |
| Income >= 150k | Credit 250k-500k | Secondary / secondary special | Laborers | M | 4309 | 565.0 | 13.11 |
| Income 100k-150k | Credit < 250k | Secondary / secondary special | Laborers | M | 1964 | 236.0 | 12.02 |
| Income 100k-150k | Credit 250k-500k | Secondary / secondary special | Missing | M | 1626 | 195.0 | 11.99 |
| Income >= 150k | Credit >= 500k | Secondary / secondary special | Laborers | M | 9098 | 1038.0 | 11.41 |
| Income 100k-150k | Credit >= 500k | Secondary / secondary special | Laborers | M | 3139 | 358.0 | 11.4 |
| Income < 100k | Credit 250k-500k | Secondary / secondary special | Sales staff | F | 2080 | 236.0 | 11.35 |
| Income < 100k | Credit 250k-500k | Secondary / secondary special | Laborers | F | 1723 | 192.0 | 11.14 |
| Income < 100k | Credit < 250k | Secondary / secondary special | Laborers | M | 1285 | 143.0 | 11.13 |
| Income < 100k | Credit 250k-500k | Secondary / secondary special | Missing | M | 1324 | 146.0 | 11.03 |
| Income 100k-150k | Credit 250k-500k | Secondary / secondary special | Sales staff | F | 2716 | 295.0 | 10.86 |
| Income >= 150k | Credit 250k-500k | Secondary / secondary special | Sales staff | F | 2116 | 226.0 | 10.68 |
| Income 100k-150k | Credit 250k-500k | Secondary / secondary special | Cooking staff | F | 574 | 61.0 | 10.63 |
| Income >= 150k | Credit >= 500k | Secondary / secondary special | Drivers | M | 6058 | 643.0 | 10.61 |
| Income < 100k | Credit 250k-500k | Secondary / secondary special | Medicine staff | F | 604 | 64.0 | 10.6 |
| Income >= 150k | Credit < 250k | Secondary / secondary special | Drivers | M | 965 | 102.0 | 10.57 |
| Income 100k-150k | Credit < 250k | Secondary / secondary special | Drivers | M | 925 | 97.0 | 10.49 |
| Income < 100k | Credit 250k-500k | Secondary / secondary special | Cleaning staff | F | 515 | 54.0 | 10.49 |

## Notes

- SQL outputs are descriptive business analysis, not model metrics.
- Segment differences should guide feature engineering, validation, and monitoring.
- No model training was performed in this phase.
