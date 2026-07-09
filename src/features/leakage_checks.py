"""Audit model features for obvious data leakage risks.

Run from the project root:
    python src/features/leakage_checks.py
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

REPORTS_DIR = Path("reports")
MPL_CACHE_DIR = REPORTS_DIR / ".matplotlib-cache"
MPL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE_DIR))

import joblib
import pandas as pd


MODEL_PATH = Path("models/credit_risk_model.pkl")
FEATURE_PATH = Path("data/processed/model_features.parquet")
OUTPUT_PATH = REPORTS_DIR / "leakage_audit.md"

FORBIDDEN_FEATURES = {
    "TARGET",
    "SK_ID_CURR",
    "SK_ID_PREV",
    "SK_ID_BUREAU",
}

HIGH_RISK_KEYWORDS = [
    "TARGET",
    "DEFAULT",
    "STATUS_APPROVED_AFTER",
    "FUTURE_DEFAULT",
    "RECOVERY",
    "COLLECTION",
    "WRITE_OFF",
    "CHARGEOFF",
]

HISTORICAL_PREFIXES = (
    "bureau_",
    "bureau_balance_",
    "previous_",
    "installment_",
    "pos_cash_",
    "credit_card_",
)

BASE_APPLICATION_FEATURES = {
    "CNT_CHILDREN",
    "AMT_INCOME_TOTAL",
    "AMT_CREDIT",
    "AMT_ANNUITY",
    "AMT_GOODS_PRICE",
    "REGION_POPULATION_RELATIVE",
    "DAYS_BIRTH",
    "DAYS_EMPLOYED",
    "DAYS_REGISTRATION",
    "DAYS_ID_PUBLISH",
    "OWN_CAR_AGE",
    "CNT_FAM_MEMBERS",
    "REGION_RATING_CLIENT",
    "REGION_RATING_CLIENT_W_CITY",
    "HOUR_APPR_PROCESS_START",
    "EXT_SOURCE_1",
    "EXT_SOURCE_2",
    "EXT_SOURCE_3",
    "OBS_30_CNT_SOCIAL_CIRCLE",
    "DEF_30_CNT_SOCIAL_CIRCLE",
    "OBS_60_CNT_SOCIAL_CIRCLE",
    "DEF_60_CNT_SOCIAL_CIRCLE",
    "DAYS_LAST_PHONE_CHANGE",
}

DERIVED_APPLICATION_FEATURES = {
    "loan_to_income_ratio",
    "credit_to_income_ratio",
    "annuity_to_income_ratio",
    "annuity_to_credit_ratio",
    "goods_price_to_credit_ratio",
    "employment_years",
    "age_years",
    "external_score_mean",
    "external_score_std",
    "missing_value_count",
}


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run leakage checks for model features.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with an error if medium-risk historical features are present.",
    )
    return parser.parse_args()


def load_model_bundle() -> dict[str, Any]:
    """Load the final model bundle."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Missing models/credit_risk_model.pkl. "
            "Run python src/models/train_final_model.py first."
        )
    return joblib.load(MODEL_PATH)


def load_processed_columns() -> list[str]:
    """Read processed feature table columns."""
    if not FEATURE_PATH.exists():
        raise FileNotFoundError(
            "Missing data/processed/model_features.parquet. "
            "Run python src/features/pyspark_feature_engineering.py first."
        )
    try:
        import pyarrow.parquet as pq

        return list(pq.ParquetDataset(FEATURE_PATH).schema.names)
    except Exception:
        return pd.read_parquet(FEATURE_PATH).columns.tolist()


def classify_feature(feature: str) -> tuple[str, str]:
    """Classify a feature by leakage-risk level and rationale."""
    upper_feature = feature.upper()
    if feature in FORBIDDEN_FEATURES:
        return "fail", "Forbidden target or identifier feature."
    if any(keyword in upper_feature for keyword in HIGH_RISK_KEYWORDS):
        return "high", "Name contains an outcome, default, collection, or recovery keyword."
    if feature.endswith("_idx"):
        return "low", "Encoded application-time categorical feature."
    if feature in BASE_APPLICATION_FEATURES:
        return "low", "Base application feature expected to be known at application time."
    if feature in DERIVED_APPLICATION_FEATURES:
        return "low", "Derived from application-time fields before modeling."
    if feature.startswith(HISTORICAL_PREFIXES):
        return (
            "medium",
            "Historical bureau, previous application, repayment, POS, or credit card aggregate. "
            "Acceptable only if the source records pre-date the current application decision.",
        )
    return "review", "Feature is not in the explicit allowlist; review manually."


def build_feature_audit(feature_columns: list[str]) -> pd.DataFrame:
    """Build feature-level leakage audit table."""
    rows = []
    for feature in feature_columns:
        risk_level, rationale = classify_feature(feature)
        rows.append(
            {
                "feature": feature,
                "risk_level": risk_level,
                "rationale": rationale,
            }
        )
    return pd.DataFrame(rows)


