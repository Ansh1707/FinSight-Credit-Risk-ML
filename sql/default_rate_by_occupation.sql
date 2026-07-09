-- Default rate by occupation type.
-- Business use: surface risk segments for collections queue design and monitoring.

SELECT
    COALESCE(OCCUPATION_TYPE, 'Missing') AS occupation_type,
    COUNT(*) AS applicant_count,
    SUM(TARGET) AS default_count,
    ROUND(AVG(TARGET) * 100, 2) AS default_rate_percent
FROM application_train
GROUP BY occupation_type
HAVING COUNT(*) >= 500
ORDER BY default_rate_percent DESC, applicant_count DESC;
