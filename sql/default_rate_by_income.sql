-- Default rate by applicant income bucket.
-- Business use: compare repayment risk across affordability segments.

WITH income_buckets AS (
    SELECT
        CASE
            WHEN AMT_INCOME_TOTAL IS NULL THEN 'Missing'
            WHEN AMT_INCOME_TOTAL < 100000 THEN '< 100k'
            WHEN AMT_INCOME_TOTAL < 150000 THEN '100k-150k'
            WHEN AMT_INCOME_TOTAL < 200000 THEN '150k-200k'
            WHEN AMT_INCOME_TOTAL < 300000 THEN '200k-300k'
            ELSE '300k+'
        END AS income_bucket,
        CASE
            WHEN AMT_INCOME_TOTAL IS NULL THEN 99
            WHEN AMT_INCOME_TOTAL < 100000 THEN 1
            WHEN AMT_INCOME_TOTAL < 150000 THEN 2
            WHEN AMT_INCOME_TOTAL < 200000 THEN 3
            WHEN AMT_INCOME_TOTAL < 300000 THEN 4
            ELSE 5
        END AS bucket_order,
        TARGET
    FROM application_train
)
SELECT
    income_bucket,
    COUNT(*) AS applicant_count,
    SUM(TARGET) AS default_count,
    ROUND(AVG(TARGET) * 100, 2) AS default_rate_percent
FROM income_buckets
GROUP BY income_bucket, bucket_order
ORDER BY bucket_order;
