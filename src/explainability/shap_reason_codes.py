"""Generate SHAP explainability and applicant-level reason codes.

Run from the project root:
    python src/explainability/shap_reason_codes.py
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

REPORTS_DIR = Path("reports")
FIGURES_DIR = REPORTS_DIR / "figures"
MPL_CACHE_DIR = REPORTS_DIR / ".matplotlib-cache"
FONT_CACHE_DIR = REPORTS_DIR / ".cache"
MPL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
FONT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE_DIR))
os.environ.setdefault("XDG_CACHE_HOME", str(FONT_CACHE_DIR))

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap


MODEL_PATH = Path("models/credit_risk_model.pkl")
FEATURE_PATH = Path("data/processed/model_features.parquet")
SHAP_SUMMARY_PATH = FIGURES_DIR / "shap_summary.png"
SHAP_BAR_PATH = FIGURES_DIR / "shap_bar.png"
REASON_CODES_PATH = REPORTS_DIR / "sample_reason_codes.csv"
REPORT_PATH = REPORTS_DIR / "explainability_summary.md"
RANDOM_STATE = 42

REASON_CODE_RULES = {
    "credit_to_income_ratio": "High credit-to-income ratio",
    "loan_to_income_ratio": "High loan-to-income ratio",
    "annuity_to_income_ratio": "High annuity burden",
    "annuity_to_credit_ratio": "High annuity burden",
    "external_score_mean": "Low external credit score",
    "external_score_std": "Inconsistent external credit scores",
    "EXT_SOURCE_1": "Low external credit score",
    "EXT_SOURCE_2": "Low external credit score",
    "EXT_SOURCE_3": "Low external credit score",
    "employment_years": "Short employment duration",
    "DAYS_EMPLOYED": "Short employment duration",
    "age_years": "Applicant age risk signal",
    "missing_value_count": "High missing information count",
    "bureau_credit_count": "Missing credit bureau signal",
    "bureau_balance_month_count": "Limited bureau balance history",
    "bureau_balance_late_status_count": "Prior bureau delinquency signal",
    "bureau_overdue_credit_count": "Prior overdue bureau credit",
    "bureau_credit_day_overdue_max": "Prior overdue bureau credit",
    "bureau_credit_debt_to_credit_ratio": "High bureau debt burden",
    "installment_late_payment_count": "Prior repayment delay",
    "installment_avg_payment_delay_days": "Prior repayment delay",
    "installment_max_payment_delay_days": "Prior repayment delay",
    "pos_cash_late_count": "Prior POS repayment delay",
    "pos_cash_max_dpd_def": "Prior POS repayment delay",
    "pos_cash_avg_installments_future": "POS repayment profile signal",
    "credit_card_max_dpd": "Prior credit card repayment delay",
    "credit_card_avg_balance": "High credit card balance",
    "credit_card_max_balance": "High credit card balance",
    "previous_refused_count": "Prior refused application history",
    "previous_application_count": "Multiple previous applications",
}


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Generate SHAP reason codes.")
    parser.add_argument(
        "--sample-size",
        type=int,
        default=5000,
        help="Number of rows to sample for SHAP global analysis.",
    )
    parser.add_argument(
        "--reason-code-sample-size",
        type=int,
        default=100,
        help="Number of highest-risk sampled applicants to write reason codes for.",
    )
    return parser.parse_args()


def load_model_bundle() -> dict[str, Any]:
    """Load the saved final model bundle."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Missing models/credit_risk_model.pkl. "
            "Run python src/models/train_final_model.py first."
        )
    return joblib.load(MODEL_PATH)


def load_feature_data(feature_columns: list[str]) -> pd.DataFrame:
    """Load processed features and retain IDs plus model columns."""
    if not FEATURE_PATH.exists():
        raise FileNotFoundError(
            "Missing data/processed/model_features.parquet. "
            "Run python src/features/pyspark_feature_engineering.py first."
        )
    data = pd.read_parquet(FEATURE_PATH).replace([np.inf, -np.inf], np.nan).fillna(0)
    missing_columns = [column for column in feature_columns if column not in data.columns]
    if missing_columns:
        raise ValueError(
            "Processed features are missing model columns: "
            + ", ".join(missing_columns[:20])
        )
    return data


def sample_for_shap(data: pd.DataFrame, sample_size: int) -> pd.DataFrame:
    """Sample data reproducibly for SHAP analysis."""
    if sample_size >= len(data):
        return data.copy()
    return data.sample(n=sample_size, random_state=RANDOM_STATE)


def positive_class_shap_values(explainer: shap.TreeExplainer, X: pd.DataFrame) -> np.ndarray:
    """Return SHAP values for the positive/default class."""
    shap_values = explainer.shap_values(X)
    if isinstance(shap_values, list):
        return np.asarray(shap_values[1])
    shap_array = np.asarray(shap_values)
    if shap_array.ndim == 3:
        return shap_array[:, :, 1]
    return shap_array


def global_importance(shap_values: np.ndarray, feature_columns: list[str]) -> pd.DataFrame:
    """Compute mean absolute SHAP feature importance."""
    importance = pd.DataFrame(
        {
            "feature": feature_columns,
            "mean_abs_shap": np.abs(shap_values).mean(axis=0),
            "mean_shap": shap_values.mean(axis=0),
        }
    )
    return importance.sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)


