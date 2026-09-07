# Statistical Validation

Actual saved-model predictions: 61,503 test applicants; 4,965 defaults. No ranking model was retrained.

## Paired 95% Confidence Intervals

1,000 label-stratified applicant bootstrap replicates, seed 42. Both models use the same resampled applicants. PR-AUC here means average precision.

| comparison | metric | estimate | lower_95 | upper_95 |
| --- | --- | --- | --- | --- |
| champion | roc_auc | 0.7765 | 0.7699 | 0.7829 |
| champion | average_precision | 0.264 | 0.2533 | 0.2756 |
| champion | recall_at_top_10pct | 0.3593 | 0.3474 | 0.371 |
| champion | ks | 0.4123 | 0.4012 | 0.4276 |
| champion | brier | 0.1645 | 0.1631 | 0.1658 |
| champion | ece | 0.2742 | 0.2725 | 0.2758 |
| challenger | roc_auc | 0.7703 | 0.7641 | 0.7767 |
| challenger | average_precision | 0.2559 | 0.2458 | 0.2676 |
| challenger | recall_at_top_10pct | 0.3488 | 0.337 | 0.3609 |
| challenger | ks | 0.4013 | 0.3899 | 0.4146 |
| challenger | brier | 0.1678 | 0.1662 | 0.1691 |
| challenger | ece | 0.2793 | 0.2775 | 0.2808 |
| challenger_minus_champion | roc_auc | -0.0062 | -0.0081 | -0.004 |
| challenger_minus_champion | average_precision | -0.0081 | -0.0115 | -0.0043 |
| challenger_minus_champion | recall_at_top_10pct | -0.0105 | -0.0171 | -0.004 |
| challenger_minus_champion | ks | -0.0109 | -0.0185 | -0.0034 |
| challenger_minus_champion | brier | 0.0033 | 0.0029 | 0.0037 |
| challenger_minus_champion | ece | 0.0051 | 0.0046 | 0.0056 |

Positive challenger-minus-champion differences favor the challenger for ranking; negative differences favor it for Brier/ECE. Intervals containing zero do not establish a directional difference. These are marginal intervals, without multiplicity adjustment; fairness and financial impact are not established by predictive differences.

## Calibration Selection

| method | selection_brier |
| --- | --- |
| uncalibrated | 0.1639 |
| platt_sigmoid | 0.0667 |
| isotonic | 0.0666 |

Selected `isotonic` by Brier on a held-out half of the original validation split. Calibrators fit on the other half. Refit the selected method on the whole validation split before reporting test metrics.

| roc_auc | average_precision | recall_at_top_10pct | ks | brier | ece |
| --- | --- | --- | --- | --- | --- |
| 0.776 | 0.254 | 0.3547 | 0.411 | 0.0668 | 0.0023 |

This corrects future method-selection logic, not historical test reuse. The champion was already tuned using this validation set, and test results were previously inspected. This is retrospective supporting analysis, not a new untouched evaluation. A future experiment needs development-only tuning, out-of-fold calibration selection, and a locked temporal test cohort.

## Assumptions And Limits

One independent applicant per row is assumed. Household dependence requires cluster bootstrap; temporal dependence requires time-block evaluation. Intervals condition on observed class prevalence, fixed trained models and preprocessing; they exclude training, selection and future distribution-shift uncertainty. Historical source timing assumptions remain unresolved. Reconstructed splits reproduce stored PR-AUC but original artifacts lack row-level split manifests.

## Probability In Plain Language

Among many comparable applicants scored at 70%, about 70 out of 100 should default over the defined outcome window if probabilities are calibrated. It is not a guarantee for one person. A reliability plot compares average predicted probability with observed default frequency in each bin; points above the diagonal indicate underestimated risk. Brier measures squared probability error and reflects discrimination as well as calibration. ECE depends on binning. Calibration cannot repair missing populations, timing leakage or a changed outcome window.

The selected transform is evaluated here only; the deployed champion artifact is unchanged. Do not describe API scores as newly calibrated based on this report.
