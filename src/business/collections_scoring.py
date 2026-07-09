"""Convert model scores into collections priority scores and risk bands.

Run from the project root:
    python src/business/collections_scoring.py
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
import numpy as np
import pandas as pd


MODEL_PATH = Path("models/credit_risk_model.pkl")
FEATURE_PATH = Path("data/processed/model_features.parquet")
REASON_CODES_PATH = REPORTS_DIR / "sample_reason_codes.csv"
OUTPUT_PATH = REPORTS_DIR / "collections_priority_sample.csv"
SUMMARY_PATH = REPORTS_DIR / "collections_summary.md"

RISK_BAND_WEIGHTS = {
    "Low Risk": 0.75,
    "Medium Risk": 1.00,
    "High Risk": 1.30,
    "Critical Risk": 1.60,
}


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Create collections priority scores.")
    parser.add_argument(
        "--output-size",
        type=int,
        default=1000,
        help="Number of highest-priority applicants to save in the sample output.",
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


def load_features(feature_columns: list[str]) -> pd.DataFrame:
    """Load processed model features."""
    if not FEATURE_PATH.exists():
        raise FileNotFoundError(
            "Missing data/processed/model_features.parquet. "
            "Run python src/features/pyspark_feature_engineering.py first."
        )

    data = pd.read_parquet(FEATURE_PATH).replace([np.inf, -np.inf], np.nan).fillna(0)
    missing_columns = [column for column in feature_columns if column not in data.columns]
    if missing_columns:
        raise ValueError(
            "Processed feature data is missing required model columns: "
            + ", ".join(missing_columns[:20])
        )
    return data


def assign_risk_band(default_probability: float) -> str:
    """Assign business risk band from predicted default probability."""
    if default_probability >= 0.70:
        return "Critical Risk"
    if default_probability >= 0.50:
        return "High Risk"
    if default_probability >= 0.25:
        return "Medium Risk"
    return "Low Risk"


def min_max_normalize(series: pd.Series) -> pd.Series:
    """Normalize a numeric series to [0, 1]."""
    min_value = series.min()
    max_value = series.max()
    if max_value == min_value:
        return pd.Series(0.0, index=series.index)
    return (series - min_value) / (max_value - min_value)


def build_top_reason_codes(reason_df: pd.DataFrame) -> pd.DataFrame:
    """Combine available applicant-level reason codes into one readable column."""
    if reason_df.empty:
        return pd.DataFrame(columns=["SK_ID_CURR", "top_reason_codes"])

    reason_columns = ["reason_code_1", "reason_code_2", "reason_code_3"]
    available_reason_columns = [
        column for column in reason_columns if column in reason_df.columns
    ]
    reason_df = reason_df.copy()
    reason_df["top_reason_codes"] = reason_df[available_reason_columns].apply(
        lambda row: "; ".join(
            dict.fromkeys(str(value) for value in row if pd.notna(value) and str(value))
        ),
        axis=1,
    )
    return reason_df[["SK_ID_CURR", "top_reason_codes"]]


def load_reason_codes() -> pd.DataFrame:
    """Load sample SHAP reason codes if available."""
    if not REASON_CODES_PATH.exists():
        return pd.DataFrame(columns=["SK_ID_CURR", "top_reason_codes"])
    reason_df = pd.read_csv(REASON_CODES_PATH)
    return build_top_reason_codes(reason_df)


def create_collections_scores(data: pd.DataFrame, model_bundle: dict[str, Any]) -> pd.DataFrame:
    """Create model predictions, risk bands, and collections priority scores."""
    feature_columns = model_bundle["feature_columns"]
    scores = model_bundle["model"].predict_proba(data[feature_columns])[:, 1]

    scored = pd.DataFrame(
        {
            "SK_ID_CURR": data["SK_ID_CURR"].astype(int),
            "default_probability": scores,
            "credit_amount": data["AMT_CREDIT"],
        }
    )
    scored["risk_band"] = scored["default_probability"].map(assign_risk_band)
    scored["risk_band_weight"] = scored["risk_band"].map(RISK_BAND_WEIGHTS)
    scored["normalized_credit_amount"] = min_max_normalize(scored["credit_amount"])
    scored["collections_priority_score"] = (
        100
        * scored["default_probability"]
        * (0.70 + 0.30 * scored["normalized_credit_amount"])
        * scored["risk_band_weight"]
    ).round(2)

    reason_codes = load_reason_codes()
    scored = scored.merge(reason_codes, on="SK_ID_CURR", how="left")
    scored["top_reason_codes"] = scored["top_reason_codes"].fillna(
        "Reason codes not available in SHAP sample"
    )

    return scored.sort_values(
        ["collections_priority_score", "default_probability"], ascending=False
    ).reset_index(drop=True)


def band_summary(scored: pd.DataFrame) -> pd.DataFrame:
    """Summarize portfolio distribution by risk band."""
    summary = (
        scored.groupby("risk_band", dropna=False)
        .agg(
            applicant_count=("SK_ID_CURR", "count"),
            avg_default_probability=("default_probability", "mean"),
            avg_credit_amount=("credit_amount", "mean"),
            avg_priority_score=("collections_priority_score", "mean"),
            max_priority_score=("collections_priority_score", "max"),
        )
        .reset_index()
    )
    summary["band_order"] = summary["risk_band"].map(
        {"Low Risk": 1, "Medium Risk": 2, "High Risk": 3, "Critical Risk": 4}
    )
    summary = summary.sort_values("band_order").drop(columns=["band_order"])
    numeric_columns = [
        "avg_default_probability",
        "avg_credit_amount",
        "avg_priority_score",
        "max_priority_score",
    ]
    summary[numeric_columns] = summary[numeric_columns].round(4)
    return summary


def markdown_table(df: pd.DataFrame) -> str:
    """Render a DataFrame as a markdown table without optional dependencies."""
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


def build_summary_report(scored: pd.DataFrame, sample_output: pd.DataFrame) -> str:
    """Build business-readable collections scoring summary."""
    summary = band_summary(scored)
    top_preview = sample_output[
        [
            "SK_ID_CURR",
            "default_probability",
            "risk_band",
            "credit_amount",
            "collections_priority_score",
            "top_reason_codes",
        ]
    ].head(10).copy()
    top_preview["default_probability"] = top_preview["default_probability"].round(4)
    top_preview["credit_amount"] = top_preview["credit_amount"].round(2)

    return "\n".join(
        [
            "# Collections Scoring Summary",
            "",
            "This report converts final model predictions into business-friendly risk bands "
            "and a collections priority score. Predictions are generated from the saved final "
            "model and processed applicant-level features.",
            "",
            "## Scoring Formula",
            "",
            "For each applicant:",
            "",
            "`collections_priority_score = 100 * default_probability * "
            "(0.70 + 0.30 * normalized_credit_amount) * risk_band_weight`",
            "",
            "Where:",
            "",
            "- `default_probability` is the final model score.",
            "- `normalized_credit_amount` is min-max scaled `AMT_CREDIT` across the scored portfolio.",
            "- `risk_band_weight` is `0.75` for Low Risk, `1.00` for Medium Risk, "
            "`1.30` for High Risk, and `1.60` for Critical Risk.",
            "",
            "This formula prioritizes applicants with high predicted default risk, larger "
            "credit exposure, and more severe risk bands.",
            "",
            "## Risk Band Rules",
            "",
            "- Low Risk: probability < 0.25",
            "- Medium Risk: 0.25 <= probability < 0.50",
            "- High Risk: 0.50 <= probability < 0.70",
            "- Critical Risk: probability >= 0.70",
            "",
            "## Portfolio Risk Band Summary",
            "",
            markdown_table(summary),
            "",
            "## Top Priority Sample",
            "",
            markdown_table(top_preview),
            "",
            "## Business Use",
            "",
            "Collections teams can use the priority score to rank follow-up queues. Risk bands "
            "make the score easier to operationalize, while SHAP reason codes provide context "
            "for why a customer appears risky when that customer was included in the SHAP sample. "
            "The score should support prioritization and review, not automatic adverse action.",
            "",
            "## Saved Output",
            "",
            f"- `{OUTPUT_PATH.as_posix()}`",
            f"- `{SUMMARY_PATH.as_posix()}`",
            "",
        ]
    )


def run_collections_scoring(output_size: int = 1000) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run scoring and save outputs."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    bundle = load_model_bundle()
    data = load_features(bundle["feature_columns"])
    scored = create_collections_scores(data, bundle)
    sample_output = scored.head(output_size)
    output_columns = [
        "SK_ID_CURR",
        "default_probability",
        "risk_band",
        "credit_amount",
        "collections_priority_score",
        "top_reason_codes",
    ]
    sample_output[output_columns].to_csv(OUTPUT_PATH, index=False)
    SUMMARY_PATH.write_text(
        build_summary_report(scored=scored, sample_output=sample_output),
        encoding="utf-8",
    )
    return scored, sample_output[output_columns]


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    scored, sample_output = run_collections_scoring(output_size=args.output_size)
    summary = band_summary(scored)

    print("Collections scoring complete.")
    print(f"Sample priority file saved to: {OUTPUT_PATH}")
    print(f"Summary report saved to: {SUMMARY_PATH}")
    print("\nRisk band summary:")
    print(summary.to_string(index=False))
    print("\nTop 5 priority applicants:")
    print(sample_output.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
