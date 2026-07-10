"""Production-style batch scoring and privacy-safe prediction logging.

Run from the project root:
    python src/api/batch_score.py --input data/processed/model_features.parquet --limit 1000

This script scores an input CSV or Parquet file with the saved final model,
validates the serving schema, and writes privacy-safe sample outputs. It does
not retrain models and does not commit raw feature values.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
MPL_CACHE_DIR = REPORTS_DIR / ".matplotlib-cache"
MPL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE_DIR))

import joblib
import numpy as np
import pandas as pd

from src.api.model_loader import assign_risk_band
from src.business.collections_scoring import (
    RISK_BAND_WEIGHTS,
    load_reason_codes,
    min_max_normalize,
)


MODEL_PATH = Path("models/credit_risk_model.pkl")
MODEL_REGISTRY_PATH = REPORTS_DIR / "model_registry.json"
DEFAULT_INPUT_PATH = Path("data/processed/model_features.parquet")
PREDICTION_SAMPLE_PATH = REPORTS_DIR / "batch_scoring_sample.csv"
AUDIT_SAMPLE_PATH = REPORTS_DIR / "prediction_audit_log_sample.csv"
SCHEMA_PATH = REPORTS_DIR / "batch_scoring_schema.json"
SUMMARY_PATH = REPORTS_DIR / "batch_scoring_summary.md"

AUDIT_COLUMNS = [
    "request_id",
    "batch_id",
    "score_timestamp_utc",
    "model_name",
    "model_version",
    "model_stage",
    "feature_count",
    "input_schema_version",
    "applicant_hash",
    "default_probability",
    "risk_band",
    "above_operational_threshold",
    "collections_priority_score",
    "reason_code_1",
    "reason_code_2",
    "reason_code_3",
    "schema_validation_status",
    "missing_feature_count",
    "unknown_feature_count",
]


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Batch score applicants and write privacy-safe audit logs."
    )
    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT_PATH.as_posix(),
        help="CSV or Parquet input file/path to score.",
    )
    parser.add_argument(
        "--prediction-output",
        default=PREDICTION_SAMPLE_PATH.as_posix(),
        help="Privacy-safe prediction sample output path.",
    )
    parser.add_argument(
        "--audit-output",
        default=AUDIT_SAMPLE_PATH.as_posix(),
        help="Privacy-safe audit-log sample output path.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Optional row limit for local portfolio scoring samples.",
    )
    return parser.parse_args()


def utc_now_iso() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def stable_hash(value: Any, salt: str = "finsight_portfolio_audit") -> str:
    """Hash identifiers for privacy-safe audit samples."""
    raw = f"{salt}:{value}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def load_model_bundle(model_path: Path = MODEL_PATH) -> dict[str, Any]:
    """Load the saved model bundle."""
    if not model_path.exists():
        raise FileNotFoundError(
            "Missing models/credit_risk_model.pkl. "
            "Run python src/models/train_final_model.py first."
        )
    return joblib.load(model_path)


def load_model_registry() -> dict[str, Any]:
    """Load model registry metadata when available."""
    if MODEL_REGISTRY_PATH.exists():
        return json.loads(MODEL_REGISTRY_PATH.read_text(encoding="utf-8"))
    return {
        "model_name": "FinSight Credit Risk Model",
        "model_version": "unregistered_local_model",
        "model_stage": "portfolio_ready_not_production_approved",
    }


def load_input(path: Path, limit: int | None = None) -> pd.DataFrame:
    """Load batch input from CSV or Parquet."""
    if not path.exists():
        raise FileNotFoundError(f"Batch scoring input not found: {path}")
    if path.suffix.lower() == ".csv":
        data = pd.read_csv(path)
    elif path.suffix.lower() == ".parquet" or path.is_dir():
        data = pd.read_parquet(path)
    else:
        raise ValueError("Batch scoring input must be CSV or Parquet.")
    if limit:
        data = data.head(limit)
    return data.replace([np.inf, -np.inf], np.nan)


def validate_schema(data: pd.DataFrame, feature_columns: list[str]) -> dict[str, Any]:
    """Validate serving input schema before scoring."""
    missing = [column for column in feature_columns if column not in data.columns]
    unknown = [
        column
        for column in data.columns
        if column not in set(feature_columns + ["SK_ID_CURR", "TARGET"])
    ]
    non_numeric = [
        column
        for column in feature_columns
        if column in data.columns and not pd.api.types.is_numeric_dtype(data[column])
    ]
    duplicate_ids = (
        int(data["SK_ID_CURR"].duplicated().sum()) if "SK_ID_CURR" in data.columns else None
    )
    status = "passed" if not missing and not non_numeric else "failed"
    return {
        "schema_validation_status": status,
        "required_feature_count": len(feature_columns),
        "input_column_count": int(len(data.columns)),
        "row_count": int(len(data)),
        "missing_feature_count": int(len(missing)),
        "missing_features": missing[:50],
        "unknown_feature_count": int(len(unknown)),
        "unknown_features": unknown[:50],
        "non_numeric_feature_count": int(len(non_numeric)),
        "non_numeric_features": non_numeric[:50],
        "duplicate_sk_id_curr_count": duplicate_ids,
    }


def fail_on_invalid_schema(validation: dict[str, Any]) -> None:
    """Raise a helpful error when required serving schema checks fail."""
    if validation["schema_validation_status"] == "passed":
        return
    errors = []
    if validation["missing_feature_count"]:
        errors.append(
            "missing required features: "
            + ", ".join(validation["missing_features"][:20])
        )
    if validation["non_numeric_feature_count"]:
        errors.append(
            "non-numeric model features: "
            + ", ".join(validation["non_numeric_features"][:20])
        )
    raise ValueError("Batch scoring schema validation failed; " + "; ".join(errors))


def top_reason_codes_for_batch(data: pd.DataFrame) -> pd.DataFrame:
    """Attach reason codes from the SHAP sample when available."""
    reason_codes = load_reason_codes()
    if reason_codes.empty:
        return pd.DataFrame(columns=["SK_ID_CURR", "top_reason_codes"])
    return data[["SK_ID_CURR"]].merge(reason_codes, on="SK_ID_CURR", how="left")


def fallback_reason_codes(row: pd.Series) -> list[str]:
    """Create simple non-customer-facing reason-code fallback from feature signals."""
    reasons: list[str] = []
    if row.get("external_score_mean", 1.0) <= 0.40:
        reasons.append("Low external credit score")
    if row.get("credit_to_income_ratio", 0.0) >= 3.0:
        reasons.append("High credit-to-income ratio")
    if row.get("annuity_to_income_ratio", 0.0) >= 0.20:
        reasons.append("High annuity burden")
    if row.get("employment_years", 99.0) <= 2.0:
        reasons.append("Short employment duration")
    if row.get("bureau_credit_count", 1.0) <= 0:
        reasons.append("Missing credit bureau signal")
    if row.get("installment_late_payment_count", 0.0) > 0:
        reasons.append("Prior repayment delay")
    return reasons[:3] or ["No dominant submitted risk driver identified"]


def split_reason_codes(reason_text: str, fallback: list[str]) -> list[str]:
    """Return exactly three reason-code fields."""
    if reason_text and reason_text != "nan":
        reasons = [part.strip() for part in reason_text.split(";") if part.strip()]
    else:
        reasons = fallback
    reasons = list(dict.fromkeys(reasons))[:3]
    return reasons + [""] * (3 - len(reasons))


def collections_priority_score(
    default_probability: pd.Series,
    credit_amount: pd.Series,
    risk_band: pd.Series,
) -> pd.Series:
    """Compute collections priority score using the documented formula."""
    normalized_credit = min_max_normalize(credit_amount.astype(float))
    weights = risk_band.map(RISK_BAND_WEIGHTS).astype(float)
    return (
        100
        * default_probability.astype(float)
        * (0.70 + 0.30 * normalized_credit)
        * weights
    ).round(2)


def score_batch(
    data: pd.DataFrame,
    model_bundle: dict[str, Any],
    registry: dict[str, Any],
    batch_id: str | None = None,
    score_timestamp_utc: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Score a batch and return prediction, audit, and schema metadata."""
    feature_columns = list(model_bundle["feature_columns"])
    validation = validate_schema(data, feature_columns)
    fail_on_invalid_schema(validation)

    batch_id = batch_id or f"batch_{uuid.uuid4().hex[:12]}"
    score_timestamp_utc = score_timestamp_utc or utc_now_iso()
    scoring_frame = data.copy()
    scoring_frame[feature_columns] = scoring_frame[feature_columns].fillna(0)
    probabilities = model_bundle["model"].predict_proba(scoring_frame[feature_columns])[:, 1]
    threshold = float(model_bundle["threshold"])
    applicant_ids = (
        scoring_frame["SK_ID_CURR"].astype(str)
        if "SK_ID_CURR" in scoring_frame.columns
        else pd.Series(range(len(scoring_frame))).astype(str)
    )

    predictions = pd.DataFrame(
        {
            "request_id": [f"req_{uuid.uuid4().hex}" for _ in range(len(scoring_frame))],
            "batch_id": batch_id,
            "score_timestamp_utc": score_timestamp_utc,
            "applicant_hash": [stable_hash(value) for value in applicant_ids],
            "default_probability": probabilities,
            "risk_band": [assign_risk_band(float(prob)) for prob in probabilities],
            "above_operational_threshold": probabilities >= threshold,
            "credit_amount": scoring_frame.get("AMT_CREDIT", pd.Series(0.0, index=scoring_frame.index)).astype(float),
        }
    )
    predictions["collections_priority_score"] = collections_priority_score(
        predictions["default_probability"],
        predictions["credit_amount"],
        predictions["risk_band"],
    )

    reason_frame = top_reason_codes_for_batch(scoring_frame)
    if "top_reason_codes" not in reason_frame.columns:
        reason_frame["top_reason_codes"] = ""
    reason_text = reason_frame["top_reason_codes"].fillna("").astype(str)
    reason_rows = [
        split_reason_codes(text, fallback_reason_codes(scoring_frame.iloc[idx]))
        for idx, text in enumerate(reason_text)
    ]
    reason_columns = pd.DataFrame(
        reason_rows, columns=["reason_code_1", "reason_code_2", "reason_code_3"]
    )
    predictions = pd.concat([predictions.reset_index(drop=True), reason_columns], axis=1)

    metadata = {
        "model_name": registry.get("model_name", "FinSight Credit Risk Model"),
        "model_version": registry.get("model_version", "unregistered_local_model"),
        "model_stage": registry.get("model_stage", "portfolio_ready_not_production_approved"),
        "feature_count": len(feature_columns),
        "input_schema_version": "batch_scoring_schema_v1",
    }
    audit = predictions.copy()
    for key, value in metadata.items():
        audit[key] = value
    audit["schema_validation_status"] = validation["schema_validation_status"]
    audit["missing_feature_count"] = validation["missing_feature_count"]
    audit["unknown_feature_count"] = validation["unknown_feature_count"]
    audit = audit[AUDIT_COLUMNS]
    prediction_output = predictions.drop(columns=["credit_amount"])
    return prediction_output, audit, {**validation, **metadata, "batch_id": batch_id}