def audit_feature_set(
    model_features: list[str],
    processed_columns: list[str],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Audit model features against processed columns and forbidden names."""
    audit = build_feature_audit(model_features)
    forbidden_present = sorted(set(model_features) & FORBIDDEN_FEATURES)
    missing_from_processed = sorted(set(model_features) - set(processed_columns))
    summary = {
        "feature_count": len(model_features),
        "processed_column_count": len(processed_columns),
        "forbidden_feature_count": len(forbidden_present),
        "forbidden_features": forbidden_present,
        "missing_from_processed_count": len(missing_from_processed),
        "missing_from_processed": missing_from_processed,
        "high_risk_count": int((audit["risk_level"] == "high").sum()),
        "medium_risk_count": int((audit["risk_level"] == "medium").sum()),
        "manual_review_count": int((audit["risk_level"] == "review").sum()),
        "pass": not forbidden_present
        and not missing_from_processed
        and not (audit["risk_level"] == "high").any(),
    }
    return audit, summary


def markdown_table(df: pd.DataFrame) -> str:
    """Render a DataFrame as markdown without optional dependencies."""
    if df.empty:
        return "_No rows to display._"
    safe_df = df.fillna("").astype(str)
    rows = ["| " + " | ".join(safe_df.columns) + " |"]
    rows.append("| " + " | ".join("---" for _ in safe_df.columns) + " |")
    rows.extend(
        "| " + " | ".join(row) + " |"
        for row in safe_df.itertuples(index=False, name=None)
    )
    return "\n".join(rows)


def build_report(audit: pd.DataFrame, summary: dict[str, Any]) -> str:
    """Build leakage audit report."""
    risk_counts = (
        audit["risk_level"]
        .value_counts()
        .rename_axis("risk_level")
        .reset_index(name="feature_count")
        .sort_values("risk_level")
    )
    review_features = audit[audit["risk_level"].isin(["high", "medium", "review"])]

    return "\n".join(
        [
            "# Leakage Audit",
            "",
            "This report checks the saved final model's feature list for obvious data "
            "leakage risks. It is a project governance check, not a replacement for a "
            "full production feature-lineage review.",
            "",
            "## Automated Check Summary",
            "",
            f"- Model feature count: `{summary['feature_count']}`",
            f"- Processed table column count: `{summary['processed_column_count']}`",
            f"- Forbidden target/identifier features found: `{summary['forbidden_feature_count']}`",
            f"- Missing model features in processed table: `{summary['missing_from_processed_count']}`",
            f"- High-risk keyword features found: `{summary['high_risk_count']}`",
            f"- Medium-risk historical aggregate features: `{summary['medium_risk_count']}`",
            f"- Manual-review features: `{summary['manual_review_count']}`",
            f"- Automated leakage check passed: `{summary['pass']}`",
            "",
            "## Risk Level Counts",
            "",
            markdown_table(risk_counts),
            "",
            "## Features Requiring Human Review",
            "",
            markdown_table(review_features),
            "",
            "## Explicitly Forbidden Features",
            "",
            "These features must not be used as model inputs:",
            "",
            "- `TARGET`",
            "- `SK_ID_CURR`",
            "- `SK_ID_PREV`",
            "- `SK_ID_BUREAU`",
            "",
            "The saved model feature list does not include these forbidden fields.",
            "",
            "## Timing Assumptions",
            "",
            "- Base application features are treated as available at application time.",
            "- Derived affordability, age, employment, external-score, and missingness features are derived from application-time fields.",
            "- Bureau, previous application, installment, POS cash, and credit-card aggregates are treated as historical inputs. They are acceptable only if all source records are known before the current loan decision or before the collections scoring timestamp.",
            "- Repayment-delay features are especially important to validate in production because they can become leakage if they include performance after the target loan begins.",
            "",
            "## Production Recommendations",
            "",
            "- Add source-record timestamp filters for every historical table before production use.",
            "- Maintain a feature registry with availability time, source table, owner, and leakage-risk rating.",
            "- Keep identifiers for joins and auditability, but exclude them from model training.",
            "- Re-run this leakage audit after every feature engineering change.",
            "",
            "## Saved Output",
            "",
            f"- `{OUTPUT_PATH.as_posix()}`",
            "",
        ]
    )


def run(strict: bool = False) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Run leakage audit and save report."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    bundle = load_model_bundle()
    model_features = list(bundle["feature_columns"])
    processed_columns = load_processed_columns()
    audit, summary = audit_feature_set(model_features, processed_columns)
    OUTPUT_PATH.write_text(build_report(audit, summary), encoding="utf-8")
    if strict and (summary["medium_risk_count"] or not summary["pass"]):
        raise RuntimeError("Strict leakage audit failed. Review generated report.")
    if not summary["pass"]:
        raise RuntimeError("Automated leakage audit failed. Review generated report.")
    return audit, summary


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    audit, summary = run(strict=args.strict)
    print("Leakage audit complete.")
    print(f"Report saved to: {OUTPUT_PATH}")
    print(f"Automated leakage check passed: {summary['pass']}")
    print("\nRisk level counts:")
    print(audit["risk_level"].value_counts().to_string())


if __name__ == "__main__":
    main()