def save_shap_plots(
    shap_values: np.ndarray, X_sample: pd.DataFrame, importance: pd.DataFrame
) -> list[Path]:
    """Save SHAP summary and bar plots."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    plt.figure()
    shap.summary_plot(shap_values, X_sample, show=False, max_display=20)
    plt.tight_layout()
    plt.savefig(SHAP_SUMMARY_PATH, dpi=160, bbox_inches="tight")
    plt.close()

    top_importance = importance.head(20).sort_values("mean_abs_shap")
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.barh(top_importance["feature"], top_importance["mean_abs_shap"], color="#3c6e71")
    ax.set_title("Top Global SHAP Feature Importance")
    ax.set_xlabel("Mean absolute SHAP value")
    fig.tight_layout()
    fig.savefig(SHAP_BAR_PATH, dpi=160)
    plt.close(fig)

    return [SHAP_SUMMARY_PATH, SHAP_BAR_PATH]


def reason_code_for_feature(feature: str, value: float) -> str:
    """Map a technical feature into a business-readable reason code."""
    if feature in {"EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3", "external_score_mean"}:
        if value <= 0.40:
            return "Low external credit score"
        return "External credit score risk signal"
    if feature == "employment_years":
        if value <= 2:
            return "Short employment duration"
        return "Employment duration risk signal"
    if feature in {"annuity_to_income_ratio", "annuity_to_credit_ratio"}:
        if value >= 0.20:
            return "High annuity burden"
        return "Annuity burden risk signal"
    if feature in {"credit_to_income_ratio", "loan_to_income_ratio"}:
        if value >= 3:
            return "High credit-to-income ratio"
        return "Credit-to-income risk signal"
    if feature in {"bureau_credit_count", "bureau_balance_month_count"}:
        if value <= 0:
            return "Missing credit bureau signal"
        return "Credit bureau history signal"
    if feature in {
        "installment_late_payment_count",
        "installment_avg_payment_delay_days",
        "installment_max_payment_delay_days",
        "pos_cash_late_count",
        "pos_cash_max_dpd_def",
        "credit_card_max_dpd",
        "bureau_balance_late_status_count",
        "bureau_overdue_credit_count",
        "bureau_credit_day_overdue_max",
    }:
        if value > 0:
            return "Prior repayment delay"
        return "Repayment history risk signal"
    if feature == "pos_cash_month_count":
        if value <= 0:
            return "Limited POS repayment history"
        return "POS repayment history signal"

    if feature in REASON_CODE_RULES:
        return REASON_CODE_RULES[feature]

    if feature.endswith("_idx"):
        return f"Categorical segment signal: {feature.removesuffix('_idx')}"
    if "EXT_SOURCE" in feature:
        return "Low external credit score"
    if "delay" in feature.lower() or "dpd" in feature.lower() or "overdue" in feature.lower():
        return "Prior repayment delay"
    if "income" in feature.lower() and value > 0:
        return "Income or affordability risk signal"
    if "credit" in feature.lower() and value > 0:
        return "Credit exposure risk signal"
    if "bureau" in feature.lower():
        return "Credit bureau history signal"
    return f"Model risk signal: {feature}"


def build_applicant_reason_codes(
    data_sample: pd.DataFrame,
    X_sample: pd.DataFrame,
    shap_values: np.ndarray,
    model: Any,
    top_n: int = 3,
    reason_code_sample_size: int = 100,
) -> pd.DataFrame:
    """Build applicant-level reason codes from positive SHAP contributions."""
    probabilities = model.predict_proba(X_sample)[:, 1]
    sample = data_sample.copy()
    sample["default_probability"] = probabilities
    sample = sample.sort_values("default_probability", ascending=False).head(
        reason_code_sample_size
    )

    rows = []
    feature_columns = X_sample.columns.tolist()
    for row_position, (idx, row) in enumerate(sample.iterrows()):
        original_position = data_sample.index.get_loc(idx)
        applicant_shap = shap_values[original_position]
        positive_indices = np.where(applicant_shap > 0)[0]
        ordered_indices = positive_indices[np.argsort(applicant_shap[positive_indices])[::-1]]
        top_indices = ordered_indices[:top_n]

        reason_codes = []
        reason_features = []
        reason_values = []
        reason_shap_values = []
        for feature_idx in top_indices:
            feature = feature_columns[feature_idx]
            value = X_sample.loc[idx, feature]
            reason_codes.append(reason_code_for_feature(feature, float(value)))
            reason_features.append(feature)
            reason_values.append(float(value))
            reason_shap_values.append(float(applicant_shap[feature_idx]))

        while len(reason_codes) < top_n:
            reason_codes.append("No additional positive SHAP risk driver")
            reason_features.append("")
            reason_values.append(np.nan)
            reason_shap_values.append(0.0)

        rows.append(
            {
                "rank_in_sample": row_position + 1,
                "SK_ID_CURR": int(row.get("SK_ID_CURR", idx)),
                "default_probability": row["default_probability"],
                "reason_code_1": reason_codes[0],
                "reason_feature_1": reason_features[0],
                "reason_feature_value_1": reason_values[0],
                "reason_shap_value_1": reason_shap_values[0],
                "reason_code_2": reason_codes[1],
                "reason_feature_2": reason_features[1],
                "reason_feature_value_2": reason_values[1],
                "reason_shap_value_2": reason_shap_values[1],
                "reason_code_3": reason_codes[2],
                "reason_feature_3": reason_features[2],
                "reason_feature_value_3": reason_values[2],
                "reason_shap_value_3": reason_shap_values[2],
            }
        )

    return pd.DataFrame(rows)


def markdown_table(df: pd.DataFrame) -> str:
    """Render a DataFrame as a dependency-free markdown table."""
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


def build_report(
    sample_size: int,
    total_rows: int,
    importance: pd.DataFrame,
    reason_codes: pd.DataFrame,
    figure_paths: list[Path],
) -> str:
    """Build the explainability markdown report."""
    top_global = importance.head(15).copy()
    top_global["mean_abs_shap"] = top_global["mean_abs_shap"].round(6)
    top_global["mean_shap"] = top_global["mean_shap"].round(6)

    sample_reason_display = reason_codes[
        [
            "SK_ID_CURR",
            "default_probability",
            "reason_code_1",
            "reason_feature_1",
            "reason_code_2",
            "reason_feature_2",
            "reason_code_3",
            "reason_feature_3",
        ]
    ].head(10).copy()
    sample_reason_display["default_probability"] = sample_reason_display[
        "default_probability"
    ].round(4)

    return "\n".join(
        [
            "# Explainability Summary",
            "",
            "This report explains the saved final LightGBM credit-risk model using SHAP. "
            "Reason codes are generated only from positive applicant-level SHAP contributions, "
            "meaning each listed reason increased the model score for that applicant.",
            "",
            "## Scope",
            "",
            f"- Total processed rows available: `{total_rows:,}`",
            f"- SHAP sample size: `{sample_size:,}`",
            "- Model loaded from `models/credit_risk_model.pkl`",
            "- Features loaded from `data/processed/model_features.parquet`",
            "",
            "## Top Global Risk Drivers",
            "",
            markdown_table(top_global),
            "",
            "## Sample Applicant Reason Codes",
            "",
            markdown_table(sample_reason_display),
            "",
            "## Business Interpretation",
            "",
            "Global SHAP importance identifies the variables the model relies on most across "
            "the sampled portfolio. Applicant-level reason codes translate the largest "
            "positive SHAP contributors into review-friendly explanations such as affordability "
            "burden, external score weakness, limited bureau signal, or prior repayment delay. "
            "These explanations should support review, monitoring, and collections prioritization; "
            "they are not standalone approval or rejection rules.",
            "",
            "## Saved Outputs",
            "",
            *[f"- `{path.as_posix()}`" for path in figure_paths],
            f"- `{REASON_CODES_PATH.as_posix()}`",
            f"- `{REPORT_PATH.as_posix()}`",
            "",
        ]
    )


def run_explainability(
    sample_size: int = 5000, reason_code_sample_size: int = 100
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run SHAP explainability and save plots/reports."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    bundle = load_model_bundle()
    model = bundle["model"]
    feature_columns = bundle["feature_columns"]
    data = load_feature_data(feature_columns)
    data_sample = sample_for_shap(data, sample_size=sample_size)
    X_sample = data_sample[feature_columns]

    explainer = shap.TreeExplainer(model)
    shap_values = positive_class_shap_values(explainer, X_sample)
    importance = global_importance(shap_values, feature_columns)
    figure_paths = save_shap_plots(shap_values, X_sample, importance)
    reason_codes = build_applicant_reason_codes(
        data_sample=data_sample,
        X_sample=X_sample,
        shap_values=shap_values,
        model=model,
        reason_code_sample_size=reason_code_sample_size,
    )

    reason_codes.to_csv(REASON_CODES_PATH, index=False)
    REPORT_PATH.write_text(
        build_report(
            sample_size=len(data_sample),
            total_rows=len(data),
            importance=importance,
            reason_codes=reason_codes,
            figure_paths=figure_paths,
        ),
        encoding="utf-8",
    )
    return importance, reason_codes


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    importance, reason_codes = run_explainability(
        sample_size=args.sample_size,
        reason_code_sample_size=args.reason_code_sample_size,
    )
    print("SHAP explainability complete.")
    print(f"SHAP summary plot saved to: {SHAP_SUMMARY_PATH}")
    print(f"SHAP bar plot saved to: {SHAP_BAR_PATH}")
    print(f"Sample reason codes saved to: {REASON_CODES_PATH}")
    print(f"Explainability report saved to: {REPORT_PATH}")
    print("\nTop global risk drivers:")
    print(importance.head(10).to_string(index=False))
    print("\nSample applicant reason codes:")
    print(
        reason_codes[
            [
                "SK_ID_CURR",
                "default_probability",
                "reason_code_1",
                "reason_code_2",
                "reason_code_3",
            ]
        ]
        .head(5)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
