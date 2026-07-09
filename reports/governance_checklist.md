# FinSight Governance And Deployment Checklist

This checklist translates the model card into concrete controls a fintech data science reviewer would expect before a credit-risk model moves beyond a portfolio prototype.

## Current Governance Status

| area | status | evidence |
| --- | --- | --- |
| Business use defined | Complete for portfolio | README, final case study, model card |
| Model artifact saved | Complete | `models/credit_risk_model.pkl` |
| Validation metrics reported | Complete | `reports/final_model_report.md` |
| Cross-validation stability checked | Complete | `reports/cross_validation_summary.md` |
| Calibration assessed | Complete | `reports/calibration_report.md` |
| Explainability produced | Complete | `reports/explainability_summary.md` |
| Leakage audit performed | Complete for automated screen | `reports/leakage_audit.md` |
| Proxy-risk analysis performed | Complete for portfolio review | `reports/fairness_proxy_analysis.md` |
| Monitoring report produced | Complete for simulated windows | `reports/monitoring_summary.md` |
| API implemented | Complete for local serving | `src/api/main.py` |
| Production approval | Not complete | Requires business, risk, legal, compliance, and MLOps review |

## Intended Use Approval

- Confirm the model is used for risk ranking, manual review support, collections prioritization, monitoring, and explainability.
- Confirm the model is not used as a fully automated approval, rejection, or adverse-action engine.
- Document whether scores are used at application time, collections time, or both.
- Define the decision owner for any business action triggered by the score.

## Data And Feature Controls

- Verify raw data sources and refresh cadence.
- Validate that `TARGET`, `SK_ID_CURR`, `SK_ID_PREV`, and `SK_ID_BUREAU` are excluded from model inputs.
- Add source-record timestamp filters for bureau, previous application, installment, POS cash, and credit-card aggregates.
- Create a feature registry with feature name, source table, transformation, owner, availability time, and leakage-risk rating.
- Validate categorical encoding stability and behavior for unseen categories.
- Add schema checks for required columns, numeric ranges, missingness, and duplicate applicant identifiers.
- Re-run `python src/features/leakage_checks.py` after every feature engineering change.

## Model Validation Controls

- Re-run baseline and final model training from the processed dataset.
- Review ROC-AUC, PR-AUC, Recall, Precision, F1, Recall@Top-10%, KS statistic, and confusion matrix.
- Keep validation PR-AUC and Recall@Top-10% as ranking-focused selection metrics.
- Review calibration before using default probability as a policy threshold.
- Stress-test thresholds at realistic review capacity levels.
- Confirm model selection is not based on accuracy.
- Compare champion model against a simple interpretable baseline.

## Fairness And Compliance Controls

- Treat current proxy-risk analysis as a screening tool, not a legal audit.
- Review age-band, income-band, gender-proxy, education-proxy, family-status-proxy, and occupation-proxy gaps.
- Investigate segments with high top-10% review rates or large non-default review rates.
- Decide which features are prohibited, restricted, or require policy justification.
- Add reject-inference analysis before real lending deployment.
- Review adverse-action and reason-code requirements with compliance and legal teams.
- Document final approval or rejection of proxy-sensitive feature groups.

## Explainability Controls

- Keep global SHAP importance for model review.
- Keep applicant-level reason codes for analyst review.
- Ensure reason codes are based on actual positive model contributions.
- Map technical features to stable business-friendly reason text.
- Review reason codes for compliance suitability before customer-facing use.
- Track reason-code distribution over time for monitoring.

## API And Deployment Controls

- Confirm `/health`, `/predict`, `/batch_predict`, `/explain`, and `/model_info` endpoints run locally.
- Validate request and response schemas with representative applicants.
- Add authentication and authorization before any non-local deployment.
- Add request logging, prediction logging, model version logging, and correlation IDs.
- Add timeout, payload-size, and rate-limit controls.
- Validate Docker build and container startup.
- Define rollback procedure for a bad model or bad deployment.
- Store model artifacts in a controlled registry for production use.

## Monitoring Controls

- Define a stable reference window.
- Monitor feature drift with PSI or equivalent distribution checks.
- Monitor prediction drift and top-decile score movement.
- Monitor missingness-rate changes.
- Monitor labeled performance when outcomes mature.
- Monitor calibration drift for probability quality.
- Monitor segment-level review rates and reason-code distribution.
- Set alert thresholds, owners, and escalation paths.
- Define retraining and recalibration triggers.

## Production Deployment Checklist

Before production, every item below should be complete:

- [ ] Business owner approved intended use.
- [ ] Risk/compliance owner approved prohibited use boundaries.
- [ ] Raw data source contracts reviewed.
- [ ] Feature availability timestamps validated.
- [ ] Leakage audit passed with timestamp controls.
- [ ] Fair-lending and proxy-risk review completed.
- [ ] Calibration strategy selected.
- [ ] Threshold and review-capacity policy approved.
- [ ] API authentication and logging added.
- [ ] Model registry and versioning configured.
- [ ] Monitoring alerts configured.
- [ ] Rollback and incident process documented.
- [ ] Retraining and retirement criteria documented.
- [ ] Final sign-off recorded.

## Current Portfolio Conclusion

FinSight is strong as a portfolio-grade credit-risk and collections ML platform. It demonstrates the technical workflow expected from a fintech Data Scientist I candidate: PySpark feature engineering, SQL analysis, imbalanced classification, validation beyond accuracy, calibration, SHAP explanations, business prioritization, FastAPI serving, monitoring, dashboard outputs, and governance documentation.

It should be presented as a production-style prototype. A real lender would still require formal compliance review, fair-lending validation, data contracts, timestamp-based feature controls, model registry integration, and live monitoring operations before deployment.
