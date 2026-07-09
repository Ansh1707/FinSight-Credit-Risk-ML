-- High-risk customer segments from interpretable business attributes.
-- Business use: create candidate segments for monitoring, review, and collections prioritization.

WITH base AS (
    SELECT
        CASE
            WHEN AMT_INCOME_TOTAL < 100000 THEN 'Income < 100k'
            WHEN AMT_INCOME_TOTAL < 150000 THEN 'Income 100k-150k'
            ELSE 'Income >= 150k'
        END AS income_segment,
        CASE
            WHEN AMT_CREDIT < 250000 THEN 'Credit < 250k'
            WHEN AMT_CREDIT < 500000 THEN 'Credit 250k-500k'
            ELSE 'Credit >= 500k'
        END AS credit_segment,
        COALESCE(NAME_EDUCATION_TYPE, 'Missing') AS education_type,
        COALESCE(OCCUPATION_TYPE, 'Missing') AS occupation_type,
        CODE_GENDER,
        TARGET
    FROM application_train
),
segments AS (
    SELECT
        income_segment,
        credit_segment,
        education_type,
        occupation_type,
        CODE_GENDER,
        COUNT(*) AS applicant_count,
        SUM(TARGET) AS default_count,
        AVG(TARGET) AS default_rate
    FROM base
    GROUP BY
        income_segment,
        credit_segment,
        education_type,
        occupation_type,
        CODE_GENDER
)
SELECT
    income_segment,
    credit_segment,
    education_type,
    occupation_type,
    CODE_GENDER AS gender,
    applicant_count,
    default_count,
    ROUND(default_rate * 100, 2) AS default_rate_percent
FROM segments
WHERE applicant_count >= 500
ORDER BY default_rate_percent DESC, applicant_count DESC
LIMIT 25;
