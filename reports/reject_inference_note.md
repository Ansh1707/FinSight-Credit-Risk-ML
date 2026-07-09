# Reject Inference Methodology Note

This report documents accepted-applicant bias and reject inference considerations for FinSight. It does not create labels for rejected applicants, does not retrain models, and does not modify raw data.

## Current Portfolio Scope

| field | value |
| --- | --- |
| accepted_applicant_rows | 307511 |
| model_type | lightgbm |
| selection_metric | validation_pr_auc |
| feature_count | 76 |
| test_roc_auc | 0.7764561203602978 |
| test_pr_auc | 0.2639813012708453 |
| test_recall_at_top_10pct | 0.35931520644511583 |
| test_ks_statistic | 0.41226513002671034 |

## Why Reject Inference Matters

Credit-risk models are usually trained on applicants who were approved, booked, or otherwise observed after a lending decision. Applicants who were rejected do not generate repayment outcomes for the lender, so their true default behavior is missing. This creates accepted-applicant bias: the training data reflects historical approval policy, not the full through-the-door applicant population.

## What Is Missing

- Rejected-applicant repayment outcomes are not observed in this dataset.
- Rejected-applicant labels are not inferable from `application_train.csv` alone.
- The current validation metrics measure performance on the observed accepted/booked population.
- The project does not use `application_test.csv` or Kaggle submission labels.

## Portfolio-Safe Decision

Do not invent rejected-applicant labels. Document the selection-bias limitation and define production methods that require additional data, policy review, and compliance approval.

## Interpretation Impact

- Validation metrics are conditional on the observed accepted/booked population.
- Default probabilities should not be interpreted as fully through-the-door population risk.
- Thresholds and calibration may shift if rejected applicants are later included.
- Fairness and segment conclusions may be incomplete if rejected applicants differ by segment.

## Production Methods

| method | description | benefit | risk | portfolio_status |
| --- | --- | --- | --- | --- |
| Parceling | Assign inferred good/bad outcomes to rejected applicants within score bands using observed accepted-applicant bad rates adjusted by policy or bureau evidence. | Simple to explain and commonly discussed in credit-risk workflows. | Can reinforce historical policy bias if parceling assumptions are wrong. | documented_only_not_applied |
| Fuzzy augmentation | Add rejected applicants multiple times with fractional outcome weights based on estimated default probability or external performance signals. | Captures uncertainty rather than forcing a single inferred label. | Requires strong assumptions and careful calibration; can overstate certainty. | documented_only_not_applied |
| Bureau or alternative outcome matching | Use later bureau performance or external repayment/default signals to observe whether rejected applicants defaulted elsewhere. | Anchors rejected outcomes in observed external behavior. | Requires data contracts, identity matching, observation windows, and consent/legal review. | production_candidate_requires_data |
| Exploration or randomized policy holdout | Approve a controlled, risk-managed sample near the decision boundary to observe future repayment outcomes. | Produces cleaner labels for policy expansion and bias reduction. | Requires risk appetite, ethics review, operational controls, and compliance approval. | production_candidate_requires_governance |
| Two-stage selection modeling | Model approval/acceptance probability and use inverse-probability or selection-bias corrections when estimating default risk. | Explicitly models the accepted-applicant selection mechanism. | Requires rejected-applicant features and a reliable acceptance policy history. | documented_only_not_applied |

## Recommended Production Approach

1. Preserve the current model as an accepted-population risk-ranking baseline.
2. Store rejected-applicant application features with decision timestamp and reason.
3. Obtain compliant external outcome data or create a controlled exploration policy.
4. Compare baseline, parceling, fuzzy augmentation, and selection-model approaches.
5. Re-evaluate PR-AUC, Recall@Top-K, KS, calibration, fairness/proxy-risk, and business impact.
6. Require risk, legal, compliance, and model governance sign-off before policy use.

## What This Means For FinSight

FinSight should be presented as a strong accepted-applicant credit-risk and collections prioritization platform. It should not be described as a fully unbiased through-the-door underwriting model until rejected applicant outcomes or approved reject-inference assumptions are added.

## Saved Outputs

- `reports/reject_inference_note.md`
- `reports/reject_inference_methodology.json`
