"""Exploratory data analysis utilities for the Home Credit base table.

Run from the project root:
    python src/data/eda_utils.py
"""

from __future__ import annotations

import os
from pathlib import Path

MATPLOTLIB_CACHE_DIR = Path("reports/.matplotlib-cache")
FONT_CACHE_DIR = Path("reports/.cache")
MATPLOTLIB_CACHE_DIR.mkdir(parents=True, exist_ok=True)
FONT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MATPLOTLIB_CACHE_DIR))
os.environ.setdefault("XDG_CACHE_HOME", str(FONT_CACHE_DIR))

import matplotlib.pyplot as plt
import pandas as pd


RAW_DATA_DIR = Path("data/raw")
REPORTS_DIR = Path("reports")
FIGURES_DIR = REPORTS_DIR / "figures"
EDA_REPORT_PATH = REPORTS_DIR / "eda_summary.md"
BASE_TABLE = "application_train.csv"
TARGET_COLUMN = "TARGET"
CSV_ENCODINGS = ("utf-8", "latin1")

NUMERIC_FEATURES = [
    "AMT_INCOME_TOTAL",
    "AMT_CREDIT",
    "AMT_ANNUITY",
    "AGE_YEARS",
    "EMPLOYMENT_YEARS",
    "EXT_SOURCE_1",
    "EXT_SOURCE_2",
    "EXT_SOURCE_3",
]

CATEGORICAL_FEATURES = [
    "NAME_CONTRACT_TYPE",
    "CODE_GENDER",
    "NAME_EDUCATION_TYPE",
    "NAME_FAMILY_STATUS",
    "NAME_HOUSING_TYPE",
    "OCCUPATION_TYPE",
]


def read_csv_with_encoding_fallback(csv_path: Path, **kwargs: object) -> pd.DataFrame:
    """Read a CSV with a small encoding fallback for source metadata files."""
    last_error: UnicodeDecodeError | None = None

    for encoding in CSV_ENCODINGS:
        try:
            return pd.read_csv(csv_path, encoding=encoding, **kwargs)
        except UnicodeDecodeError as exc:
            last_error = exc

    raise UnicodeDecodeError(
        last_error.encoding if last_error else "unknown",
        last_error.object if last_error else b"",
        last_error.start if last_error else 0,
        last_error.end if last_error else 0,
        f"Could not read {csv_path} with encodings: {', '.join(CSV_ENCODINGS)}",
    )


def load_application_train(raw_data_dir: Path = RAW_DATA_DIR) -> pd.DataFrame:
    """Load the base application table and validate TARGET."""
    csv_path = raw_data_dir / BASE_TABLE
    if not csv_path.is_file():
        raise FileNotFoundError(
            f"Missing {BASE_TABLE} under data/raw/. "
            "Place the Home Credit raw files in data/raw/ and rerun."
        )

    df = read_csv_with_encoding_fallback(csv_path)
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Expected column '{TARGET_COLUMN}' was not found in {BASE_TABLE}.")

    return add_credit_risk_features(df)


def add_credit_risk_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add EDA-only interpretable features without changing raw data."""
    enriched = df.copy()
    enriched["AGE_YEARS"] = (-enriched["DAYS_BIRTH"] / 365.25).round(1)

    employed_days = enriched["DAYS_EMPLOYED"].where(enriched["DAYS_EMPLOYED"] != 365243)
    enriched["EMPLOYMENT_YEARS"] = (-employed_days / 365.25).round(1)

    return enriched


def target_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Return TARGET counts and default-rate context."""
    counts = df[TARGET_COLUMN].value_counts(dropna=False).sort_index()
    return pd.DataFrame(
        {
            "target": counts.index.astype(str),
            "count": counts.values,
            "share_percent": (counts.values / len(df) * 100).round(2),
        }
    )


def missing_value_summary(df: pd.DataFrame, top_n: int = 25) -> pd.DataFrame:
    """Return top missing-value columns."""
    missing_count = df.isna().sum()
    missing_percent = (missing_count / len(df) * 100).round(2)
    summary = pd.DataFrame(
        {
            "column": missing_count.index,
            "missing_count": missing_count.values,
            "missing_percent": missing_percent.values,
            "dtype": df.dtypes.astype(str).values,
        }
    )
    return (
        summary[summary["missing_count"] > 0]
        .sort_values(["missing_percent", "column"], ascending=[False, True])
        .head(top_n)
        .reset_index(drop=True)
    )


