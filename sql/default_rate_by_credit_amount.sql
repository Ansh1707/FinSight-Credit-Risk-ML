-- Default rate by requested credit amount bucket.
-- Business use: compare default risk across ticket-size bands.

WITH credit_buckets AS (
    SELECT
        CASE
            WHEN AMT_CREDIT IS NULL THEN 'Missing'
            WHEN AMT_CREDIT < 250000 THEN '< 250k'
            WHEN AMT_CREDIT < 500000 THEN '250k-500k'
            WHEN AMT_CREDIT < 750000 THEN '500k-750k'
            WHEN AMT_CREDIT < 1000000 THEN '750k-1M'
            ELSE '1M+'
        END AS credit_amount_bucket,
        CASE
            WHEN AMT_CREDIT IS NULL THEN 99
            WHEN AMT_CREDIT < 250000 THEN 1
            WHEN AMT_CREDIT < 500000 THEN 2
            WHEN AMT_CREDIT < 750000 THEN 3
            WHEN AMT_CREDIT < 1000000 THEN 4
            ELSE 5
        END AS bucket_order,
        TARGET
    FROM application_train
)
SELECT
    credit_amount_bucket,
    COUNT(*) AS applicant_count,
    SUM(TARGET) AS default_count,
    ROUND(AVG(TARGET) * 100, 2) AS default_rate_percent
FROM credit_buckets
GROUP BY credit_amount_bucket, bucket_order
ORDER BY bucket_order;
