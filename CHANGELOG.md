# Changelog

All notable project changes are summarized here. This is a portfolio project, so versions represent repository maturity milestones rather than production releases.

## 0.21.0 - Final GitHub Polish

- Added `reports/github_polish_checklist.md` for README rendering, repository safety, ignored artifacts, final links, command snippets, portfolio presentation, and push readiness.
- Linked the GitHub polish checklist from README, reviewer guide, release checklist, final submission, roadmap, project brief, and final audit.
- Extended repository hygiene tests to validate local Markdown/report references and README fenced-code rendering basics.

## 0.20.0 - Executive Summary And Interview Defense

- Added recruiter-facing executive summary with 2-minute, 5-minute, and deep-dive formats.
- Added Navi Data Scientist I interview defense guide with likely questions, crisp answers, limitations, and closing narrative.
- Linked executive and interview artifacts from README, final submission note, reviewer guide, project brief, roadmap, release checklist, and final audit.

## 0.19.0 - Production Readiness Runbook

- Added production readiness runbook covering deployment, batch operations, monitoring cadence, alert thresholds, rollback, incidents, retraining triggers, ownership, and sign-off.
- Added machine-readable production readiness checklist with required gates, owner sign-offs, alert thresholds, and privacy controls.
- Linked runbook evidence across README, project brief, model card, governance checklist, reviewer guide, release checklist, and final audit.

## 0.18.0 - Batch Scoring And Prediction Logging

- Added production-style batch scoring using the saved final model without retraining.
- Added schema validation, model metadata, request IDs, batch IDs, score timestamps, risk bands, reason-code fields, and collections priority scores.
- Added privacy-safe prediction audit sample with hashed applicant identifiers and no raw feature values.

## 0.17.0 - Challenger Model Governance

- Added a less-sensitive challenger model workflow using the existing processed data and final-model split strategy.
- Removed restricted and enhanced-review protected/proxy features from the challenger feature set.
- Compared champion and challenger models with actual PR-AUC, Recall@Top-10%, KS, calibration, and business-impact metrics.

## 0.16.0 - Fair-Lending Governance Review

- Added formal fair-lending and proxy-risk governance review documentation without claiming legal certification.
- Added protected/proxy feature-control inventory covering restricted, review-required, monitoring-required, timestamp-controlled, and vendor-governance-required features.
- Documented segment-risk interpretation, production controls, compliance-ready limitations, and sign-off requirements.

## 0.15.0 - Reject Inference Methodology

- Added portfolio-safe reject inference methodology documentation.
- Documented accepted-applicant bias, missing rejected outcomes, interpretation impact, and production methods.
- Confirmed no rejected-applicant labels are invented and no model is retrained.

## 0.14.0 - Feature Registry And Timestamp Lineage

- Added generated feature registry for all final model features.
- Added timestamp-lineage documentation for application, bureau, bureau balance, previous application, installment, POS cash, credit-card, and categorical feature groups.
- Documented source tables, transformation logic, availability-time assumptions, leakage risk, and production controls.

## 0.13.0 - MLflow Tracking And Registry Docs

- Added optional MLflow tracking for existing final model artifacts without retraining.
- Added model registry-style JSON and Markdown records.
- Added MLflow experiment summary documentation.
- Ignored local `mlruns/` tracking store.

## 0.12.0 - Final Handoff

- Added final submission note.
- Added strict final project audit with scorecard, evidence checklist, repository safety audit, and production caveats.
- Linked final handoff artifacts from README, reviewer guide, project brief, roadmap, and release checklist.

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