def numeric_feature_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize credit-risk numeric features."""
    rows = []
    for feature in NUMERIC_FEATURES:
        if feature not in df.columns:
            continue

        series = df[feature]
        rows.append(
            {
                "feature": feature,
                "non_null": int(series.notna().sum()),
                "missing_percent": round(series.isna().mean() * 100, 2),
                "mean": round(series.mean(), 2),
                "median": round(series.median(), 2),
                "p25": round(series.quantile(0.25), 2),
                "p75": round(series.quantile(0.75), 2),
            }
        )

    return pd.DataFrame(rows)


def categorical_feature_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize cardinality and missingness for selected categorical features."""
    rows = []
    for feature in CATEGORICAL_FEATURES:
        if feature not in df.columns:
            continue

        rows.append(
            {
                "feature": feature,
                "unique_values": int(df[feature].nunique(dropna=True)),
                "missing_percent": round(df[feature].isna().mean() * 100, 2),
                "top_value": str(df[feature].mode(dropna=True).iloc[0]),
                "top_value_share_percent": round(
                    df[feature].value_counts(normalize=True, dropna=True).iloc[0] * 100,
                    2,
                ),
            }
        )

    return pd.DataFrame(rows)


def categorical_default_rates(
    df: pd.DataFrame, min_segment_size: int = 500
) -> pd.DataFrame:
    """Compare default rates across important categorical segments."""
    frames = []
    portfolio_default_rate = df[TARGET_COLUMN].mean()

    for feature in CATEGORICAL_FEATURES:
        if feature not in df.columns:
            continue

        grouped = (
            df.assign(segment=df[feature].fillna("Missing"))
            .groupby("segment", dropna=False)[TARGET_COLUMN]
            .agg(["count", "mean"])
            .reset_index()
            .rename(columns={"mean": "default_rate"})
        )
        grouped = grouped[grouped["count"] >= min_segment_size]
        grouped["feature"] = feature
        grouped["default_rate_percent"] = (grouped["default_rate"] * 100).round(2)
        grouped["portfolio_lift"] = (
            grouped["default_rate"] / portfolio_default_rate
        ).round(2)
        frames.append(
            grouped[
                ["feature", "segment", "count", "default_rate_percent", "portfolio_lift"]
            ]
        )

    return (
        pd.concat(frames, ignore_index=True)
        .sort_values(["default_rate_percent", "count"], ascending=[False, False])
        .reset_index(drop=True)
    )


def numeric_default_rates(df: pd.DataFrame, bins: int = 5) -> pd.DataFrame:
    """Compare default rates across quantile bands for numeric credit-risk features."""
    frames = []
    portfolio_default_rate = df[TARGET_COLUMN].mean()

    for feature in NUMERIC_FEATURES:
        if feature not in df.columns:
            continue

        feature_df = df[[feature, TARGET_COLUMN]].dropna()
        if feature_df[feature].nunique() < 2:
            continue

        feature_df = feature_df.assign(
            band=pd.qcut(feature_df[feature], q=bins, duplicates="drop")
        )
        grouped = (
            feature_df.groupby("band", observed=True)[TARGET_COLUMN]
            .agg(["count", "mean"])
            .reset_index()
            .rename(columns={"mean": "default_rate"})
        )
        grouped["feature"] = feature
        grouped["band"] = grouped["band"].astype(str)
        grouped["default_rate_percent"] = (grouped["default_rate"] * 100).round(2)
        grouped["portfolio_lift"] = (
            grouped["default_rate"] / portfolio_default_rate
        ).round(2)
        frames.append(
            grouped[["feature", "band", "count", "default_rate_percent", "portfolio_lift"]]
        )

    return pd.concat(frames, ignore_index=True).reset_index(drop=True)


def plot_target_distribution(target_summary: pd.DataFrame) -> Path:
    """Save target imbalance bar chart."""
    output_path = FIGURES_DIR / "target_imbalance.png"
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(target_summary["target"], target_summary["share_percent"], color=["#2f6f73", "#c4493d"])
    ax.set_title("Target Imbalance: Repaid vs Default")
    ax.set_xlabel("TARGET")
    ax.set_ylabel("Share of applications (%)")
    ax.bar_label(ax.containers[0], fmt="%.2f%%")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path


def plot_missing_values(missing_summary: pd.DataFrame) -> Path:
    """Save top missing-value chart."""
    output_path = FIGURES_DIR / "top_missing_values.png"
    top_missing = missing_summary.head(15).sort_values("missing_percent")
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(top_missing["column"], top_missing["missing_percent"], color="#6d5f8d")
    ax.set_title("Top Missing-Value Columns")
    ax.set_xlabel("Missing values (%)")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path


