"""Generate model and data monitoring reports.

Run from the project root:
    python src/monitoring/evidently_monitoring.py
"""

from __future__ import annotations

import argparse
import html
import json
import os
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

REPORTS_DIR = Path("reports")
MPL_CACHE_DIR = REPORTS_DIR / ".matplotlib-cache"
MPL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE_DIR))

import joblib
import numpy as np
import pandas as pd

try:
    import evidently
except ImportError:  # pragma: no cover - depends on local env
    evidently = None

from src.models.metrics import evaluate_binary_classifier


FEATURE_PATH = Path("data/processed/model_features.parquet")
MODEL_PATH = Path("models/credit_risk_model.pkl")
MONITORING_REPORT_PATH = REPORTS_DIR / "monitoring_report.html"
DRIFT_REPORT_PATH = REPORTS_DIR / "drift_report.html"
SUMMARY_PATH = REPORTS_DIR / "monitoring_summary.md"
RANDOM_STATE = 42
PSI_ALERT_THRESHOLD = 0.20
MISSINGNESS_ALERT_THRESHOLD = 0.05


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Generate monitoring reports.")
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Optional row count to sample before splitting reference/current windows.",
    )
    return parser.parse_args()


def load_model_bundle() -> dict[str, Any]:
    """Load final model bundle."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Missing models/credit_risk_model.pkl. "
            "Run python src/models/train_final_model.py first."
        )
    return joblib.load(MODEL_PATH)


def load_feature_data(feature_columns: list[str], sample_size: int | None = None) -> pd.DataFrame:
    """Load processed model features."""
    if not FEATURE_PATH.exists():
        raise FileNotFoundError(
            "Missing data/processed/model_features.parquet. "
            "Run python src/features/pyspark_feature_engineering.py first."
        )
    data = pd.read_parquet(FEATURE_PATH).replace([np.inf, -np.inf], np.nan)
    required = ["TARGET", "SK_ID_CURR", *feature_columns]
    missing_columns = [column for column in required if column not in data.columns]
    if missing_columns:
        raise ValueError("Missing required columns: " + ", ".join(missing_columns[:20]))

    data = data[required].fillna(0)
    if sample_size and sample_size < len(data):
        data = data.sample(n=sample_size, random_state=RANDOM_STATE).sort_values("SK_ID_CURR")
    return data.reset_index(drop=True)


def split_reference_current(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split data into deterministic reference and current monitoring windows."""
    midpoint = len(data) // 2
    if midpoint == 0:
        raise ValueError("Need at least two rows for reference/current monitoring split.")
    return data.iloc[:midpoint].copy(), data.iloc[midpoint:].copy()


def add_predictions(df: pd.DataFrame, model_bundle: dict[str, Any]) -> pd.DataFrame:
    """Add model predictions to a DataFrame."""
    output = df.copy()
    features = model_bundle["feature_columns"]
    output["prediction"] = model_bundle["model"].predict_proba(output[features])[:, 1]
    return output


def population_stability_index(
    reference: pd.Series, current: pd.Series, bins: int = 10
) -> float:
    """Compute PSI for numeric distributions."""
    ref = pd.to_numeric(reference, errors="coerce").fillna(0)
    cur = pd.to_numeric(current, errors="coerce").fillna(0)
    quantiles = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    if len(quantiles) <= 2:
        quantiles = np.linspace(min(ref.min(), cur.min()), max(ref.max(), cur.max()), bins + 1)
    if len(np.unique(quantiles)) <= 1:
        return 0.0

    ref_counts = pd.cut(ref, bins=quantiles, include_lowest=True, duplicates="drop").value_counts(
        normalize=True, sort=False
    )
    cur_counts = pd.cut(cur, bins=quantiles, include_lowest=True, duplicates="drop").value_counts(
        normalize=True, sort=False
    )
    ref_pct = ref_counts.to_numpy() + 1e-6
    cur_pct = cur_counts.reindex(ref_counts.index, fill_value=0).to_numpy() + 1e-6
    return float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))


def numeric_drift_table(
    reference: pd.DataFrame, current: pd.DataFrame, feature_columns: list[str]
) -> pd.DataFrame:
    """Compute feature-level numeric drift metrics."""
    rows = []
    for feature in feature_columns:
        psi = population_stability_index(reference[feature], current[feature])
        ref_mean = reference[feature].mean()
        cur_mean = current[feature].mean()
        rows.append(
            {
                "feature": feature,
                "reference_mean": ref_mean,
                "current_mean": cur_mean,
                "mean_change": cur_mean - ref_mean,
                "psi": psi,
                "drift_flag": psi >= PSI_ALERT_THRESHOLD,
            }
        )
    return pd.DataFrame(rows).sort_values("psi", ascending=False).reset_index(drop=True)


