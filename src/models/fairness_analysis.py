"""Run proxy fairness and segment-performance analysis for the final model.

Run from the project root:
    python src/models/fairness_analysis.py
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
from sklearn.metrics import average_precision_score, roc_auc_score


RAW_APPLICATION_PATH = Path("data/raw/application_train.csv")
FEATURE_PATH = Path("data/processed/model_features.parquet")
MODEL_PATH = Path("models/credit_risk_model.pkl")
OUTPUT_PATH = REPORTS_DIR / "fairness_proxy_metrics.csv"
SUMMARY_PATH = REPORTS_DIR / "fairness_proxy_analysis.md"
TOP_K = 0.10

RAW_SEGMENT_COLUMNS = [
    "SK_ID_CURR",
    "CODE_GENDER",
    "NAME_EDUCATION_TYPE",
    "NAME_FAMILY_STATUS",
    "OCCUPATION_TYPE",
    "DAYS_BIRTH",
    "AMT_INCOME_TOTAL",
]


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Run proxy fairness and segment-performance analysis."
    )
    parser.add_argument(
        "--min-segment-size",
        type=int,
        default=500,
        help="Minimum segment size included in the published report.",
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


def load_processed_features(feature_columns: list[str]) -> pd.DataFrame:
    """Load processed model features and labels."""
    if not FEATURE_PATH.exists():
        raise FileNotFoundError(
            "Missing data/processed/model_features.parquet. "
            "Run python src/features/pyspark_feature_engineering.py first."
        )
    data = pd.read_parquet(FEATURE_PATH).replace([np.inf, -np.inf], np.nan).fillna(0)
    required_columns = ["SK_ID_CURR", "TARGET", *feature_columns]
    missing_columns = [column for column in required_columns if column not in data.columns]
    if missing_columns:
        raise ValueError(
            "Processed feature data is missing required columns: "
            + ", ".join(missing_columns[:20])
        )
    return data


def load_raw_segments() -> pd.DataFrame | None:
    """Load readable segment columns from the raw application table when available."""
    if not RAW_APPLICATION_PATH.exists():
        return None
    return pd.read_csv(RAW_APPLICATION_PATH, usecols=RAW_SEGMENT_COLUMNS)


def age_band_from_days(days_birth: pd.Series) -> pd.Series:
    """Convert Home Credit negative DAYS_BIRTH values into applicant age bands."""
    age_years = (-days_birth / 365.25).clip(lower=18, upper=100)
    return pd.cut(
        age_years,
        bins=[17, 25, 35, 45, 55, 65, 100],
        labels=["18-25", "26-35", "36-45", "46-55", "56-65", "65+"],
        include_lowest=True,
    ).astype(str)


def income_band(income: pd.Series) -> pd.Series:
    """Create readable income bands."""
    return pd.cut(
        income,
        bins=[-np.inf, 100_000, 150_000, 200_000, 300_000, np.inf],
        labels=["<100k", "100k-150k", "150k-200k", "200k-300k", "300k+"],
    ).astype(str)


def encoded_segment(series: pd.Series, name: str) -> pd.Series:
    """Create readable labels for encoded categorical proxy values."""
    return name + "=" + series.fillna(-1).astype(float).round(0).astype(int).astype(str)


def build_scored_segments(
    features: pd.DataFrame,
    raw_segments: pd.DataFrame | None,
    model_bundle: dict[str, Any],
) -> pd.DataFrame:
    """Create scored applicant table with readable segment labels."""
    feature_columns = model_bundle["feature_columns"]
    probabilities = model_bundle["model"].predict_proba(features[feature_columns])[:, 1]
    scored = features[["SK_ID_CURR", "TARGET"]].copy()
    scored["default_probability"] = probabilities
    if raw_segments is not None:
        scored = scored.merge(raw_segments, on="SK_ID_CURR", how="left")
        scored["gender_proxy"] = scored["CODE_GENDER"].fillna("Missing").astype(str)
        scored["education_type"] = (
            scored["NAME_EDUCATION_TYPE"].fillna("Missing").astype(str)
        )
        scored["family_status"] = (
            scored["NAME_FAMILY_STATUS"].fillna("Missing").astype(str)
        )
        scored["occupation_type"] = scored["OCCUPATION_TYPE"].fillna("Missing").astype(str)
        scored["age_band"] = age_band_from_days(scored["DAYS_BIRTH"])
        scored["income_band"] = income_band(scored["AMT_INCOME_TOTAL"])
        scored.attrs["segment_source"] = "raw_application_categories"
    else:
        scored["gender_proxy"] = encoded_segment(features["CODE_GENDER_idx"], "CODE_GENDER_idx")
        scored["education_type"] = encoded_segment(
            features["NAME_EDUCATION_TYPE_idx"], "NAME_EDUCATION_TYPE_idx"
        )
        scored["family_status"] = encoded_segment(
            features["NAME_FAMILY_STATUS_idx"], "NAME_FAMILY_STATUS_idx"
        )
        scored["occupation_type"] = encoded_segment(
            features["OCCUPATION_TYPE_idx"], "OCCUPATION_TYPE_idx"
        )
        scored["age_band"] = age_band_from_days(features["DAYS_BIRTH"])
        scored["income_band"] = income_band(features["AMT_INCOME_TOTAL"])
        scored.attrs["segment_source"] = "processed_encoded_proxy_categories"
    top_threshold = float(np.quantile(scored["default_probability"], 1 - TOP_K))
    scored["global_top_10pct_review"] = scored["default_probability"] >= top_threshold
    return scored


def safe_roc_auc(y_true: pd.Series, scores: pd.Series) -> float | None:
    """Return ROC-AUC when both classes are present."""
    if y_true.nunique() < 2:
        return None
    return float(roc_auc_score(y_true, scores))


def safe_pr_auc(y_true: pd.Series, scores: pd.Series) -> float | None:
    """Return PR-AUC when both classes are present."""
    if y_true.nunique() < 2:
        return None
    return float(average_precision_score(y_true, scores))


def summarize_segments(
    scored: pd.DataFrame,
    segment_columns: list[str],
    min_segment_size: int,
) -> pd.DataFrame:
    """Compute segment-level performance and review-rate metrics."""
    rows: list[dict[str, Any]] = []
    total_rows = len(scored)
    for segment_column in segment_columns:
        for segment_value, group in scored.groupby(segment_column, dropna=False):
            applicant_count = len(group)
            if applicant_count < min_segment_size:
                continue
            defaults = int(group["TARGET"].sum())
            non_defaults = applicant_count - defaults
            reviewed = group[group["global_top_10pct_review"]]
            reviewed_defaults = int(reviewed["TARGET"].sum())
            reviewed_non_defaults = len(reviewed) - reviewed_defaults
            rows.append(
                {
                    "segment_type": segment_column,
                    "segment_value": str(segment_value),
                    "applicant_count": applicant_count,
                    "applicant_share": applicant_count / total_rows,
                    "observed_default_rate": float(group["TARGET"].mean()),
                    "mean_default_probability": float(
                        group["default_probability"].mean()
                    ),
                    "global_top10_review_rate": float(
                        group["global_top_10pct_review"].mean()
                    ),
                    "default_capture_rate_within_segment": (
                        reviewed_defaults / defaults if defaults else np.nan
                    ),
                    "non_default_review_rate": (
                        reviewed_non_defaults / non_defaults if non_defaults else np.nan
                    ),
                    "roc_auc": safe_roc_auc(
                        group["TARGET"], group["default_probability"]
                    ),
                    "pr_auc": safe_pr_auc(group["TARGET"], group["default_probability"]),
                }
            )
    return pd.DataFrame(rows).sort_values(
        ["segment_type", "applicant_count"], ascending=[True, False]
    )


def summarize_disparities(metrics: pd.DataFrame) -> pd.DataFrame:
    """Summarize max/min spread for key segment metrics."""
    rows = []
    for segment_type, group in metrics.groupby("segment_type"):
        for metric in [
            "observed_default_rate",
            "mean_default_probability",
            "global_top10_review_rate",
            "default_capture_rate_within_segment",
            "non_default_review_rate",
        ]:
            values = group[metric].dropna()
            if values.empty:
                continue
            rows.append(
                {
                    "segment_type": segment_type,
                    "metric": metric,
                    "min": values.min(),
                    "max": values.max(),
                    "absolute_gap": values.max() - values.min(),
                    "max_to_min_ratio": (
                        values.max() / values.min() if values.min() > 0 else np.nan
                    ),
                }
            )
    return pd.DataFrame(rows)


def markdown_table(df: pd.DataFrame) -> str:
    """Render a DataFrame as markdown without optional dependencies."""
    if df.empty:
        return "_No rows to display._"
    safe_df = df.copy()
    for column in safe_df.select_dtypes(include=[np.number]).columns:
        if "rate" in column or column.endswith("_share"):
            safe_df[column] = (safe_df[column] * 100).round(2)
        elif column in {"roc_auc", "pr_auc", "mean_default_probability"}:
            safe_df[column] = safe_df[column].round(4)
        else:
            safe_df[column] = safe_df[column].round(3)
    safe_df = safe_df.fillna("").astype(str)
    rows = ["| " + " | ".join(safe_df.columns) + " |"]
    rows.append("| " + " | ".join("---" for _ in safe_df.columns) + " |")
    rows.extend(
        "| " + " | ".join(row) + " |"
        for row in safe_df.itertuples(index=False, name=None)
    )
    return "\n".join(rows)


def build_report(
    metrics: pd.DataFrame,
    disparities: pd.DataFrame,
    scored: pd.DataFrame,
    min_segment_size: int,
) -> str:
    """Build the proxy fairness analysis report."""
    compact_columns = [
        "segment_type",
        "segment_value",
        "applicant_count",
        "observed_default_rate",
        "mean_default_probability",
        "global_top10_review_rate",
        "default_capture_rate_within_segment",
        "non_default_review_rate",
        "roc_auc",
        "pr_auc",
    ]
    highest_review = metrics.sort_values(
        "global_top10_review_rate", ascending=False
    ).head(12)
    largest_disparities = disparities.sort_values(
        "absolute_gap", ascending=False
    ).head(12)

    segment_source = scored.attrs.get("segment_source", "unknown")
    source_note = (
        "Readable raw application categories were available and used."
        if segment_source == "raw_application_categories"
        else "Raw application categories were not available locally, so encoded categorical "
        "feature proxies from `data/processed/model_features.parquet` were used for "
        "gender, education, family status, and occupation segments."
    )
    if segment_source == "raw_application_categories":
        segment_lines = [
            "- `gender_proxy`: raw `CODE_GENDER` from the dataset.",
            "- `age_band`: derived from `DAYS_BIRTH`.",
            "- `income_band`: derived from `AMT_INCOME_TOTAL`.",
            "- `education_type`: raw education category.",
            "- `family_status`: raw family status category.",
            "- `occupation_type`: raw occupation category with missing values labeled.",
        ]
    else:
        segment_lines = [
            "- `gender_proxy`: encoded `CODE_GENDER_idx` proxy from processed features.",
            "- `age_band`: derived from processed `DAYS_BIRTH`.",
            "- `income_band`: derived from processed `AMT_INCOME_TOTAL`.",
            "- `education_type`: encoded `NAME_EDUCATION_TYPE_idx` proxy.",
            "- `family_status`: encoded `NAME_FAMILY_STATUS_idx` proxy.",
            "- `occupation_type`: encoded `OCCUPATION_TYPE_idx` proxy.",
        ]

    return "\n".join(
        [
            "# Fairness and Proxy-Risk Analysis",
            "",
            "This report is a segment-performance and proxy-risk analysis for the saved "
            "credit-risk model. It is not a legal fairness certification, adverse-action "
            "review, or regulatory compliance audit.",
            "",
            "## Scope",
            "",
            f"- Applicants scored: `{len(scored):,}`",
            f"- Observed default rate: `{scored['TARGET'].mean() * 100:.2f}%`",
            f"- Global top-risk review policy: top `{int(TOP_K * 100)}%` of model scores",
            f"- Minimum segment size included: `{min_segment_size:,}` applicants",
            f"- Segment source: `{segment_source}`",
            f"- Segment source note: {source_note}",
            "",
            "## Segments Reviewed",
            "",
            *segment_lines,
            "",
            "## Highest Top-10% Review Rates",
            "",
            markdown_table(highest_review[compact_columns]),
            "",
            "## Largest Segment Gaps",
            "",
            markdown_table(largest_disparities),
            "",
            "## Full Segment Metrics",
            "",
            markdown_table(metrics[compact_columns]),
            "",
            "## Interpretation",
            "",
            "Segment differences can reflect true historical default-rate differences, "
            "data quality patterns, model behavior, or social/proxy bias. A production "
            "lending model would require deeper fair-lending review, policy review, "
            "feature governance, reject-inference analysis, and legal/compliance sign-off.",
            "",
            "For this portfolio project, the value is that segment performance is measured "
            "explicitly rather than hidden behind aggregate ROC-AUC or PR-AUC.",
            "",
            "## Saved Outputs",
            "",
            f"- `{OUTPUT_PATH.as_posix()}`",
            f"- `{SUMMARY_PATH.as_posix()}`",
            "",
        ]
    )


def run(min_segment_size: int = 500) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run proxy fairness analysis and save outputs."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    bundle = load_model_bundle()
    features = load_processed_features(bundle["feature_columns"])
    raw_segments = load_raw_segments()
    scored = build_scored_segments(features, raw_segments, bundle)
    metrics = summarize_segments(
        scored,
        segment_columns=[
            "gender_proxy",
            "age_band",
            "income_band",
            "education_type",
            "family_status",
            "occupation_type",
        ],
        min_segment_size=min_segment_size,
    )
    disparities = summarize_disparities(metrics)
    metrics.to_csv(OUTPUT_PATH, index=False)
    SUMMARY_PATH.write_text(
        build_report(metrics, disparities, scored, min_segment_size),
        encoding="utf-8",
    )
    return metrics, disparities


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    metrics, disparities = run(min_segment_size=args.min_segment_size)
    print("Fairness and proxy-risk analysis complete.")
    print(f"Segment metrics saved to: {OUTPUT_PATH}")
    print(f"Summary saved to: {SUMMARY_PATH}")
    print("\nHighest top-10% review-rate segments:")
    print(
        metrics.sort_values("global_top10_review_rate", ascending=False)
        .head(10)[
            [
                "segment_type",
                "segment_value",
                "applicant_count",
                "observed_default_rate",
                "global_top10_review_rate",
                "roc_auc",
            ]
        ]
        .to_string(index=False)
    )
    print("\nLargest segment gaps:")
    print(disparities.sort_values("absolute_gap", ascending=False).head(10).to_string(index=False))


if __name__ == "__main__":
    main()
