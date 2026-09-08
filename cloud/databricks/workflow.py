# Databricks notebook source
"""FinSight cloud baseline: SQL/PySpark preparation, sklearn training, MLflow.

Import as a notebook. Configure dependencies and parameters per README.md.
"""

import hashlib
import importlib.metadata
import json
import re
import time
import uuid
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


SOURCE_COLUMNS = ["SK_ID_CURR", "TARGET", "AMT_INCOME_TOTAL", "AMT_CREDIT", "AMT_ANNUITY",
                  "DAYS_BIRTH", "DAYS_EMPLOYED", "EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3"]
FEATURES = ["AMT_INCOME_TOTAL", "AMT_CREDIT", "AMT_ANNUITY", "credit_to_income_ratio",
            "annuity_to_income_ratio", "age_years", "employment_years", "external_score_mean",
            "missing_value_count"]


def validate_frame(frame):
    missing = sorted(set(SOURCE_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    if frame.SK_ID_CURR.isna().any() or frame.SK_ID_CURR.duplicated().any():
        raise ValueError("Applicant IDs must be non-null and unique.")
    if set(frame.TARGET.unique()) != {0, 1}:
        raise ValueError("TARGET must have both binary classes without missing labels.")
    if frame.TARGET.value_counts().min() < 10:
        raise ValueError("At least 10 applicants per class required for stratified splits.")


def fit_baseline(frame, seed=2026):
    """Training-only median imputation/scaling; validation-selected regularization."""
    validate_frame(frame)
    frame = frame.sort_values("SK_ID_CURR").reset_index(drop=True)
    train, remaining = train_test_split(np.arange(len(frame)), test_size=.4,
                                        stratify=frame.TARGET, random_state=seed)
    valid, test = train_test_split(remaining, test_size=.5,
        stratify=frame.TARGET.iloc[remaining], random_state=seed)
    X = frame[FEATURES].replace([np.inf, -np.inf], np.nan)
    if X.iloc[train].notna().sum().eq(0).any():
        raise ValueError("An entire training feature is missing; revise the declared feature set.")
    candidates = []
    for c in (.1, 1., 10.):
        model = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
            LogisticRegression(C=c, class_weight="balanced", max_iter=2000, random_state=seed))
        model.fit(X.iloc[train], frame.TARGET.iloc[train])
        p = model.predict_proba(X.iloc[valid])[:, 1]
        candidates.append((average_precision_score(frame.TARGET.iloc[valid], p), c, model))
    _, c, model = max(candidates, key=lambda item: (item[0], -item[1]))
    metrics = {}
    for name, idx in (("validation", valid), ("test", test)):
        p = model.predict_proba(X.iloc[idx])[:, 1]
        y = frame.TARGET.iloc[idx]
        metrics.update({f"{name}_roc_auc": float(roc_auc_score(y, p)),
                        f"{name}_average_precision": float(average_precision_score(y, p)),
                        f"{name}_brier": float(brier_score_loss(y, p))})
    predictions = pd.DataFrame({"SK_ID_CURR": frame.SK_ID_CURR.iloc[test].to_numpy(),
        "TARGET": frame.TARGET.iloc[test].to_numpy(), "default_probability": model.predict_proba(X.iloc[test])[:, 1]})
    manifest = frame[["SK_ID_CURR"]].copy()
    manifest["split"] = ""
    for name, idx in (("train", train), ("validation", valid), ("test", test)):
        manifest.loc[idx, "split"] = name
    return model, metrics, predictions, manifest, {"C": c, "seed": seed, "class_weight": "balanced"}


def run_cloud(spark, input_table, output_schema, experiment_name, evidence_volume,
              max_rows=20000, revision=""):
    """Write each run to new cloud outputs; export only aggregate evidence."""
    import mlflow
    import mlflow.sklearn
    from pathlib import Path
    from pyspark.sql import functions as F

    if not re.fullmatch(r"[A-Za-z_][\w]*\.[A-Za-z_][\w]*\.[A-Za-z_][\w]*", input_table):
        raise ValueError("input_table must be catalog.schema.table using simple identifiers.")
    if not re.fullmatch(r"[A-Za-z_][\w]*\.[A-Za-z_][\w]*", output_schema):
        raise ValueError("output_schema must be catalog.schema using simple identifiers.")
    if not 100 <= max_rows <= 50000:
        raise ValueError("max_rows must be between 100 and 50,000 to bound driver memory.")
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Provide the exact 40-character source Git commit as revision.")
    if not evidence_volume.startswith("/Volumes/"):
        raise ValueError("evidence_volume must be a configured Unity Catalog volume path.")
    started = time.perf_counter()
    source = spark.table(input_table)
    missing = sorted(set(SOURCE_COLUMNS) - set(source.columns))
    if missing:
        raise ValueError(f"Missing required source columns: {missing}")
    source_rows = source.count()
    # Hash ordering provides a deterministic bounded sample independent of file order.
    sample = source.select(*SOURCE_COLUMNS).orderBy(F.xxhash64("SK_ID_CURR"), "SK_ID_CURR").limit(max_rows)
    if sample.select("SK_ID_CURR").distinct().count() != sample.count():
        raise ValueError("Duplicate applicant IDs in sample.")
    for column in SOURCE_COLUMNS:
        sample = sample.withColumn(column, F.expr(f"try_cast(`{column}` as double)"))
    for column in SOURCE_COLUMNS:
        sample = sample.withColumn(column, F.when(F.isnan(column) | (F.abs(F.col(column)) == float("inf")), None).otherwise(F.col(column)))
    sample.createOrReplaceTempView("finsight_cloud_sample")
    features = spark.sql("""
        SELECT *,
          CASE WHEN AMT_INCOME_TOTAL > 0 THEN AMT_CREDIT / AMT_INCOME_TOTAL END AS credit_to_income_ratio,
          CASE WHEN AMT_INCOME_TOTAL > 0 THEN AMT_ANNUITY / AMT_INCOME_TOTAL END AS annuity_to_income_ratio,
          CASE WHEN DAYS_BIRTH < 0 THEN -DAYS_BIRTH / 365.25 END AS age_years,
          CASE WHEN DAYS_EMPLOYED <= 0 THEN -DAYS_EMPLOYED / 365.25 END AS employment_years,
          (coalesce(EXT_SOURCE_1, 0) + coalesce(EXT_SOURCE_2, 0) + coalesce(EXT_SOURCE_3, 0)) /
            nullif(int(EXT_SOURCE_1 IS NOT NULL) + int(EXT_SOURCE_2 IS NOT NULL) + int(EXT_SOURCE_3 IS NOT NULL), 0) AS external_score_mean
        FROM finsight_cloud_sample
    """)
    features = features.withColumn("missing_value_count", sum(F.col(c).isNull().cast("int") for c in SOURCE_COLUMNS[2:]))
    frame = features.toPandas()
    validate_frame(frame)
    frame = frame.sort_values("SK_ID_CURR").reset_index(drop=True)
    fingerprint = hashlib.sha256(frame.to_csv(index=False).encode()).hexdigest()
    mlflow.set_experiment(experiment_name)
    run_key = uuid.uuid4().hex
    with mlflow.start_run(run_name=f"finsight-cloud-{run_key[:8]}") as run:
        model, metrics, predictions, manifest, params = fit_baseline(frame)
        params.update({"sample_rows": len(frame), "source_rows": source_rows, "feature_count": len(FEATURES)})
        mlflow.log_params(params)
        mlflow.log_metrics(metrics)
        mlflow.set_tags({"source_revision": revision, "data_fingerprint": fingerprint,
                         "scope": "public-data sample cloud baseline; not production champion"})
        mlflow.sklearn.log_model(model, artifact_path="baseline_model")
        for suffix, output in (("features", frame), ("predictions", predictions), ("splits", manifest)):
            spark.createDataFrame(output).write.format("delta").mode("errorifexists").saveAsTable(f"{output_schema}.run_{run_key}_{suffix}")
        evidence = {"status": "completed", "platform": "Databricks", "run_id": run.info.run_id,
            "output_run_key": run_key, "source_revision": revision, "data_sha256": fingerprint,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(), "elapsed_seconds": time.perf_counter()-started,
            "parameters": params, "metrics": metrics, "selection": "validation average precision",
            "missing_counts": {c: int(frame[c].isna().sum()) for c in FEATURES},
            "split_counts": manifest.split.value_counts().to_dict(),
            "versions": {p: importlib.metadata.version(p) for p in ("numpy", "pandas", "scikit-learn", "mlflow")}}
        mlflow.log_dict(evidence, "aggregate_evidence.json")
        destination = Path(evidence_volume) / f"aggregate_evidence_{run_key}.json"
        destination.write_text(json.dumps(evidence, indent=2, allow_nan=False) + "\n")
    print(json.dumps(evidence, indent=2))
    return evidence


# COMMAND ----------
if __name__ == "__main__":
    if "dbutils" not in globals():
        raise SystemExit("Import this file into Databricks as a Python notebook; see cloud/databricks/README.md.")
    for key, default in [("input_table", ""), ("output_schema", ""), ("experiment_name", ""),
                         ("evidence_volume", ""), ("max_rows", "20000"), ("revision", "")]:
        dbutils.widgets.text(key, default)
    run_cloud(spark, **{k: dbutils.widgets.get(k) for k in
        ("input_table", "output_schema", "experiment_name", "evidence_volume", "revision")},
        max_rows=int(dbutils.widgets.get("max_rows")))
