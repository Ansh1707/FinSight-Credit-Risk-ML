"""Estimate business impact from model-based collections prioritization.

Run from the project root:
    python src/business/business_impact.py
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
OUTPUT_PATH = REPORTS_DIR / "business_impact_by_threshold.csv"
SUMMARY_PATH = REPORTS_DIR / "business_impact_summary.md"
DEFAULT_REVIEW_RATES = [0.05, 0.10, 0.15, 0.20]


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Quantify business impact of model-ranked review queues."
    )
    parser.add_argument(
        "--review-rates",
        nargs="+",
        type=float,
        default=DEFAULT_REVIEW_RATES,
        help="Portfolio fractions to review, such as 0.05 0.10 0.15 0.20.",
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


def load_scoring_data(feature_columns: list[str]) -> pd.DataFrame:
    """Load processed features with labels and credit amount."""
    if not FEATURE_PATH.exists():
        raise FileNotFoundError(
            "Missing data/processed/model_features.parquet. "
            "Run python src/features/pyspark_feature_engineering.py first."
        )

    data = pd.read_parquet(FEATURE_PATH).replace([np.inf, -np.inf], np.nan).fillna(0)
    required_columns = ["SK_ID_CURR", "TARGET", "AMT_CREDIT", *feature_columns]
    missing_columns = [column for column in required_columns if column not in data.columns]
    if missing_columns:
        raise ValueError(
            "Processed feature data is missing required columns: "
            + ", ".join(missing_columns[:20])
        )
    return data


def score_portfolio(data: pd.DataFrame, model_bundle: dict[str, Any]) -> pd.DataFrame:
    """Score the portfolio and compute exposure proxies."""
    feature_columns = model_bundle["feature_columns"]
    probabilities = model_bundle["model"].predict_proba(data[feature_columns])[:, 1]
    scored = pd.DataFrame(
        {
            "SK_ID_CURR": data["SK_ID_CURR"].astype(int),
            "TARGET": data["TARGET"].astype(int),
            "default_probability": probabilities,
            "credit_amount": data["AMT_CREDIT"].astype(float),
        }
    )
    scored["expected_risk_exposure"] = (
        scored["default_probability"] * scored["credit_amount"]
    )
    return scored.sort_values("default_probability", ascending=False).reset_index(
        drop=True
    )


def evaluate_review_capacity(
    scored: pd.DataFrame, review_rates: list[float]
) -> pd.DataFrame:
    """Evaluate model-ranked queues at multiple review capacity levels."""
    if any(rate <= 0 or rate > 1 for rate in review_rates):
        raise ValueError("review rates must be in the interval (0, 1].")

    total_applicants = len(scored)
    total_defaults = int(scored["TARGET"].sum())
    total_credit_exposure = float(scored["credit_amount"].sum())
    total_default_credit_exposure = float(
        scored.loc[scored["TARGET"] == 1, "credit_amount"].sum()
    )
    total_expected_risk_exposure = float(scored["expected_risk_exposure"].sum())

    rows = []
    for rate in review_rates:
        review_count = max(1, int(np.ceil(total_applicants * rate)))
        reviewed = scored.head(review_count)
        defaults_captured = int(reviewed["TARGET"].sum())
        reviewed_credit_exposure = float(reviewed["credit_amount"].sum())
        reviewed_default_credit_exposure = float(
            reviewed.loc[reviewed["TARGET"] == 1, "credit_amount"].sum()
        )
        reviewed_expected_risk_exposure = float(
            reviewed["expected_risk_exposure"].sum()
        )
        random_expected_defaults = total_defaults * rate
        lift_vs_random = (
            defaults_captured / random_expected_defaults
            if random_expected_defaults
            else 0.0
        )

        rows.append(
            {
                "review_rate": rate,
                "review_rate_percent": rate * 100,
                "applicants_reviewed": review_count,
                "defaults_captured": defaults_captured,
                "default_capture_rate": defaults_captured / total_defaults,
                "portfolio_review_share": review_count / total_applicants,
                "lift_vs_random_default_capture": lift_vs_random,
                "reviewed_credit_exposure": reviewed_credit_exposure,
                "reviewed_credit_exposure_share": reviewed_credit_exposure
                / total_credit_exposure,
                "default_credit_exposure_captured": reviewed_default_credit_exposure,
                "default_credit_exposure_capture_rate": reviewed_default_credit_exposure
                / total_default_credit_exposure,
                "expected_risk_exposure_reviewed": reviewed_expected_risk_exposure,
                "expected_risk_exposure_capture_rate": reviewed_expected_risk_exposure
                / total_expected_risk_exposure,
                "avg_default_probability_reviewed": reviewed[
                    "default_probability"
                ].mean(),
                "min_default_probability_reviewed": reviewed[
                    "default_probability"
                ].min(),
            }
        )

    return pd.DataFrame(rows)


def format_currency_proxy(value: float) -> str:
    """Format exposure proxy values without implying a real currency decision."""
    return f"{value:,.0f}"


def markdown_table(df: pd.DataFrame) -> str:
    """Render a DataFrame as markdown without optional dependencies."""
    if df.empty:
        return "_No rows to display._"
    safe_df = df.copy()
    for column in safe_df.columns:
        if column == "review_rate_percent":
            safe_df[column] = safe_df[column].astype(float).round(2)
        elif column.endswith("_percent") or column.endswith("_rate") or column.endswith("_share"):
            safe_df[column] = (safe_df[column].astype(float) * 100).round(2)
        elif column in {
            "lift_vs_random_default_capture",
            "avg_default_probability_reviewed",
            "min_default_probability_reviewed",
        }:
            safe_df[column] = safe_df[column].astype(float).round(4)
        elif "exposure" in column:
            safe_df[column] = safe_df[column].astype(float).map(format_currency_proxy)
    safe_df = safe_df.fillna("").astype(str)
    rows = ["| " + " | ".join(safe_df.columns) + " |"]
    rows.append("| " + " | ".join("---" for _ in safe_df.columns) + " |")
    rows.extend(
        "| " + " | ".join(row) + " |"
        for row in safe_df.itertuples(index=False, name=None)
    )
    return "\n".join(rows)


def build_summary_report(impact: pd.DataFrame, scored: pd.DataFrame) -> str:
    """Build a business-readable impact summary."""
    compact = impact[
        [
            "review_rate_percent",
            "applicants_reviewed",
            "defaults_captured",
            "default_capture_rate",
            "lift_vs_random_default_capture",
            "default_credit_exposure_capture_rate",
            "expected_risk_exposure_capture_rate",
            "avg_default_probability_reviewed",
            "min_default_probability_reviewed",
        ]
    ].copy()
    top_10 = impact.loc[np.isclose(impact["review_rate"], 0.10)]
    if top_10.empty:
        top_row = impact.iloc[(impact["review_rate"] - 0.10).abs().argsort().iloc[0]]
    else:
        top_row = top_10.iloc[0]

    return "\n".join(
        [
            "# Business Impact Summary",
            "",
            "This report converts model-ranked default probabilities into business "
            "review-capacity scenarios. It uses actual `TARGET` labels, final model "
            "scores, and `AMT_CREDIT` as a credit-exposure proxy. It does not invent "
            "currency loss assumptions or claim realized collections recovery.",
            "",
            "## Portfolio Context",
            "",
            f"- Applicants scored: `{len(scored):,}`",
            f"- Observed defaults: `{int(scored['TARGET'].sum()):,}`",
            f"- Observed default rate: `{scored['TARGET'].mean() * 100:.2f}%`",
            f"- Total credit exposure proxy: `{format_currency_proxy(scored['credit_amount'].sum())}`",
            "",
            "## Review Capacity Results",
            "",
            markdown_table(compact),
            "",
            "## Key Interpretation",
            "",
            f"At a `{top_row['review_rate_percent']:.0f}%` review capacity, the model-ranked "
            f"queue reviews `{int(top_row['applicants_reviewed']):,}` applicants and captures "
            f"`{top_row['default_capture_rate'] * 100:.2f}%` of observed defaults. "
            f"This is `{top_row['lift_vs_random_default_capture']:.2f}x` the default capture "
            "expected from a random review queue of the same size.",
            "",
            "The exposure columns are decision-support proxies. In a real production "
            "deployment, expected loss would require additional assumptions such as exposure "
            "at default, loss given default, collections cost, cure rate, and customer contact "
            "capacity.",
            "",
            "## Recommended Business Use",
            "",
            "- Use the top-risk capacity table to choose review queue size based on team capacity.",
            "- Pair default capture with credit exposure capture to balance risk and operational load.",
            "- Treat the output as prioritization guidance, not an automatic adverse-action policy.",
            "- Re-estimate impact after calibration, fairness review, and production monitoring.",
            "",
            "## Saved Outputs",
            "",
            f"- `{OUTPUT_PATH.as_posix()}`",
            f"- `{SUMMARY_PATH.as_posix()}`",
            "",
        ]
    )


def run(review_rates: list[float] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run impact analysis and save outputs."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    model_bundle = load_model_bundle()
    data = load_scoring_data(model_bundle["feature_columns"])
    scored = score_portfolio(data, model_bundle)
    impact = evaluate_review_capacity(
        scored, review_rates=review_rates or DEFAULT_REVIEW_RATES
    )
    impact.to_csv(OUTPUT_PATH, index=False)
    SUMMARY_PATH.write_text(build_summary_report(impact, scored), encoding="utf-8")
    return scored, impact


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    _, impact = run(review_rates=args.review_rates)
    print("Business impact analysis complete.")
    print(f"Impact table saved to: {OUTPUT_PATH}")
    print(f"Summary saved to: {SUMMARY_PATH}")
    print("\nReview capacity summary:")
    print(
        impact[
            [
                "review_rate_percent",
                "applicants_reviewed",
                "defaults_captured",
                "default_capture_rate",
                "lift_vs_random_default_capture",
                "expected_risk_exposure_capture_rate",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
