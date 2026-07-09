-- Default rate by education type.
-- Business use: identify broad risk patterns for monitoring and policy review.

SELECT
    COALESCE(NAME_EDUCATION_TYPE, 'Missing') AS education_type,
    COUNT(*) AS applicant_count,
    SUM(TARGET) AS default_count,
    ROUND(AVG(TARGET) * 100, 2) AS default_rate_percent
FROM application_train
GROUP BY education_type
ORDER BY default_rate_percent DESC, applicant_count DESC;