def missingness_table(
    reference: pd.DataFrame, current: pd.DataFrame, feature_columns: list[str]
) -> pd.DataFrame:
    """Compare missing-value rates between windows."""
    rows = []
    for feature in feature_columns:
        ref_missing = reference[feature].isna().mean()
        cur_missing = current[feature].isna().mean()
        rows.append(
            {
                "feature": feature,
                "reference_missing_rate": ref_missing,
                "current_missing_rate": cur_missing,
                "missing_rate_change": cur_missing - ref_missing,
                "missingness_flag": abs(cur_missing - ref_missing) >= MISSINGNESS_ALERT_THRESHOLD,
            }
        )
    return pd.DataFrame(rows).sort_values(
        "missing_rate_change", ascending=False
    ).reset_index(drop=True)


def prediction_drift(reference: pd.DataFrame, current: pd.DataFrame) -> dict[str, float]:
    """Compare prediction score distributions."""
    return {
        "reference_prediction_mean": float(reference["prediction"].mean()),
        "current_prediction_mean": float(current["prediction"].mean()),
        "prediction_mean_change": float(current["prediction"].mean() - reference["prediction"].mean()),
        "prediction_psi": population_stability_index(reference["prediction"], current["prediction"]),
        "reference_top_decile_mean": float(reference["prediction"].quantile(0.90)),
        "current_top_decile_mean": float(current["prediction"].quantile(0.90)),
    }


def performance_metrics(df: pd.DataFrame, threshold: float) -> dict[str, float | int]:
    """Compute model performance metrics when labels are available."""
    return evaluate_binary_classifier(
        y_true=df["TARGET"].to_numpy(),
        y_score=df["prediction"].to_numpy(),
        threshold=threshold,
        top_k=0.10,
    )


def markdown_table(df: pd.DataFrame, max_rows: int = 20) -> str:
    """Render a DataFrame as a markdown table."""
    if df.empty:
        return "_No rows to display._"
    display = df.head(max_rows).copy()
    for column in display.select_dtypes(include=[float]).columns:
        display[column] = display[column].round(6)
    safe_df = display.fillna("").astype(str)
    rows = ["| " + " | ".join(safe_df.columns) + " |"]
    rows.append("| " + " | ".join("---" for _ in safe_df.columns) + " |")
    rows.extend(
        "| " + " | ".join(row) + " |"
        for row in safe_df.itertuples(index=False, name=None)
    )
    return "\n".join(rows)


def html_table(df: pd.DataFrame, max_rows: int = 50) -> str:
    """Render a DataFrame as a simple HTML table."""
    display = df.head(max_rows).copy()
    for column in display.select_dtypes(include=[float]).columns:
        display[column] = display[column].round(6)
    headers = "".join(f"<th>{html.escape(str(col))}</th>" for col in display.columns)
    body_rows = []
    for row in display.itertuples(index=False, name=None):
        body_rows.append(
            "<tr>" + "".join(f"<td>{html.escape(str(value))}</td>" for value in row) + "</tr>"
        )
    return f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"


def write_html_report(
    path: Path,
    title: str,
    sections: list[tuple[str, str]],
) -> None:
    """Write a minimal standalone HTML report."""
    style = """
    body { font-family: Arial, sans-serif; margin: 32px; color: #1f2933; }
    h1, h2 { color: #12343b; }
    table { border-collapse: collapse; width: 100%; margin: 12px 0 28px; font-size: 13px; }
    th, td { border: 1px solid #d7dde2; padding: 7px; text-align: left; }
    th { background: #eef3f6; }
    .note { background: #f6f8fa; border-left: 4px solid #3c6e71; padding: 12px; }
    """
    section_html = "\n".join(f"<h2>{html.escape(name)}</h2>\n{content}" for name, content in sections)
    path.write_text(
        f"<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(title)}</title>"
        f"<style>{style}</style></head><body><h1>{html.escape(title)}</h1>{section_html}</body></html>",
        encoding="utf-8",
    )


def build_summary(
    reference: pd.DataFrame,
    current: pd.DataFrame,
    drift: pd.DataFrame,
    missingness: pd.DataFrame,
    pred_drift: dict[str, float],
    reference_perf: dict[str, Any],
    current_perf: dict[str, Any],
    evidently_status: str,
) -> str:
    """Build markdown monitoring summary."""
    drifted_count = int(drift["drift_flag"].sum())
    missing_flags = int(missingness["missingness_flag"].sum())
    perf_rows = pd.DataFrame(
        [
            {"window": "reference", **reference_perf},
            {"window": "current", **current_perf},
        ]
    )
    pred_rows = pd.DataFrame([pred_drift])

    return "\n".join(
        [
            "# Monitoring Summary",
            "",
            "This monitoring run simulates production by splitting the processed feature table "
            "into a reference window and a current window. The final saved model scores both "
            "windows, and all monitoring values are computed from actual features, labels, and predictions.",
            "",
            "## Implementation Path",
            "",
            f"- Evidently status: {evidently_status}",
            "- A lightweight custom fallback report was generated to avoid version-specific "
            "Evidently API issues and to keep the report reproducible in this local environment.",
            "",
            "## Window Sizes",
            "",
            f"- Reference rows: `{len(reference):,}`",
            f"- Current rows: `{len(current):,}`",
            "",
            "## Key Checks",
            "",
            f"- Features with PSI >= {PSI_ALERT_THRESHOLD}: `{drifted_count}`",
            f"- Features with missingness-rate change >= {MISSINGNESS_ALERT_THRESHOLD:.0%}: `{missing_flags}`",
            f"- Prediction PSI: `{pred_drift['prediction_psi']:.6f}`",
            f"- Reference default rate: `{reference['TARGET'].mean():.4f}`",
            f"- Current default rate: `{current['TARGET'].mean():.4f}`",
            "",
            "## Prediction Drift",
            "",
            markdown_table(pred_rows),
            "",
            "## Model Performance by Window",
            "",
            markdown_table(perf_rows),
            "",
            "## Top Feature Drift Signals",
            "",
            markdown_table(drift.head(20)),
            "",
            "## Missingness Drift",
            "",
            markdown_table(missingness.head(20)),
            "",
            "## Production Interpretation",
            "",
            "In production, the reference window would be a stable training or recent-good "
            "period, and the current window would be the latest batch of scored applicants. "
            "Drift alerts should trigger data-quality review, score-distribution review, and "
            "possibly model recalibration or retraining analysis. This report is descriptive "
            "monitoring and does not retrain the model.",
            "",
        ]
    )


