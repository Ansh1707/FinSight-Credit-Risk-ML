# FinSight Databricks Workflow

Status: prepared and locally tested; no cloud execution claimed. Databricks Free Edition provides serverless compute subject to quotas. This workflow demonstrates Databricks, not Azure. See [Free Edition limitations](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations).

## Architecture

```text
Local public-data sample (ignored CSV)
  -> Unity Catalog source table (unchanged)
  -> serverless notebook: Spark schema checks + SQL risk features
  -> bounded pandas sample: stratified 60/20/20 split
  -> training-only median imputer + scaler + balanced logistic regression
  -> validation average precision selects C from [0.1, 1, 10]
  -> one test evaluation + MLflow model/metrics
  -> run-specific Delta features, split manifest and test predictions
  -> Unity Catalog volume: aggregate JSON evidence
```

This is a new small application-table baseline, not a migration or retraining of the 76-feature champion. It uses 9 numeric features, including income ratios, age, employment and external-score mean. Employment sentinel/positive days become missing. Zero income produces missing ratios; training medians handle missing predictors. Scores are class-weighted, uncalibrated baseline probabilities. Existing proxy, selection-bias and timing limitations still apply. No Scala code or Azure resources are introduced.

Malformed numeric predictor values are converted to missing and included in missingness counts; invalid IDs or labels fail validation. Missingness counts are diagnostic, not production acceptance thresholds. Define approved feature-quality limits before operational use.

## Step 1: Prepare Data Locally

From the repository root:

```bash
source .venv/bin/activate
python -m src.data.prepare_cloud_sample --limit 20000
```

The script scans required columns in chunks and keeps the 20,000 smallest deterministic applicant-ID hashes. Selection does not use TARGET. It records actual source/sample counts, package versions and file SHA-256 in `reports/cloud_sample_manifest.json`. Upload `data/processed/cloud_sample.csv` only after confirming dataset terms permit use in your workspace. It remains Git-ignored. Source rows are never modified.

## Step 2: Create Workspace Storage

1. Create your Databricks Free Edition account and sign in.
2. In Catalog Explorer, choose a writable catalog and create a `finsight` schema and `evidence` volume. Record their names privately.
3. Use the upload/create-table UI to upload the ignored sample CSV as a managed table, for example `workspace.finsight.application_sample`. Check inferred columns and TARGET values. The exact catalog may differ.
4. Create a workspace MLflow experiment and record its path. Keep all applicant data, predictions, IDs and split records within your workspace.

Use only a workspace/environment you control. There is no continuously running endpoint.

## Step 3: Import And Run Notebook

Import `workflow.py` as a Python source notebook. Select serverless compute. In the notebook Environment panel, add `scikit-learn==1.6.1`, `pandas==2.2.3`, `numpy==1.26.4`, and `mlflow==2.22.0`; apply/restart as requested. Do not install the repository's pinned local PySpark into Databricks; use its supplied Spark session. If the environment rejects these dependencies, stop and record the error before changing versions. The actual resolved versions are saved in every run.

Set widgets:

| Parameter | Value |
| --- | --- |
| input_table | Your `catalog.schema.application_sample` |
| output_schema | Your `catalog.finsight` |
| experiment_name | Your existing workspace experiment path |
| evidence_volume | Your volume path, such as `/Volumes/workspace/finsight/evidence` |
| max_rows | `20000` |
| revision | Exact output of `git rev-parse HEAD` for the code you imported |

Cloud paths are supplied at runtime; no local absolute paths are embedded in code. Run all cells. Confirm MLflow parameters/metrics/model appear, three new Delta tables exist (features, splits, predictions), and one aggregate evidence JSON appears in the volume. Failure must remain visible; the notebook does not report success if an output write fails.

## Step 4: Create And Rerun A Job

If an earlier notebook fails with `[UNSUPPORTED_OPERATION] errorifexists is not supported`, import the updated `workflow.py`. The output writer now uses SQL `CREATE TABLE ... USING DELTA AS SELECT`, with unique table names per run and no overwrite. MLflow logging also includes the model signature. An uploaded MLflow artifact alone does not mean the entire workflow succeeded. Preserve your widget values, update `revision` to the imported code's commit, and rerun all cells. Partial failed runs can remain for diagnosis; each rerun gets new output names.

The UI is the simplest first route: choose **Schedule / Create job** from the notebook, use a manual trigger and serverless compute, copy the same parameters, and run twice. Confirm the job uses the notebook dependency environment. Both executions must finish successfully with the same input snapshot and code revision. This is a reproducibility check, not a second independent model evaluation.

For CLI-managed deployment, install the current [Databricks CLI](https://docs.databricks.com/aws/en/dev-tools/cli/install), then use the bundled configuration. Authenticate with browser OAuth; never paste tokens into this repository.

```bash
databricks auth login --host https://YOUR-WORKSPACE-HOST
cd cloud/databricks
databricks bundle validate --var 'input_table=CATALOG.finsight.application_sample,output_schema=CATALOG.finsight,experiment_name=/Workspace/YOUR_EXPERIMENT,evidence_volume=/Volumes/CATALOG/finsight/evidence,revision=YOUR_40_CHARACTER_COMMIT'
databricks bundle deploy --var 'input_table=CATALOG.finsight.application_sample,output_schema=CATALOG.finsight,experiment_name=/Workspace/YOUR_EXPERIMENT,evidence_volume=/Volumes/CATALOG/finsight/evidence,revision=YOUR_40_CHARACTER_COMMIT'
```

Because Python source exports do not reliably capture serverless notebook environment metadata, configure and confirm the deployed notebook's Environment dependencies before running the job. For subsequent deployments repeat this check. See [serverless limitations](https://docs.databricks.com/aws/en/compute/serverless/limitations) and [bundle configuration examples](https://docs.databricks.com/aws/en/dev-tools/bundles/examples). This bundle deliberately omits a cluster definition for serverless notebook execution.

```bash
databricks bundle run credit_risk_baseline --var 'input_table=CATALOG.finsight.application_sample,output_schema=CATALOG.finsight,experiment_name=/Workspace/YOUR_EXPERIMENT,evidence_volume=/Volumes/CATALOG/finsight/evidence,revision=YOUR_40_CHARACTER_COMMIT'
```

Run that same command again after the first finishes. All uppercase values above are placeholders to replace. The bundle has no schedule and allows one concurrent run. Source-format environment setup and workspace permissions require cloud verification before claiming the configuration is operational.

## Step 5: Publish Evidence

Download only the two `aggregate_evidence_*.json` files from the volume into ignored local storage such as `data/processed/`. Review them: the notebook exports counts, metrics, hashes, versions, timestamps and opaque run IDs, without applicant rows, workspace hosts or account emails. Record job success from the Databricks UI separately; JSON alone is self-reported evidence and not independent attestation.

Compare code revision, fingerprint, sample size, parameters, split counts, versions and metrics across the two runs. They should agree apart from run IDs, timestamps and runtime. Investigate differences before publication. Publish the reviewed aggregate files under a new `reports/cloud_runs/` directory and update the progress checklist only after successful cloud execution. Never publish predictions, model binaries, IDs, source exports, tokens or notebook cell outputs containing rows.

After verified runs, a defensible project statement is: "Executed a reproducible credit-risk baseline training and scoring job on Databricks using SQL/PySpark, training-only preprocessing and MLflow." Add measured row counts and run evidence. Until then describe it as a prepared workflow. No cloud metric or work-experience score is promised.