def write_schema_file(schema_metadata: dict[str, Any], feature_columns: list[str]) -> None:
    """Write a serving schema and audit-log contract."""
    schema = {
        "schema_name": "FinSight batch scoring schema",
        "input_schema_version": "batch_scoring_schema_v1",
        "required_model_features": feature_columns,
        "optional_identifier_columns": ["SK_ID_CURR"],
        "optional_label_columns_for_backtesting_only": ["TARGET"],
        "prediction_output_columns": [
            "request_id",
            "batch_id",
            "score_timestamp_utc",
            "applicant_hash",
            "default_probability",
            "risk_band",
            "above_operational_threshold",
            "collections_priority_score",
            "reason_code_1",
            "reason_code_2",
            "reason_code_3",
        ],
        "audit_log_columns": AUDIT_COLUMNS,
        "privacy_controls": [
            "Do not log raw feature values in the committed audit sample.",
            "Hash applicant identifiers before writing audit samples.",
            "Do not commit production logs, raw data, processed data, or model binaries.",
        ],
        "latest_validation": schema_metadata,
    }
    SCHEMA_PATH.write_text(json.dumps(schema, indent=2), encoding="utf-8")


def markdown_table(df: pd.DataFrame) -> str:
    """Render a small DataFrame as markdown."""
    if df.empty:
        return "_No rows to display._"
    table = df.copy()
    for column in table.select_dtypes(include=[np.number]).columns:
        table[column] = table[column].round(4)
    table = table.fillna("").astype(str)
    rows = ["| " + " | ".join(table.columns) + " |"]
    rows.append("| " + " | ".join("---" for _ in table.columns) + " |")
    rows.extend("| " + " | ".join(row) + " |" for row in table.itertuples(index=False, name=None))
    return "\n".join(rows)