def plot_segment_default_rates(segment_rates: pd.DataFrame) -> Path:
    """Save highest categorical segment default rates."""
    output_path = FIGURES_DIR / "categorical_segment_default_rates.png"
    plot_df = segment_rates.head(15).copy()
    plot_df["label"] = plot_df["feature"] + ": " + plot_df["segment"].astype(str)
    plot_df = plot_df.sort_values("default_rate_percent")

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(plot_df["label"], plot_df["default_rate_percent"], color="#b85c38")
    ax.set_title("Highest Default Rates Across Business Segments")
    ax.set_xlabel("Default rate (%)")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path


def plot_external_score_default_rates(numeric_rates: pd.DataFrame) -> Path:
    """Save default rates by external score bands."""
    output_path = FIGURES_DIR / "external_score_default_rates.png"
    score_df = numeric_rates[numeric_rates["feature"].isin(["EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3"])]

    fig, ax = plt.subplots(figsize=(10, 5))
    for feature, feature_df in score_df.groupby("feature"):
        ax.plot(
            range(len(feature_df)),
            feature_df["default_rate_percent"],
            marker="o",
            label=feature,
        )

    ax.set_title("Default Rate by External Score Quantile")
    ax.set_xlabel("Quantile band, low score to high score")
    ax.set_ylabel("Default rate (%)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path


def markdown_table(df: pd.DataFrame) -> str:
    """Render a DataFrame as a dependency-free markdown table."""
    if df.empty:
        return "_No rows to display._"

    safe_df = df.fillna("").astype(str)
    headers = safe_df.columns.tolist()
    rows = ["| " + " | ".join(headers) + " |"]
    rows.append("| " + " | ".join("---" for _ in headers) + " |")
    rows.extend(
        "| " + " | ".join(row) + " |"
        for row in safe_df.itertuples(index=False, name=None)
    )
    return "\n".join(rows)


def build_findings(
    df: pd.DataFrame,
    target_summary: pd.DataFrame,
    missing_summary: pd.DataFrame,
    segment_rates: pd.DataFrame,
    numeric_rates: pd.DataFrame,
) -> list[str]:
    """Create data-backed, business-readable EDA findings."""
    default_rate = df[TARGET_COLUMN].mean() * 100
    default_count = int(df[TARGET_COLUMN].sum())
    total_count = len(df)

    top_segment = segment_rates.iloc[0]
    missing_high = missing_summary[missing_summary["missing_percent"] >= 50]

    ext_score_rates = numeric_rates[numeric_rates["feature"].isin(["EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3"])]
    highest_ext = ext_score_rates.sort_values("default_rate_percent", ascending=False).iloc[0]
    lowest_ext = ext_score_rates.sort_values("default_rate_percent", ascending=True).iloc[0]

    age_rates = numeric_rates[numeric_rates["feature"] == "AGE_YEARS"].copy()
    highest_age = age_rates.sort_values("default_rate_percent", ascending=False).iloc[0]

    findings = [
        (
            f"The portfolio is highly imbalanced: {default_count:,} of {total_count:,} "
            f"applications defaulted, a {default_rate:.2f}% default rate. Modeling should "
            "therefore emphasize ranking, recall, PR-AUC, calibration, and top-K capture "
            "instead of accuracy."
        ),
        (
            f"The highest observed categorical segment is {top_segment['feature']} = "
            f"{top_segment['segment']}, with a {top_segment['default_rate_percent']}% "
            f"default rate across {int(top_segment['count']):,} applications. This is a useful "
            "candidate for underwriting policy review and collections prioritization, not a "
            "standalone decision rule."
        ),
        (
            f"{len(missing_high)} columns have at least 50% missing values. Many are housing "
            "or building attributes, so missingness itself may carry applicant profile signal "
            "but must be handled carefully in feature engineering."
        ),
        (
            f"External score bands show strong risk separation: {highest_ext['feature']} band "
            f"{highest_ext['band']} has a {highest_ext['default_rate_percent']}% default rate, "
            f"while {lowest_ext['feature']} band {lowest_ext['band']} has "
            f"{lowest_ext['default_rate_percent']}%. These variables should be checked for "
            "availability, stability, and leakage risk before modeling."
        ),
        (
            f"Age bands differ materially: the riskiest age band is {highest_age['band']} with "
            f"a {highest_age['default_rate_percent']}% default rate. This supports segment-level "
            "risk monitoring, while any model use must still be reviewed for fairness and policy "
            "constraints."
        ),
    ]

    return findings


def build_eda_report(
    df: pd.DataFrame,
    target_summary: pd.DataFrame,
    missing_summary: pd.DataFrame,
    numeric_summary: pd.DataFrame,
    categorical_summary: pd.DataFrame,
    segment_rates: pd.DataFrame,
    numeric_rates: pd.DataFrame,
    figure_paths: list[Path],
    findings: list[str],
) -> str:
    """Build the business-readable EDA markdown report."""
    top_numeric_rates = numeric_rates.sort_values(
        "default_rate_percent", ascending=False
    ).head(20)

    return "\n".join(
        [
            "# EDA Summary",
            "",
            "This report analyzes `data/raw/application_train.csv` only. Raw data is read "
            "from disk and is not modified.",
            "",
            "## Scope",
            "",
            f"- Rows analyzed: `{len(df):,}`",
            f"- Columns analyzed: `{df.shape[1]:,}` including EDA-only derived age and employment fields",
            "- Sampling: no sampling used; full `application_train.csv` was analyzed.",
            "- Modeling: no model training was performed.",
            "",
            "## Top 5 Business Findings",
            "",
            *[f"{idx}. {finding}" for idx, finding in enumerate(findings, start=1)],
            "",
            "## Target Imbalance",
            "",
            markdown_table(target_summary),
            "",
            "## Missing Values",
            "",
            markdown_table(missing_summary),
            "",
            "## Numerical Credit-Risk Features",
            "",
            markdown_table(numeric_summary),
            "",
            "## Categorical Business Features",
            "",
            markdown_table(categorical_summary),
            "",
            "## Highest Default Rates Across Categorical Segments",
            "",
            markdown_table(segment_rates.head(25)),
            "",
            "## Highest Default Rates Across Numeric Quantile Bands",
            "",
            markdown_table(top_numeric_rates),
            "",
            "## Figures",
            "",
            *[f"- `{path.as_posix()}`" for path in figure_paths],
            "",
            "## Business Interpretation",
            "",
            "This EDA is intended to guide later feature engineering and validation. Segments "
            "with higher default rates are risk signals for monitoring and prioritization, but "
            "they should not be used as hard policy rules without fairness, stability, and "
            "leakage review. Missingness patterns should be treated as a feature-engineering "
            "question rather than cleaned away mechanically.",
            "",
        ]
    )


def run_eda() -> dict[str, pd.DataFrame | list[Path] | list[str]]:
    """Run EDA, save plots/report, and return key artifacts for notebooks."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    df = load_application_train()
    target_summary = target_distribution(df)
    missing_summary = missing_value_summary(df)
    numeric_summary = numeric_feature_summary(df)
    categorical_summary = categorical_feature_summary(df)
    segment_rates = categorical_default_rates(df)
    numeric_rates = numeric_default_rates(df)

    figure_paths = [
        plot_target_distribution(target_summary),
        plot_missing_values(missing_summary),
        plot_segment_default_rates(segment_rates),
        plot_external_score_default_rates(numeric_rates),
    ]

    findings = build_findings(
        df=df,
        target_summary=target_summary,
        missing_summary=missing_summary,
        segment_rates=segment_rates,
        numeric_rates=numeric_rates,
    )

    report = build_eda_report(
        df=df,
        target_summary=target_summary,
        missing_summary=missing_summary,
        numeric_summary=numeric_summary,
        categorical_summary=categorical_summary,
        segment_rates=segment_rates,
        numeric_rates=numeric_rates,
        figure_paths=figure_paths,
        findings=findings,
    )
    EDA_REPORT_PATH.write_text(report, encoding="utf-8")

    return {
        "data": df,
        "target_summary": target_summary,
        "missing_summary": missing_summary,
        "numeric_summary": numeric_summary,
        "categorical_summary": categorical_summary,
        "segment_rates": segment_rates,
        "numeric_rates": numeric_rates,
        "figure_paths": figure_paths,
        "findings": findings,
    }


def main() -> None:
    """CLI entry point."""
    artifacts = run_eda()
    data = artifacts["data"]
    findings = artifacts["findings"]
    figure_paths = artifacts["figure_paths"]

    print("EDA complete.")
    print(f"Rows analyzed: {len(data):,}")
    print(f"Report saved to: {EDA_REPORT_PATH}")
    print("Figures saved:")
    for path in figure_paths:
        print(f"- {path}")
    print("\nTop 5 findings:")
    for idx, finding in enumerate(findings, start=1):
        print(f"{idx}. {finding}")


if __name__ == "__main__":
    main()
