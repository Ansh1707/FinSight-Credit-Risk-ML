"""Create feature registry and timestamp-lineage documentation.

Run from the project root:
    python src/features/feature_registry.py

The registry documents model feature groups, source tables, transformation
logic, availability time, leakage risk, and production controls. It reads the
saved final model feature list when available and falls back to feature
engineering constants for CI and reviewer environments.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

try:
    from src.features.pyspark_feature_engineering import (
        AGGREGATED_FEATURES,
        BASE_CATEGORICAL_COLUMNS,
        BASE_NUMERIC_COLUMNS,
        DERIVED_FEATURES,
    )
except ModuleNotFoundError:  # Allows direct script execution from project root.
    from pyspark_feature_engineering import (  # type: ignore
        AGGREGATED_FEATURES,
        BASE_CATEGORICAL_COLUMNS,
        BASE_NUMERIC_COLUMNS,
        DERIVED_FEATURES,
    )


REPORTS_DIR = Path("reports")
MPL_CACHE_DIR = REPORTS_DIR / ".matplotlib-cache"
MPL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE_DIR))

MODEL_PATH = Path("models/credit_risk_model.pkl")
CSV_PATH = REPORTS_DIR / "feature_registry.csv"
MD_PATH = REPORTS_DIR / "feature_registry.md"


@dataclass(frozen=True)
class FeatureLineage:
    """Feature group lineage and governance metadata."""

    feature_group: str
    source_tables: str
    source_columns: str
    transformation_logic: str
    join_key: str
    aggregation_level: str
    availability_time: str
    leakage_risk: str
    production_controls: str
    owner: str = "Data Science / Credit Risk"


BASE_APPLICATION_LINEAGE = FeatureLineage(
    feature_group="base_application_numeric",
    source_tables="application_train.csv",
    source_columns="Application-time numeric applicant and loan fields",
    transformation_logic="Direct selected numeric fields from the base application table.",
    join_key="SK_ID_CURR",
    aggregation_level="Applicant level",
    availability_time="Known at loan application submission time.",
    leakage_risk="low",
    production_controls=(
        "Validate schema, numeric ranges, missingness, and application timestamp; "
        "exclude identifiers and target from model inputs."
    ),
)

DERIVED_APPLICATION_LINEAGE = FeatureLineage(
    feature_group="derived_application_features",
    source_tables="application_train.csv",
    source_columns=(
        "AMT_CREDIT, AMT_INCOME_TOTAL, AMT_ANNUITY, AMT_GOODS_PRICE, "
        "DAYS_BIRTH, DAYS_EMPLOYED, EXT_SOURCE_1/2/3, and source-column null flags"
    ),
    transformation_logic=(
        "Creates affordability ratios, age/employment transformations, external "
        "score aggregate statistics, and application-row missingness count."
    ),
    join_key="SK_ID_CURR",
    aggregation_level="Applicant level",
    availability_time="Known or derivable at loan application submission time.",
    leakage_risk="low",
    production_controls=(
        "Freeze ratio definitions, handle zero denominators consistently, validate "
        "external-score source timing, and monitor null-rate drift."
    ),
)

CATEGORICAL_LINEAGE = FeatureLineage(
    feature_group="encoded_application_categorical",
    source_tables="application_train.csv",
    source_columns=", ".join(BASE_CATEGORICAL_COLUMNS),
    transformation_logic=(
        "Fill missing categorical values with 'Missing' and encode with Spark "
        "StringIndexer using handleInvalid='keep'."
    ),
    join_key="SK_ID_CURR",
    aggregation_level="Applicant level",
    availability_time="Known at loan application submission time.",
    leakage_risk="low_to_medium_proxy_risk",
    production_controls=(
        "Persist category mapping, handle unseen categories, monitor category drift, "
        "and review protected/proxy-sensitive fields with policy and compliance."
    ),
)

GROUP_LINEAGE: dict[str, FeatureLineage] = {
    "bureau_balance_": FeatureLineage(
        feature_group="bureau_balance_history",
        source_tables="bureau.csv, bureau_balance.csv",
        source_columns="SK_ID_BUREAU, MONTHS_BALANCE, STATUS",
        transformation_logic=(
            "Join bureau_balance to bureau through SK_ID_BUREAU and aggregate monthly "
            "status counts and late-status counts to SK_ID_CURR."
        ),
        join_key="SK_ID_BUREAU -> SK_ID_CURR",
        aggregation_level="Applicant level from historical bureau monthly status",
        availability_time=(
            "Must include only monthly statuses visible before the current decision or "
            "collections scoring timestamp."
        ),
        leakage_risk="medium",
        production_controls=(
            "Filter MONTHS_BALANCE/status snapshots by observation cutoff, validate "
            "bureau linkage integrity, and monitor late-status distribution drift."
        ),
    ),
    "bureau_": FeatureLineage(
        feature_group="bureau_credit_history",
        source_tables="bureau.csv",
        source_columns=(
            "CREDIT_ACTIVE, CREDIT_DAY_OVERDUE, DAYS_CREDIT, AMT_CREDIT_SUM, "
            "AMT_CREDIT_SUM_DEBT"
        ),
        transformation_logic=(
            "Aggregate external bureau tradeline counts, active/closed status, "
            "overdue counts, credit recency, credit amount, and debt burden to SK_ID_CURR."
        ),
        join_key="SK_ID_CURR",
        aggregation_level="Applicant level from historical bureau records",
        availability_time=(
            "Must be restricted to bureau records available before the current loan "
            "decision or collections scoring timestamp."
        ),
        leakage_risk="medium",
        production_controls=(
            "Apply source-record timestamp filters, validate bureau pull date, exclude "
            "post-application bureau updates, and monitor bureau-source refresh changes."
        ),
    ),
    "previous_": FeatureLineage(
        feature_group="previous_application_history",
        source_tables="previous_application.csv",
        source_columns=(
            "NAME_CONTRACT_STATUS, AMT_CREDIT, AMT_APPLICATION, AMT_DOWN_PAYMENT, "
            "DAYS_DECISION"
        ),
        transformation_logic=(
            "Aggregate prior application counts, approved/refused counts, mean credit, "
            "mean application amount, mean down payment, and mean decision recency."
        ),
        join_key="SK_ID_CURR",
        aggregation_level="Applicant level from previous applications",
        availability_time=(
            "Must include only applications decided before the current application or "
            "collections scoring timestamp."
        ),
        leakage_risk="medium",
        production_controls=(
            "Filter by prior decision timestamp, exclude current-loan outcome, validate "
            "application identity links, and monitor refused/approved mix drift."
        ),
    ),
    "installment_": FeatureLineage(
        feature_group="installment_repayment_history",
        source_tables="installments_payments.csv",
        source_columns="DAYS_ENTRY_PAYMENT, DAYS_INSTALMENT, AMT_PAYMENT, AMT_INSTALMENT",
        transformation_logic=(
            "Create payment delay and payment ratio, then aggregate count, late count, "
            "average/max delay, and average payment ratio to SK_ID_CURR."
        ),
        join_key="SK_ID_CURR",
        aggregation_level="Applicant level from historical installments",
        availability_time=(
            "Must include only installments from loans observed before the current "
            "decision or collections scoring timestamp."
        ),
        leakage_risk="medium_high_timing_sensitive",
        production_controls=(
            "Enforce observation cutoff by installment/payment date, exclude future "
            "repayment behavior, and separately test leakage around target-loan payments."
        ),
    ),
    "pos_cash_": FeatureLineage(
        feature_group="pos_cash_balance_history",
        source_tables="POS_CASH_balance.csv",
        source_columns="SK_DPD_DEF, CNT_INSTALMENT_FUTURE",
        transformation_logic=(
            "Aggregate POS cash monthly observation count, delinquency count, max DPD, "
            "and average remaining installments to SK_ID_CURR."
        ),
        join_key="SK_ID_CURR",
        aggregation_level="Applicant level from historical POS cash records",
        availability_time=(
            "Must include only POS balance snapshots before the current decision or "
            "collections scoring timestamp."
        ),
        leakage_risk="medium_high_timing_sensitive",
        production_controls=(
            "Filter monthly snapshots by observation date, exclude target-loan future "
            "performance, and monitor delinquency and remaining-installment drift."
        ),
    ),
    "credit_card_": FeatureLineage(
        feature_group="credit_card_balance_history",
        source_tables="credit_card_balance.csv",
        source_columns="AMT_BALANCE, AMT_DRAWINGS_CURRENT, SK_DPD_DEF",
        transformation_logic=(
            "Aggregate credit-card monthly observation count, average/max balance, "
            "average drawings, and max DPD to SK_ID_CURR."
        ),
        join_key="SK_ID_CURR",
        aggregation_level="Applicant level from historical credit card records",
        availability_time=(
            "Must include only credit-card snapshots known before the current decision "
            "or collections scoring timestamp."
        ),
        leakage_risk="medium_high_timing_sensitive",
        production_controls=(
            "Filter balance snapshots by observation cutoff, exclude post-decision "
            "behavior, and monitor balance/drawing/DPD distribution drift."
        ),
    ),
}


def load_model_feature_columns() -> list[str]:
    """Load final model features when available; otherwise use pipeline constants."""
    if MODEL_PATH.exists():
        try:
            import joblib

            bundle = joblib.load(MODEL_PATH)
            feature_columns = bundle.get("feature_columns")
            if feature_columns:
                return list(feature_columns)
        except Exception:
            pass

    categorical_index_columns = [
        f"{column_name}_idx" for column_name in BASE_CATEGORICAL_COLUMNS
    ]
    return BASE_NUMERIC_COLUMNS + DERIVED_FEATURES + AGGREGATED_FEATURES + categorical_index_columns


def lineage_for_feature(feature_name: str) -> FeatureLineage:
    """Return feature lineage metadata for a model feature."""
    if feature_name in BASE_NUMERIC_COLUMNS:
        return BASE_APPLICATION_LINEAGE
    if feature_name in DERIVED_FEATURES:
        return DERIVED_APPLICATION_LINEAGE
    if feature_name.endswith("_idx"):
        return CATEGORICAL_LINEAGE
    for prefix, lineage in GROUP_LINEAGE.items():
        if feature_name.startswith(prefix):
            return lineage
    return FeatureLineage(
        feature_group="manual_review_required",
        source_tables="Unknown",
        source_columns="Unknown",
        transformation_logic="Feature was not mapped by the registry rules.",
        join_key="Unknown",
        aggregation_level="Unknown",
        availability_time="Unknown; must be reviewed before production use.",
        leakage_risk="review",
        production_controls="Add source table, transformation, owner, and timestamp-lineage controls.",
    )


def build_registry(feature_names: Iterable[str]) -> pd.DataFrame:
    """Build feature-level registry rows."""
    rows = []
    for feature_name in feature_names:
        lineage = lineage_for_feature(feature_name)
        row = asdict(lineage)
        row.update(
            {
                "feature_name": feature_name,
                "used_in_model": True,
            }
        )
        rows.append(row)
    columns = [
        "feature_name",
        "feature_group",
        "source_tables",
        "source_columns",
        "transformation_logic",
        "join_key",
        "aggregation_level",
        "availability_time",
        "leakage_risk",
        "production_controls",
        "owner",
        "used_in_model",
    ]
    return pd.DataFrame(rows)[columns].sort_values(["feature_group", "feature_name"])


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


def build_markdown_report(registry: pd.DataFrame) -> str:
    """Build business-readable feature registry documentation."""
    group_summary = (
        registry.groupby(["feature_group", "leakage_risk", "source_tables"], dropna=False)
        .size()
        .reset_index(name="feature_count")
        .sort_values(["leakage_risk", "feature_group"])
    )
    lineage_summary = registry[
        [
            "feature_group",
            "source_tables",
            "transformation_logic",
            "availability_time",
            "leakage_risk",
            "production_controls",
        ]
    ].drop_duplicates()
    high_timing = registry[
        registry["leakage_risk"].isin(["medium", "medium_high_timing_sensitive"])
    ][
        [
            "feature_name",
            "feature_group",
            "availability_time",
            "leakage_risk",
            "production_controls",
        ]
    ]

    return "\n".join(
        [
            "# Feature Registry And Timestamp Lineage",
            "",
            "This registry documents the final model feature groups, source tables, "
            "transformation logic, availability-time assumptions, leakage risk, and "
            "production controls. It is generated from the saved final model feature "
            "list when available and does not modify raw data or retrain models.",
            "",
            "## Scope",
            "",
            f"- Registered model features: `{len(registry):,}`",
            f"- Output CSV: `{CSV_PATH.as_posix()}`",
            f"- Output report: `{MD_PATH.as_posix()}`",
            "- Model training: not performed.",
            "",
            "## Feature Group Summary",
            "",
            markdown_table(group_summary),
            "",
            "## Timestamp-Lineage Summary",
            "",
            markdown_table(lineage_summary),
            "",
            "## Timing-Sensitive Features",
            "",
            "The features below are useful credit-risk signals, but production use "
            "requires timestamp controls to prove the source records existed before "
            "the decision or scoring timestamp.",
            "",
            markdown_table(high_timing),
            "",
            "## Production Feature Governance Requirements",
            "",
            "- Maintain a feature registry with owner, source table, source columns, "
            "transformation, availability time, and leakage-risk rating.",
            "- Enforce observation cutoffs for bureau, previous application, installment, "
            "POS cash, and credit-card records.",
            "- Exclude identifiers and target fields from model inputs while preserving "
            "identifiers for joins and auditability.",
            "- Version feature definitions and category encodings before deployment.",
            "- Re-run `python src/features/feature_registry.py` and "
            "`python src/features/leakage_checks.py` after every feature change.",
            "",
            "## Portfolio Interpretation",
            "",
            "For this portfolio build, the registry closes the lineage documentation "
            "gap by making timing assumptions explicit. For real production lending, "
            "these assumptions would need source-system timestamps, policy sign-off, "
            "data contracts, feature-store ownership, and monitoring alerts.",
            "",
        ]
    )


def run() -> pd.DataFrame:
    """Create feature registry outputs."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    registry = build_registry(load_model_feature_columns())
    registry.to_csv(CSV_PATH, index=False)
    MD_PATH.write_text(build_markdown_report(registry), encoding="utf-8")
    return registry


def main() -> None:
    """CLI entry point."""
    registry = run()
    print("Feature registry complete.")
    print(f"Registered features: {len(registry):,}")
    print(f"CSV saved to: {CSV_PATH}")
    print(f"Report saved to: {MD_PATH}")


if __name__ == "__main__":
    main()
