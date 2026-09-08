# Databricks notebook source
"""FinSight cloud baseline: SQL/PySpark preparation, sklearn training, MLflow.

Import as a Databricks source notebook. Configure dependencies and parameters
per README.md before executing the training cell.
"""

import hashlib
import importlib.metadata
import json
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


SOURCE_COLUMNS = [
    "SK_ID_CURR", "TARGET", "AMT_INCOME_TOTAL", "AMT_CREDIT", "AMT_ANNUITY",
    "DAYS_BIRTH", "DAYS_EMPLOYED", "EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3",
]
NUMERIC_SOURCE_COLUMNS = SOURCE_COLUMNS[2:]
FEATURES = [
    "AMT_INCOME_TOTAL", "AMT_CREDIT", "AMT_ANNUITY", "credit_to_income_ratio",
    "annuity_to_income_ratio", "age_years", "employment_years", "external_score_mean",
    "missing_value_count",
]


def validate_frame(frame):
    required = SOURCE_COLUMNS + FEATURES
    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise ValueError(f"Missing required model/source columns: {missing}")
    if frame["SK_ID_CURR"].isna().any() or frame["SK_ID_CURR"].duplicated().any():
        raise ValueError("Applicant IDs must be non-null and unique.")
    observed_targets = set(frame["TARGET"].dropna().unique().tolist())
    if frame["TARGET"].isna().any() or observed_targets != {0, 1}:
        raise ValueError("TARGET must contain exactly 0 and 1 with no missing labels.")
    if frame["TARGET"].value_counts().min() < 10:
        raise ValueError("At least 10 applicants per class are required for stratified splits.")
    usable = frame[FEATURES].replace([np.inf, -np.inf], np.nan).notna().sum()
    if usable.eq(0).any():
        raise ValueError(f"Entire model features are missing: {usable[usable.eq(0)].index.tolist()}")


