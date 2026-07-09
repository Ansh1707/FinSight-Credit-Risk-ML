"""Build dashboard-ready CSV outputs from generated project artifacts.

Run from the project root:
    python dashboard/build_dashboard_data.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.business.collections_scoring import band_summary, load_model_bundle


DASHBOARD_DATA_DIR = Path("dashboard/dashboard_data")
COLLECTIONS_PATH = Path("reports/collections_priority_sample.csv")
FINAL_METRICS_PATH = Path("reports/final_model_metrics.json")
EXPLAINABILITY_PATH = Path("reports/explainability_summary.md")
MONITORING_SUMMARY_PATH = Path("reports/monitoring_summary.md")


def parse_markdown_table(lines: list[str], start_marker: str) -> pd.DataFrame:
    """Parse the first markdown table after a section heading."""
    start_index = next(i for i, line in enumerate(lines) if line.strip() == start_marker)
    table_lines = []
    for line in lines[start_index + 1 :]:
        if line.startswith("|"):
            table_lines.append(line)
        elif table_lines:
            break

    if len(table_lines) < 3:
        return pd.DataFrame()

    headers = [value.strip() for value in table_lines[0].strip("|").split("|")]
    rows = []
    for line in table_lines[2:]:
        rows.append([value.strip() for value in line.strip("|").split("|")])
    return pd.DataFrame(rows, columns=headers)


def build_kpi_summary(scored: pd.DataFrame, metrics: dict) -> pd.DataFrame:
    """Create top-level dashboard KPIs."""
    test_metrics = metrics["splits"]["test"]["classification"]
    monitoring = parse_monitoring_key_values()
    return pd.DataFrame(
        [
            {"metric": "Total applicants analyzed", "value": len(scored)},
            {
                "metric": "Average default probability",
                "value": round(scored["default_probability"].mean(), 6),
            },
            {
                "metric": "Critical risk applicants",
                "value": int((scored["risk_band"] == "Critical Risk").sum()),
            },
            {"metric": "Test ROC-AUC", "value": round(test_metrics["roc_auc"], 6)},
            {"metric": "Test PR-AUC", "value": round(test_metrics["pr_auc"], 6)},
            {
                "metric": "Test Recall@Top-10%",
                "value": round(test_metrics["recall_at_top_10pct"], 6),
            },
            {"metric": "Prediction PSI", "value": monitoring.get("Prediction PSI", "")},
            {
                "metric": "Feature drift flags",
                "value": monitoring.get("Features with PSI >= 0.2", ""),
            },
        ]
    )


def parse_monitoring_key_values() -> dict[str, str]:
    """Extract key monitoring checks from the markdown summary."""
    if not MONITORING_SUMMARY_PATH.exists():
        return {}

    values: dict[str, str] = {}
    for line in MONITORING_SUMMARY_PATH.read_text(encoding="utf-8").splitlines():
        clean = line.strip("- ").replace("`", "")
        if ": " not in clean:
            continue
        key, value = clean.split(": ", 1)
        values[key] = value
    return values


def build_model_metrics(metrics: dict) -> pd.DataFrame:
    """Flatten validation/test metric summary."""
    rows = []
    for split_name, split_payload in metrics["splits"].items():
        row = {"split": split_name}
        row.update(split_payload["classification"])
        row["brier_score"] = split_payload["calibration"]["brier_score"]
        rows.append(row)
    return pd.DataFrame(rows)


def build_dashboard_data() -> dict[str, Path]:
    """Generate dashboard-ready CSV files."""
    DASHBOARD_DATA_DIR.mkdir(parents=True, exist_ok=True)

    scored, collections_sample = load_full_collections_output()
    metrics = json.loads(FINAL_METRICS_PATH.read_text(encoding="utf-8"))
    explainability_lines = EXPLAINABILITY_PATH.read_text(encoding="utf-8").splitlines()

    outputs = {
        "kpi_summary": DASHBOARD_DATA_DIR / "kpi_summary.csv",
        "risk_band_distribution": DASHBOARD_DATA_DIR / "risk_band_distribution.csv",
        "collections_priority": DASHBOARD_DATA_DIR / "collections_priority.csv",
        "model_performance": DASHBOARD_DATA_DIR / "model_performance.csv",
        "top_model_features": DASHBOARD_DATA_DIR / "top_model_features.csv",
        "high_risk_segments": DASHBOARD_DATA_DIR / "high_risk_segments.csv",
        "monitoring_summary": DASHBOARD_DATA_DIR / "monitoring_summary.csv",
    }

    build_kpi_summary(scored, metrics).to_csv(outputs["kpi_summary"], index=False)
    band_summary(scored).to_csv(outputs["risk_band_distribution"], index=False)
    collections_sample.to_csv(outputs["collections_priority"], index=False)
    build_model_metrics(metrics).to_csv(outputs["model_performance"], index=False)

    top_features = parse_markdown_table(explainability_lines, "## Top Global Risk Drivers")
    top_features.to_csv(outputs["top_model_features"], index=False)

    build_high_risk_segments(scored).to_csv(outputs["high_risk_segments"], index=False)
    pd.DataFrame(
        [
            {"check": key, "value": value}
            for key, value in parse_monitoring_key_values().items()
        ]
    ).to_csv(outputs["monitoring_summary"], index=False)

    return outputs


def load_full_collections_output() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Recreate full scored portfolio and load saved sample output."""
    from src.business.collections_scoring import create_collections_scores, load_features

    model_bundle = load_model_bundle()
    data = load_features(model_bundle["feature_columns"])
    scored = create_collections_scores(data, model_bundle)
    collections_sample = pd.read_csv(COLLECTIONS_PATH)
    return scored, collections_sample


def build_high_risk_segments(scored: pd.DataFrame) -> pd.DataFrame:
    """Create simple high-risk segment summary for dashboard slicing."""
    segments = scored.copy()
    segments["credit_amount_bucket"] = pd.cut(
        segments["credit_amount"],
        bins=[0, 250000, 500000, 750000, 1000000, float("inf")],
        labels=["<250k", "250k-500k", "500k-750k", "750k-1M", "1M+"],
        include_lowest=True,
    )
    return (
        segments.groupby(["risk_band", "credit_amount_bucket"], observed=True)
        .agg(
            applicant_count=("SK_ID_CURR", "count"),
            avg_default_probability=("default_probability", "mean"),
            avg_priority_score=("collections_priority_score", "mean"),
            max_priority_score=("collections_priority_score", "max"),
        )
        .reset_index()
        .sort_values(["avg_priority_score", "applicant_count"], ascending=False)
    )


def main() -> None:
    """CLI entry point."""
    outputs = build_dashboard_data()
    print("Dashboard-ready data created.")
    for name, path in outputs.items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