def build_summary(
    prediction_output: pd.DataFrame,
    audit_output: pd.DataFrame,
    schema_metadata: dict[str, Any],
) -> str:
    """Build production-style batch scoring documentation."""
    band_summary = (
        prediction_output.groupby("risk_band")
        .agg(
            row_count=("request_id", "count"),
            avg_default_probability=("default_probability", "mean"),
            avg_priority_score=("collections_priority_score", "mean"),
        )
        .reset_index()
    )
    audit_preview = audit_output.head(5)[
        [
            "request_id",
            "batch_id",
            "score_timestamp_utc",
            "model_version",
            "applicant_hash",
            "risk_band",
            "reason_code_1",
            "schema_validation_status",
        ]
    ]
    return "\n".join(
        [
            "# Batch Scoring And Prediction Logging Summary",
            "",
            "This document describes a production-style batch scoring pattern for "
            "FinSight. It uses the saved final model, validates the input schema, "
            "scores a batch, and writes privacy-safe sample prediction and audit-log "
            "outputs. It does not retrain the model or write raw feature values to "
            "the committed audit sample.",
            "",
            "## Run Command",
            "",
            "```bash",
            "python src/api/batch_score.py --input data/processed/model_features.parquet --limit 1000",
            "```",
            "",
            "## Schema Validation",
            "",
            f"- Status: `{schema_metadata['schema_validation_status']}`",
            f"- Rows scored: `{schema_metadata['row_count']}`",
            f"- Required feature count: `{schema_metadata['required_feature_count']}`",
            f"- Missing feature count: `{schema_metadata['missing_feature_count']}`",
            f"- Unknown feature count: `{schema_metadata['unknown_feature_count']}`",
            f"- Non-numeric feature count: `{schema_metadata['non_numeric_feature_count']}`",
            "",
            "## Model Metadata Logged",
            "",
            f"- Model name: `{schema_metadata['model_name']}`",
            f"- Model version: `{schema_metadata['model_version']}`",
            f"- Model stage: `{schema_metadata['model_stage']}`",
            f"- Batch ID: `{schema_metadata['batch_id']}`",
            f"- Input schema version: `{schema_metadata['input_schema_version']}`",
            "",
            "## Risk Band Summary",
            "",
            markdown_table(band_summary),
            "",
            "## Privacy-Safe Audit Log Sample",
            "",
            markdown_table(audit_preview),
            "",
            "## Production Logging Controls",
            "",
            "- Generate one `request_id` per scored applicant.",
            "- Generate one `batch_id` per scoring run.",
            "- Store `score_timestamp_utc`, model version, model stage, and schema version with every score.",
            "- Store risk band, operational-threshold flag, priority score, and reason-code fields.",
            "- Hash applicant identifiers before writing review samples.",
            "- Do not commit raw production logs, raw features, raw data, processed data, model binaries, credentials, or customer identifiers.",
            "",
            "## Saved Outputs",
            "",
            f"- `{PREDICTION_SAMPLE_PATH.as_posix()}`",
            f"- `{AUDIT_SAMPLE_PATH.as_posix()}`",
            f"- `{SCHEMA_PATH.as_posix()}`",
            f"- `{SUMMARY_PATH.as_posix()}`",
            "",
        ]
    )