def canonical_sha256(frame, columns):
    canonical = frame.loc[:, columns].sort_values("SK_ID_CURR").reset_index(drop=True)
    payload = canonical.to_csv(
        index=False, na_rep="<NA>", float_format="%.17g", lineterminator="\n"
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def fit_baseline(frame, seed=2026):
    """Training-only median imputation/scaling; validation-selected regularization."""
    validate_frame(frame)
    frame = frame.sort_values("SK_ID_CURR").reset_index(drop=True)

    train, remaining = train_test_split(
        np.arange(len(frame)), test_size=0.4, stratify=frame["TARGET"], random_state=seed
    )
    valid, test = train_test_split(
        remaining, test_size=0.5,
        stratify=frame["TARGET"].iloc[remaining], random_state=seed
    )

    X = frame[FEATURES].replace([np.inf, -np.inf], np.nan)
    usable = X.iloc[train].notna().sum()
    if usable.eq(0).any():
        raise ValueError(f"Entire training features are missing: {usable[usable.eq(0)].index.tolist()}")

    candidate_models = {}
    tuning_results = []
    for c in (0.1, 1.0, 10.0):
        model = make_pipeline(
            SimpleImputer(strategy="median"), StandardScaler(),
            LogisticRegression(C=c, class_weight="balanced", max_iter=2000, random_state=seed),
        )
        model.fit(X.iloc[train], frame["TARGET"].iloc[train])
        p = model.predict_proba(X.iloc[valid])[:, 1]
        ap = float(average_precision_score(frame["TARGET"].iloc[valid], p))
        candidate_models[c] = model
        tuning_results.append({"C": float(c), "validation_average_precision": ap})

    selected = max(tuning_results, key=lambda item: (item["validation_average_precision"], -item["C"]))
    selected_c = selected["C"]
    model = candidate_models[selected_c]

    metrics = {}
    for name, idx in (("validation", valid), ("test", test)):
        p = model.predict_proba(X.iloc[idx])[:, 1]
        y = frame["TARGET"].iloc[idx]
        metrics.update({
            f"{name}_roc_auc": float(roc_auc_score(y, p)),
            f"{name}_average_precision": float(average_precision_score(y, p)),
            f"{name}_brier": float(brier_score_loss(y, p)),
            f"{name}_positive_rate": float(y.mean()),
        })

    predictions = pd.DataFrame({
        "SK_ID_CURR": frame["SK_ID_CURR"].iloc[test].to_numpy(),
        "TARGET": frame["TARGET"].iloc[test].to_numpy(),
        "default_probability": model.predict_proba(X.iloc[test])[:, 1],
    })

    manifest = frame[["SK_ID_CURR"]].copy()
    manifest["split"] = ""
    for name, idx in (("train", train), ("validation", valid), ("test", test)):
        manifest.loc[idx, "split"] = name

    params = {
        "C": float(selected_c), "seed": int(seed), "class_weight": "balanced",
        "candidate_C_values": "0.1,1.0,10.0",
    }
    return model, metrics, predictions, manifest, params, tuning_results


def run_cloud(spark, input_table, output_schema, experiment_name, evidence_volume,
              max_rows=20000, revision=""):
    """Write each run to new cloud outputs; export only aggregate evidence."""
    import mlflow
    import mlflow.sklearn
    from mlflow.models import infer_signature
    from mlflow.tracking import MlflowClient
    from pyspark.sql import functions as F

    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*", input_table):
        raise ValueError("input_table must be catalog.schema.table using simple identifiers.")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*", output_schema):
        raise ValueError("output_schema must be catalog.schema using simple identifiers.")

    try:
        max_rows = int(max_rows)
    except (TypeError, ValueError) as exc:
        raise ValueError("max_rows must be an integer.") from exc
    if not 100 <= max_rows <= 50000:
        raise ValueError("max_rows must be between 100 and 50,000 to bound driver memory.")
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Provide the exact lowercase 40-character Git commit as revision.")

    volume_parts = evidence_volume.strip("/").split("/")
    if len(volume_parts) < 4 or volume_parts[0] != "Volumes" or any(p in {"", ".", ".."} for p in volume_parts):
        raise ValueError("evidence_volume must be /Volumes/<catalog>/<schema>/<volume> or a safe subdirectory.")
    evidence_dir = Path(evidence_volume)
    if not evidence_dir.exists() or not evidence_dir.is_dir():
        raise ValueError(f"Evidence volume path is not accessible: {evidence_volume}")

    if MlflowClient().get_experiment_by_name(experiment_name) is None:
        raise ValueError("Configured MLflow experiment does not exist. Copy its exact workspace path.")

    started = time.perf_counter()
    raw_source = spark.table(input_table).select(*SOURCE_COLUMNS)

    def cleaned_double(column_name):
        numeric = F.expr(f"try_cast(`{column_name}` as double)")
        return F.when(
            numeric.isNull() | F.isnan(numeric) | (F.abs(numeric) == float("inf")),
            F.lit(None).cast("double"),
        ).otherwise(numeric)

    typed = raw_source.select(
        F.expr("try_cast(`SK_ID_CURR` as bigint)").alias("SK_ID_CURR"),
        F.expr("try_cast(`TARGET` as double)").alias("_TARGET_NUM"),
        *[cleaned_double(c).alias(c) for c in NUMERIC_SOURCE_COLUMNS],
    )
    source_rows = typed.count()

    if typed.filter(F.col("SK_ID_CURR").isNull()).limit(1).count():
        raise ValueError("SK_ID_CURR contains null or unparseable IDs.")
    invalid_target = (
        F.col("_TARGET_NUM").isNull() | F.isnan("_TARGET_NUM") |
        (F.abs(F.col("_TARGET_NUM")) == float("inf")) |
        (~F.col("_TARGET_NUM").isin(0.0, 1.0))
    )
    if typed.filter(invalid_target).limit(1).count():
        raise ValueError("TARGET contains missing, malformed, or non-binary values.")

    typed = typed.select(
        "SK_ID_CURR", F.col("_TARGET_NUM").cast("int").alias("TARGET"), *NUMERIC_SOURCE_COLUMNS
    )
    if typed.groupBy("SK_ID_CURR").count().filter(F.col("count") > 1).limit(1).count():
        raise ValueError("Applicant IDs must be unique in the source table.")

    sample = typed.orderBy(F.xxhash64("SK_ID_CURR"), "SK_ID_CURR").limit(max_rows).cache()
    sample_rows = sample.count()
    if sample_rows < 100:
        raise ValueError(f"Only {sample_rows} rows are available; at least 100 are required.")
    sample.createOrReplaceTempView("finsight_cloud_sample")

    features = spark.sql("""
        WITH engineered AS (
          SELECT *,
            CASE WHEN AMT_INCOME_TOTAL > 0 THEN AMT_CREDIT / AMT_INCOME_TOTAL END AS credit_to_income_ratio,
            CASE WHEN AMT_INCOME_TOTAL > 0 THEN AMT_ANNUITY / AMT_INCOME_TOTAL END AS annuity_to_income_ratio,
            CASE WHEN DAYS_BIRTH < 0 THEN -DAYS_BIRTH / 365.25 END AS age_years,
            CASE WHEN DAYS_EMPLOYED <= 0 THEN -DAYS_EMPLOYED / 365.25 END AS employment_years,
            CASE WHEN (
                CASE WHEN EXT_SOURCE_1 IS NOT NULL THEN 1 ELSE 0 END +
                CASE WHEN EXT_SOURCE_2 IS NOT NULL THEN 1 ELSE 0 END +
                CASE WHEN EXT_SOURCE_3 IS NOT NULL THEN 1 ELSE 0 END
              ) > 0
              THEN (COALESCE(EXT_SOURCE_1, 0.0) + COALESCE(EXT_SOURCE_2, 0.0) + COALESCE(EXT_SOURCE_3, 0.0)) /
                   (CASE WHEN EXT_SOURCE_1 IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN EXT_SOURCE_2 IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN EXT_SOURCE_3 IS NOT NULL THEN 1 ELSE 0 END)
            END AS external_score_mean
          FROM finsight_cloud_sample
        )
        SELECT *,
          (CASE WHEN AMT_INCOME_TOTAL IS NULL THEN 1 ELSE 0 END +
           CASE WHEN AMT_CREDIT IS NULL THEN 1 ELSE 0 END +
           CASE WHEN AMT_ANNUITY IS NULL THEN 1 ELSE 0 END +
           CASE WHEN credit_to_income_ratio IS NULL THEN 1 ELSE 0 END +
           CASE WHEN annuity_to_income_ratio IS NULL THEN 1 ELSE 0 END +
           CASE WHEN age_years IS NULL THEN 1 ELSE 0 END +
           CASE WHEN employment_years IS NULL THEN 1 ELSE 0 END +
           CASE WHEN external_score_mean IS NULL THEN 1 ELSE 0 END) AS missing_value_count
        FROM engineered
    """)

    frame = features.toPandas().sort_values("SK_ID_CURR").reset_index(drop=True)
    validate_frame(frame)
    input_fingerprint = canonical_sha256(frame, SOURCE_COLUMNS)
    feature_fingerprint = canonical_sha256(frame, ["SK_ID_CURR", "TARGET", *FEATURES])

    mlflow.set_experiment(experiment_name)
    run_key = uuid.uuid4().hex
    with mlflow.start_run(run_name=f"finsight-cloud-{run_key[:8]}") as run:
        model, metrics, predictions, manifest, params, tuning_results = fit_baseline(frame)
        params.update({"sample_rows": len(frame), "source_rows": source_rows, "feature_count": len(FEATURES)})
        mlflow.log_params(params)

        tuning_metrics = {
            "candidate_validation_ap_C_" + str(item["C"]).replace(".", "p"): item["validation_average_precision"]
            for item in tuning_results
        }
        mlflow.log_metrics({**metrics, **tuning_metrics})
        mlflow.set_tags({
            "source_revision": revision,
            "input_data_fingerprint": input_fingerprint,
            "feature_fingerprint": feature_fingerprint,
            "scope": "public-data sample cloud baseline; not production champion",
        })

        input_example = frame[FEATURES].head(5).copy()
        signature = infer_signature(input_example, model.predict(input_example))
        mlflow.sklearn.log_model(
            model, artifact_path="baseline_model", signature=signature, input_example=input_example
        )

        feature_table = f"{output_schema}.run_{run_key}_features"
        prediction_table = f"{output_schema}.run_{run_key}_predictions"
        split_table = f"{output_schema}.run_{run_key}_splits"

        features.write.format("delta").mode("errorifexists").saveAsTable(feature_table)
        spark.createDataFrame(predictions).write.format("delta").mode("errorifexists").saveAsTable(prediction_table)
        spark.createDataFrame(manifest).write.format("delta").mode("errorifexists").saveAsTable(split_table)

        evidence = {
            "evidence_schema_version": 2,
            "platform": "Databricks",
            "run_id": run.info.run_id,
            "output_run_key": run_key,
            "source_revision": revision,
            "input_data_sha256": input_fingerprint,
            "feature_data_sha256": feature_fingerprint,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": float(time.perf_counter() - started),
            "parameters": params,
            "metrics": metrics,
            "tuning": tuning_results,
            "selection": "validation average precision",
            "features": FEATURES,
            "missing_counts": {c: int(frame[c].isna().sum()) for c in FEATURES},
            "split_counts": {str(k): int(v) for k, v in manifest["split"].value_counts().to_dict().items()},
            "class_counts": {str(int(k)): int(v) for k, v in frame["TARGET"].value_counts().sort_index().to_dict().items()},
            "versions": {p: importlib.metadata.version(p) for p in ("numpy", "pandas", "scikit-learn", "mlflow")},
            "probability_note": "Class-weighted logistic-regression scores are uncalibrated baseline probabilities.",
        }

        destination = evidence_dir / f"aggregate_evidence_{run_key}.json"
        destination.write_text(json.dumps(evidence, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        mlflow.log_dict(evidence, "aggregate_evidence.json")
        mlflow.set_tag("evidence_volume_written", "true")

    sample.unpersist()
    print(json.dumps(evidence, indent=2))
    return evidence


# COMMAND ----------
# Create widgets without overwriting values already set in the notebook or Job.
def _ensure_widget(name, default_value):
    try:
        dbutils.widgets.get(name)
    except Exception:
        dbutils.widgets.text(name, default_value)


if "dbutils" in globals():
    for _name, _default in (
        ("input_table", ""), ("output_schema", ""), ("experiment_name", ""),
        ("evidence_volume", ""), ("max_rows", "20000"), ("revision", ""),
    ):
        _ensure_widget(_name, _default)


# COMMAND ----------
# This cell executes in Databricks, but is skipped when local tests import the file.
if "spark" in globals() and "dbutils" in globals():
    _params = dbutils.widgets.getAll()
    _required = ("input_table", "output_schema", "experiment_name", "evidence_volume", "revision")
    _empty = [name for name in _required if not _params.get(name, "").strip()]
    if _empty:
        raise ValueError("Set these Databricks widget values before running: " + ", ".join(_empty))

    EVIDENCE = run_cloud(
        spark=spark,
        input_table=_params["input_table"].strip(),
        output_schema=_params["output_schema"].strip(),
        experiment_name=_params["experiment_name"].strip(),
        evidence_volume=_params["evidence_volume"].strip(),
        max_rows=int(_params.get("max_rows", "20000")),
        revision=_params["revision"].strip().lower(),
    )
