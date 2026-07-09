# Dashboard Summary

The dashboard layer uses Power BI-ready CSV files under `dashboard/dashboard_data/`.
Streamlit was not used because it is not installed in the current project environment, and adding a new dependency is unnecessary for this phase.

## How To Refresh Dashboard Data

```bash
python dashboard/build_dashboard_data.py
```

## Dashboard-Ready Files

- `dashboard/dashboard_data/kpi_summary.csv`: top-level portfolio, model, and monitoring KPIs.
- `dashboard/dashboard_data/risk_band_distribution.csv`: applicant counts, average default probabilities, and average priority scores by risk band.
- `dashboard/dashboard_data/collections_priority.csv`: top collections queue sample with probability, risk band, credit amount, priority score, and reason codes.
- `dashboard/dashboard_data/model_performance.csv`: validation and test model metrics.
- `dashboard/dashboard_data/top_model_features.csv`: top SHAP global model features.
- `dashboard/dashboard_data/high_risk_segments.csv`: risk-band and credit-amount segment summary.
- `dashboard/dashboard_data/monitoring_summary.csv`: monitoring checks extracted from the monitoring report.

## Recommended Dashboard Sections

1. Executive KPIs: total applicants analyzed, average default probability, critical-risk count, PR-AUC, Recall@Top-10%, and prediction PSI.
2. Risk Band Distribution: applicant count and average priority score by Low, Medium, High, and Critical Risk bands.
3. Collections Priority Queue: ranked applicant table for collections teams.
4. High-Risk Segments: risk band by credit amount bucket.
5. Model Performance: validation/test ROC-AUC, PR-AUC, Recall, F1-score, Recall@Top-10%, KS, and confusion matrix counts.
6. Model Drivers: SHAP global feature importance.
7. Monitoring: feature drift flags, missingness flags, prediction drift, and performance by monitoring window.

## Business Use

This dashboard layer translates the model into an operating view for credit-risk and collections stakeholders. It links applicant-level prioritization with model quality, explainability, and monitoring, which is the kind of production-aware data science workflow expected in fintech lending.