def run(
    input_path: Path = DEFAULT_INPUT_PATH,
    prediction_output_path: Path = PREDICTION_SAMPLE_PATH,
    audit_output_path: Path = AUDIT_SAMPLE_PATH,
    limit: int | None = 1000,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Run batch scoring and write privacy-safe outputs."""
    model_bundle = load_model_bundle()
    registry = load_model_registry()
    data = load_input(input_path, limit=limit)
    prediction_output, audit_output, schema_metadata = score_batch(
        data, model_bundle, registry
    )
    prediction_output_path.parent.mkdir(parents=True, exist_ok=True)
    audit_output_path.parent.mkdir(parents=True, exist_ok=True)
    prediction_output.to_csv(prediction_output_path, index=False)
    audit_output.to_csv(audit_output_path, index=False)
    write_schema_file(schema_metadata, list(model_bundle["feature_columns"]))
    SUMMARY_PATH.write_text(
        build_summary(prediction_output, audit_output, schema_metadata),
        encoding="utf-8",
    )
    return prediction_output, audit_output, schema_metadata


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    predictions, audit, metadata = run(
        input_path=Path(args.input),
        prediction_output_path=Path(args.prediction_output),
        audit_output_path=Path(args.audit_output),
        limit=args.limit,
    )
    print("Batch scoring and prediction logging complete.")
    print(f"Rows scored: {len(predictions):,}")
    print(f"Schema validation: {metadata['schema_validation_status']}")
    print(f"Prediction sample saved to: {args.prediction_output}")
    print(f"Audit sample saved to: {args.audit_output}")
    print(f"Summary saved to: {SUMMARY_PATH}")
    print(f"Audit columns: {', '.join(audit.columns)}")


if __name__ == "__main__":
    main()
