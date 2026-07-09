# Changelog

All notable project changes are summarized here. This is a portfolio project, so versions represent repository maturity milestones rather than production releases.

## 0.11.0 - GitHub Maintenance Polish

- Added MIT license.
- Added contributor guidance for local setup, raw-data safety, testing, and pull requests.
- Added security policy explaining secret, data, and vulnerability handling.
- Added GitHub issue templates and pull request template.
- Added this changelog for release-history visibility.

## 0.10.0 - Reviewer Readiness

- Added `REVIEW_GUIDE.md` for recruiter and interviewer review.
- Added `RELEASE_CHECKLIST.md` for GitHub safety, presentation, and final manual checks.

## 0.9.0 - Model Governance

- Added professional model card.
- Added governance and deployment checklist.
- Documented intended use, prohibited use, validation evidence, calibration, fairness/proxy-risk analysis, leakage audit, monitoring plan, limitations, and deployment readiness.

## 0.8.0 - Leakage Audit

- Added automated model feature leakage audit.
- Documented forbidden identifiers, high-risk leakage keywords, and medium-risk historical aggregate timing assumptions.

## 0.7.0 - Proxy-Risk And Fairness Review

- Added segment-performance analysis across age, income, and encoded categorical proxies.
- Documented segment review-rate gaps without claiming legal fair-lending certification.

## 0.6.0 - Business Impact And Calibration

- Added review-capacity business impact analysis.
- Added Platt/sigmoid and isotonic calibration comparison.
- Added cross-validation stability checks.

## 0.5.0 - Final Model, Explainability, API, Monitoring, Dashboard

- Trained and validated final LightGBM model.
- Added SHAP reason codes.
- Added collections scoring.
- Added FastAPI serving layer.
- Added monitoring reports.
- Added dashboard-ready outputs.

## 0.1.0 - Initial End-To-End Scaffold

- Created project scaffold, data loading, EDA, SQL analysis, PySpark feature engineering, baseline modeling, and initial documentation.
