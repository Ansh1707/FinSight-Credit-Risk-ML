# PROJECT_BRIEF.md

## Project Title

FinSight — Explainable Credit Risk & Collections ML Platform

## Target Role

Data Scientist I at Navi.

## Business Problem

A fintech lending company needs to predict which loan applicants are likely to default and prioritize high-risk customers for manual review or collections. The model must be accurate, explainable, monitored, and useful to business stakeholders.

## ML Problem

Binary classification.

Input:

* customer/application-level loan data
* bureau history
* previous application data
* repayment behavior data

Output:

* probability of default
* risk band
* reason codes
* collections priority score

## Dataset

Use the Home Credit Default Risk dataset.

Assume these files are stored locally under `data/raw/`:

* application_train.csv
* HomeCredit_columns_description.csv
* bureau.csv
* bureau_balance.csv
* previous_application.csv
* installments_payments.csv
* POS_CASH_balance.csv
* credit_card_balance.csv

Do not use `application_test.csv` or `sample_submission.csv`. This is not a Kaggle submission project. Use `application_train.csv` and create our own train/validation/test split.

## Expected Outputs

* EDA report
* SQL business analysis
* PySpark feature engineering pipeline
* model comparison report
* trained credit-risk model
* SHAP reason codes
* collections priority scoring module
* FastAPI inference service
* model monitoring reports
* dashboard or dashboard-ready output
* final README with resume-ready explanation

## Final Project Outputs

The implemented project produces:

* `data/processed/model_features.parquet` with `307,511` applicant rows and `78` columns
* feature registry and timestamp-lineage documentation under `reports/feature_registry.csv` and `reports/feature_registry.md`
* `models/credit_risk_model.pkl` as the final tuned LightGBM model
* `reports/final_model_metrics.json` and `reports/final_model_report.md`
* SHAP plots and applicant-level reason codes under `reports/`
* collections priority outputs under `reports/collections_priority_sample.csv`
* FastAPI service under `src/api/`
* monitoring reports under `reports/monitoring_summary.md`, `reports/monitoring_report.html`, and `reports/drift_report.html`
* Power BI-ready dashboard data under `dashboard/dashboard_data/`
* leakage audit report under `reports/leakage_audit.md`
* model governance artifacts under `reports/model_card.md` and `reports/governance_checklist.md`
* MLflow tracking and registry-style documentation under `reports/mlflow_experiment_summary.md`, `reports/model_registry.md`, and `reports/model_registry.json`
* reject inference methodology documentation under `reports/reject_inference_note.md` and `reports/reject_inference_methodology.json`
* fair-lending and proxy-risk governance review under `reports/fair_lending_review.md`, `reports/proxy_feature_controls.csv`, and `reports/fair_lending_governance.json`
* reviewer and release-readiness documentation under `REVIEW_GUIDE.md` and `RELEASE_CHECKLIST.md`
* repository maintenance files including `LICENSE`, `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, and GitHub issue/PR templates
* final handoff artifacts under `FINAL_SUBMISSION.md` and `reports/final_project_audit.md`

## Success Metrics

Model metrics:

* ROC-AUC
* PR-AUC
* Precision
* Recall
* F1-score
* Recall@Top-K
* KS statistic
* calibration curve

Business outputs:

* risk bands
* top default drivers
* high-risk applicant segments
* collections priority ranking
* monitoring summary

## Final Resume Goal

The final project should support resume bullets showing PySpark, SQL, credit risk modeling, model validation, explainability, FastAPI deployment, and model monitoring.

## Final Model Snapshot

The final tuned LightGBM model was selected by validation PR-AUC.

| split | ROC-AUC | PR-AUC | Precision | Recall | F1 | Recall@Top-10% | KS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| validation | 0.7799 | 0.2712 | 0.2941 | 0.3644 | 0.3255 | 0.3644 | 0.4194 |
| test | 0.7765 | 0.2640 | 0.2908 | 0.3577 | 0.3208 | 0.3593 | 0.4123 |

These metrics are actual computed results from the saved project reports. Accuracy is intentionally not used as the main metric.

## Cross-Validation Snapshot

The final LightGBM configuration was checked with stratified 5-fold validation on the full processed dataset.

| metric | mean | std | min | max |
| --- | ---: | ---: | ---: | ---: |
| ROC-AUC | 0.7830 | 0.0044 | 0.7782 | 0.7893 |
| PR-AUC | 0.2745 | 0.0074 | 0.2651 | 0.2854 |
| Recall@Top-10% | 0.3646 | 0.0074 | 0.3577 | 0.3772 |
| KS statistic | 0.4276 | 0.0104 | 0.4146 | 0.4419 |

## Calibration Snapshot

Calibration was evaluated by fitting Platt/sigmoid and isotonic transforms on the validation split and evaluating on the test split.

| method | test Brier | test ECE | test ROC-AUC | test PR-AUC | test Recall@Top-10% |
| --- | ---: | ---: | ---: | ---: | ---: |
| Uncalibrated | 0.1645 | 0.2742 | 0.7765 | 0.2640 | 0.3593 |
| Platt/sigmoid | 0.0669 | 0.0062 | 0.7765 | 0.2640 | 0.3593 |
| Isotonic | 0.0668 | 0.0023 | 0.7760 | 0.2540 | 0.3547 |

Platt/sigmoid calibration is the preferred balanced option for calibrated probability reporting because it improves Brier score and expected calibration error while preserving the model's ranking metrics.

## Business Impact Snapshot

Collections capacity analysis ranks applicants by final model probability and evaluates how many observed defaults are captured at different review queue sizes. At a `10%` review capacity, the model reviews `30,752` applicants and captures `10,853` observed defaults, or `43.72%` of all defaults. This is `4.37x` the default capture expected from random review at the same queue size.

| review capacity | applicants reviewed | defaults captured | default capture rate | lift vs random |
| --- | ---: | ---: | ---: | ---: |
| Top 5% | 15,376 | 6,715 | 27.05% | 5.41x |
| Top 10% | 30,752 | 10,853 | 43.72% | 4.37x |
| Top 15% | 46,127 | 14,029 | 56.51% | 3.77x |
| Top 20% | 61,503 | 16,376 | 65.97% | 3.30x |

## Fairness and Proxy-Risk Snapshot

Segment analysis was added to measure model behavior across age, income, and encoded categorical proxy groups. The current local run used processed encoded category proxies because raw application category files are intentionally ignored and were not available locally.

Important findings:

* `OCCUPATION_TYPE_idx=13` has the highest top-10% review rate at `32.11%`, with observed default rate `17.15%`.
* Age band `18-25` has top-10% review rate `22.50%`, with observed default rate `12.29%`.
* Encoded gender proxy `CODE_GENDER_idx=1` has top-10% review rate `14.03%`, compared with `7.91%` for `CODE_GENDER_idx=0`.

This is a proxy segment-performance review, not a regulatory fairness audit. Production use would require legal/compliance review, policy review, approved feature governance, reject-inference analysis, and documented sign-off.

## Fair-Lending Governance Snapshot

The project includes a formal portfolio governance review:

* `reports/fair_lending_review.md`
* `reports/proxy_feature_controls.csv`
* `reports/fair_lending_governance.json`

The review converts existing segment metrics and the feature registry into protected/proxy feature controls and production sign-off requirements. It reviews `76` model features and `41` segment metric rows. It explicitly does not claim legal fair-lending certification, does not approve adverse-action language, does not infer protected-class membership, and does not retrain the model.

Current feature-control summary:

* `1` gender proxy feature restricted pending fair-lending approval.
* `2` age-related features restricted pending policy approval.
* `5` socioeconomic/employment categorical proxies requiring fair-lending review.
* `7` region/social-network proxies requiring enhanced review.
* `32` historical credit-behavior features requiring timestamp controls.

## Reject Inference Snapshot

The project includes a portfolio-safe reject inference methodology note:

* `reports/reject_inference_note.md`
* `reports/reject_inference_methodology.json`

The analysis explains accepted-applicant bias, why rejected-applicant outcomes are missing, why labels are not invented, and how production teams could approach reject inference through parceling, fuzzy augmentation, bureau outcome matching, controlled exploration, or two-stage selection modeling. No rejected-applicant labels are created and no model is retrained.

## Leakage Governance Snapshot

The saved final model feature list was audited for obvious target leakage. The automated check passed on the current artifacts:

* Model input features checked: `76`
* Forbidden target or identifier inputs found: `0`
* Model features missing from the processed table: `0`
* High-risk outcome-keyword features found: `0`
* Medium-risk historical aggregate features: `32`

The medium-risk features are historical bureau, prior application, repayment, POS cash, and credit-card aggregates. They are acceptable for this portfolio build, but production use would require source-record timestamp filters and feature-lineage review to prove every signal was available before the credit decision or collections scoring timestamp.

## Feature Registry Snapshot

The project includes a generated feature registry:

* `reports/feature_registry.csv`
* `reports/feature_registry.md`

The registry documents `76` final model features by feature group, source table, source columns, transformation logic, join key, aggregation level, availability time, leakage risk, owner, and production controls. It makes the timestamp-lineage assumptions explicit for bureau, bureau balance, previous application, installment repayment, POS cash, and credit-card feature groups.

## Governance Snapshot

The project now includes a professional model card and governance checklist:

* `reports/model_card.md`
* `reports/governance_checklist.md`

These documents cover intended use, prohibited use, training data, feature groups, validation metrics, calibration, explainability, proxy-risk findings, fair-lending governance, leakage audit results, monitoring plan, limitations, deployment checklist, ownership expectations, rollback needs, and production sign-off requirements.

## Reviewer Readiness Snapshot

The repository includes:

* `REVIEW_GUIDE.md` for a fast recruiter or interviewer walkthrough.
* `RELEASE_CHECKLIST.md` for safe GitHub sharing and final push checks.

These files help reviewers understand the strongest project evidence quickly while documenting what is intentionally excluded from Git, such as raw data, processed data, trained model binaries, virtual environments, and large HTML reports.

## Repository Maintenance Snapshot

The repository includes open-source-style maintenance files:

* `LICENSE`
* `CHANGELOG.md`
* `CONTRIBUTING.md`
* `SECURITY.md`
* `.github/PULL_REQUEST_TEMPLATE.md`
* `.github/ISSUE_TEMPLATE/`

These artifacts make the repository easier to inspect, maintain, and safely share as a professional portfolio project.

## Final Handoff Snapshot

The final handoff files are:

* `FINAL_SUBMISSION.md`
* `reports/final_project_audit.md`

The final audit rates FinSight at `99/100` as a portfolio project, with explicit remaining production gaps around live data contracts, legal fair-lending certification, adverse-action compliance approval, applied reject inference with compliant rejected-applicant outcomes, production enforcement of timestamp cutoffs, authentication, production-grade registry approval workflow, production monitoring, and incident ownership.

## MLflow and Registry Snapshot

The project includes `src/models/mlflow_tracking.py`, which logs existing final model parameters, validation/test metrics, and report artifacts to MLflow when MLflow is installed. It does not retrain the model.

Generated outputs:

* `reports/mlflow_experiment_summary.md`
* `reports/model_registry.md`
* `reports/model_registry.json`

The local `mlruns/` tracking store is ignored by Git. The script uses a local SQLite backend at `sqlite:///mlruns/mlflow.db` to avoid MLflow's deprecated filesystem tracking backend.
