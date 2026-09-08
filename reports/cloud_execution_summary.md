# Databricks Cloud Execution Evidence

Reviewed on 2026-09-08. Two user-supplied aggregate exports report completed Databricks baseline runs. The accompanying screenshot shows two successful manually launched jobs. This review compares the exported records and the referenced repository code; it did not access the workspace or rerun cloud training independently.

## Evidence

- [Earlier completed run](cloud_runs/aggregate_evidence_2688e7c56a8f4629820c6afd14cf1717.json)
- [Later completed run](cloud_runs/aggregate_evidence_1d8ef6a8d8b1444790bb17543fe4cccb.json)
- [Machine-readable comparison](cloud_runs/comparison.json)
- [Declared notebook source](https://github.com/Ansh1707/FinSight-Credit-Risk-ML/blob/2eed79e1c97d9839e8d8f53440b2e4866ac9a66a/cloud/databricks/workflow.py)

The JSONs contain aggregate counts, evaluation metrics, software versions, hashes, timestamps and opaque run identifiers. Their values are preserved; no applicant records, predictions, credentials, workspace URLs or account names are included. The screenshot is not published because it exposes an account identifier. Its success statuses and displayed durations are transcribed below. Identifiers in the screenshot are cropped, so its two rows cannot be independently mapped to these exact JSON run IDs.

## Reproducibility Comparison

| Check | Result in both records |
| --- | --- |
| Status / platform | completed / Databricks |
| Data SHA-256 | `f605df3d4e3a223bdfa06d3147afae6523cba09826595d4710c0759f0f638433` |
| Declared source revision | `2eed79e1c97d9839e8d8f53440b2e4866ac9a66a` |
| Source rows / sample rows | 20,000 / 20,000 |
| Features | 9 |
| Selected C / seed / class weight | 1.0 / 2026 / balanced |
| Selection rule | validation average precision |
| Train / validation / test counts | 12,000 / 4,000 / 4,000 |
| NumPy / pandas | 1.26.4 / 2.2.3 |
| scikit-learn / MLflow | 1.6.1 / 2.22.0 |
| Missingness / six metrics | Exact equality in parsed JSON values |

The referenced workflow fingerprints the sorted, transformed cloud DataFrame serialized to CSV, including identifiers and labels. This hash is not the local upload-file checksum and should not be compared directly with that checksum. The cloud source is the uploaded 20,000-row sample, not the complete 307,511-row Home Credit table. Split counts add up to 20,000 in each run; no additional independent test cohort is created by repeating the job.

## Model Results

| Metric | Validation | Test | Difference between runs |
| --- | ---: | ---: | ---: |
| ROC-AUC | 0.698279 | 0.720921 | 0 |
| Average precision (PR-AUC convention used here) | 0.189271 | 0.200987 | 0 |
| Brier score | 0.210361 | 0.208881 | 0 |

The notebook defines a balanced logistic regression baseline, with training-only median imputation and scaling. C is selected from 0.1, 1 and 10 using validation average precision. SQL/PySpark builds the application-level features; bounded pandas/scikit-learn performs training. This is a cloud baseline demonstration, not distributed model training or a deployment of the full local LightGBM champion. The metrics cannot be used as a controlled head-to-head comparison with that champion because the sample, feature set and split differ.

The baseline remains uncalibrated. Its Brier score of 0.208881 does not establish probability quality suitable for lending decisions; the exports lack split default rates and a constant-probability comparator. Calibration and business-threshold approval are still required for operational use. These runs do not establish financial uplift, fairness, Azure experience, Scala implementation, an online endpoint or production approval.

## Missing Values

Both runs report 3,607 missing employment-year values (18.035% of the sample), 18 missing external-score means (0.09%), and 2 missing values each for annuity and annuity-to-income ratio (0.01%). Other reported model columns have zero missing values. These are pre-imputation counts. In the referenced code, positive employment-day values, including the known sentinel, are converted to missing; the aggregate records do not separate sentinel cases from other causes. Training medians handle remaining model-input missingness.

## Expected Differences

| Field | Earlier completion | Later completion |
| --- | --- | --- |
| Output run key | `2688e7c56a8f4629820c6afd14cf1717` | `1d8ef6a8d8b1444790bb17543fe4cccb` |
| Completion (UTC) | 2026-09-08 01:31:09.308444 | 2026-09-08 01:32:24.948468 |
| Measured workflow seconds | 74.924266 | 30.784017 |

MLflow run IDs also differ, as expected for distinct runs. The screenshot displays job durations of 3m13s and 2m8s; no exact pairing to the JSON files is claimed. In the source, elapsed time begins inside run_cloud after argument checks and ends before final evidence writes. Job duration can include environment setup, earlier notebook cells, orchestration and finalization outside that interval. Cache reuse or environment warm-up could contribute to runtime variation, but these records do not diagnose the cause. Two runs are insufficient to claim a speedup or latency guarantee.

## Scope Of Verification

The exports support repeatability of recorded aggregate results across two reported cloud executions. They do not prove byte-identical trained artifacts or row-level predictions. The revision is entered through a widget, not measured from the running notebook. Job IDs, notebook content hashes, Spark/Python runtime versions, prediction hashes and model artifact hashes were not exported. A future stronger audit should capture those fields and tie them to authenticated job metadata. CLI bundle deployment was not demonstrated by these manual-job records.

## Supported Project Statement

Executed a Databricks credit-risk baseline training and scoring workflow on 20,000 public-data applicants using SQL/PySpark, scikit-learn and MLflow; two reported successful manual job runs produced identical recorded metrics and data fingerprints.

The evidence review and documentation publication did not retrain the local champion or modify applicant data.