def run_monitoring(sample_size: int | None = None) -> dict[str, Any]:
    """Generate monitoring artifacts."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    model_bundle = load_model_bundle()
    feature_columns = model_bundle["feature_columns"]
    data = load_feature_data(feature_columns, sample_size=sample_size)
    reference, current = split_reference_current(data)
    reference = add_predictions(reference, model_bundle)
    current = add_predictions(current, model_bundle)

    drift = numeric_drift_table(reference, current, feature_columns)
    missingness = missingness_table(reference, current, feature_columns)
    pred_drift = prediction_drift(reference, current)
    reference_perf = performance_metrics(reference, threshold=model_bundle["threshold"])
    current_perf = performance_metrics(current, threshold=model_bundle["threshold"])
    evidently_status = (
        f"available ({evidently.__version__}) but custom fallback used"
        if evidently is not None
        else "not installed; custom fallback used"
    )

    SUMMARY_PATH.write_text(
        build_summary(
            reference=reference,
            current=current,
            drift=drift,
            missingness=missingness,
            pred_drift=pred_drift,
            reference_perf=reference_perf,
            current_perf=current_perf,
            evidently_status=evidently_status,
        ),
        encoding="utf-8",
    )

    perf_df = pd.DataFrame(
        [
            {"window": "reference", **reference_perf},
            {"window": "current", **current_perf},
        ]
    )
    pred_df = pd.DataFrame([pred_drift])
    write_html_report(
        MONITORING_REPORT_PATH,
        "FinSight Model Monitoring Report",
        [
            (
                "Run Context",
                "<div class='note'>Reference and current windows are deterministic halves of "
                "data/processed/model_features.parquet. No model retraining is performed.</div>",
            ),
            ("Prediction Drift", html_table(pred_df)),
            ("Model Performance by Window", html_table(perf_df)),
            ("Missingness Drift", html_table(missingness, max_rows=50)),
        ],
    )
    write_html_report(
        DRIFT_REPORT_PATH,
        "FinSight Data Drift Report",
        [
            (
                "Drift Method",
                f"<div class='note'>Numeric feature drift uses Population Stability Index (PSI). "
                f"Features with PSI >= {PSI_ALERT_THRESHOLD} are flagged.</div>",
            ),
            ("Top Feature Drift Signals", html_table(drift, max_rows=76)),
            ("Prediction Drift", html_table(pred_df)),
        ],
    )

    return {
        "reference_rows": len(reference),
        "current_rows": len(current),
        "drifted_features": int(drift["drift_flag"].sum()),
        "missingness_flags": int(missingness["missingness_flag"].sum()),
        "prediction_psi": pred_drift["prediction_psi"],
        "reference_perf": reference_perf,
        "current_perf": current_perf,
        "evidently_status": evidently_status,
    }


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    result = run_monitoring(sample_size=args.sample_size)
    print("Monitoring reports generated.")
    print(f"Monitoring report saved to: {MONITORING_REPORT_PATH}")
    print(f"Drift report saved to: {DRIFT_REPORT_PATH}")
    print(f"Summary saved to: {SUMMARY_PATH}")
    print(
        "Key checks: "
        f"drifted_features={result['drifted_features']}, "
        f"missingness_flags={result['missingness_flags']}, "
        f"prediction_psi={result['prediction_psi']:.6f}"
    )
    print(
        "Current performance: "
        f"ROC-AUC={result['current_perf']['roc_auc']:.4f}, "
        f"PR-AUC={result['current_perf']['pr_auc']:.4f}, "
        f"Recall@Top-10%={result['current_perf']['recall_at_top_10pct']:.4f}, "
        f"KS={result['current_perf']['ks_statistic']:.4f}"
    )


if __name__ == "__main__":
    main()
