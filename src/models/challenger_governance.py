"""Train and document a less-sensitive challenger model governance workflow.

Run from the project root:
    python src/models/challenger_governance.py

The challenger removes features flagged as restricted or enhanced-review proxy
features, trains on the same split strategy as the champion model, and compares
actual computed metrics. It does not change the saved champion model.
"""

from __future__ import annotations

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
from lightgbm import LGBMClassifier
from sklearn.metrics import brier_score_loss

try:
    from src.business.business_impact import evaluate_review_capacity
    from src.models.calibrate_model import expected_calibration_error
    from src.models.metrics import evaluate_binary_classifier
    from src.models.train_final_model import (
        RANDOM_STATE,
        TOP_K,
        class_imbalance_ratio,
        split_data,
        top_k_threshold,
    )
except ModuleNotFoundError:  # Allows direct script execution from project root.
    from business.business_impact import evaluate_review_capacity
    from calibrate_model import expected_calibration_error
    from metrics import evaluate_binary_classifier
    from train_final_model import (
        RANDOM_STATE,
        TOP_K,
        class_imbalance_ratio,
        split_data,
        top_k_threshold,
    )


FEATURE_PATH = Path("data/processed/model_features.parquet")
CHAMPION_MODEL_PATH = Path("models/credit_risk_model.pkl")
PROXY_CONTROLS_PATH = Path("reports/proxy_feature_controls.csv")
MODELS_DIR = Path("models")
COMPARISON_PATH = REPORTS_DIR / "challenger_model_comparison.csv"
REPORT_PATH = REPORTS_DIR / "challenger_governance_report.md"
JSON_PATH = REPORTS_DIR / "challenger_governance.json"
CHALLENGER_MODEL_PATH = MODELS_DIR / "less_sensitive_challenger_model.pkl"

REVIEW_RATES = [0.05, 0.10, 0.15, 0.20]
REMOVED_CONTROL_DECISIONS = {
    "restricted_pending_fair_lending_approval",
    "restricted_pending_policy_approval",
    "fair_lending_review_required",
    "enhanced_review_required",
}


def load_inputs() -> tuple[pd.DataFrame, pd.Series, dict[str, Any], pd.DataFrame]:
    """Load processed data, champion model bundle, and proxy feature controls."""
    if not FEATURE_PATH.exists():
        raise FileNotFoundError(
            "Missing data/processed/model_features.parquet. "
            "Run python src/features/pyspark_feature_engineering.py first."
        )
    if not CHAMPION_MODEL_PATH.exists():
        raise FileNotFoundError(
            "Missing models/credit_risk_model.pkl. "
            "Run python src/models/train_final_model.py first."
        )
    if not PROXY_CONTROLS_PATH.exists():
        raise FileNotFoundError(
            "Missing reports/proxy_feature_controls.csv. "
            "Run python src/models/fair_lending_governance.py first."
        )

    data = pd.read_parquet(FEATURE_PATH).replace([np.inf, -np.inf], np.nan).fillna(0)
    if "TARGET" not in data.columns:
        raise ValueError("TARGET column was not found in processed features.")
    y = data["TARGET"].astype(int)
    X = data.drop(columns=["TARGET", "SK_ID_CURR"], errors="ignore")
    champion_bundle = joblib.load(CHAMPION_MODEL_PATH)
    controls = pd.read_csv(PROXY_CONTROLS_PATH)
    return X, y, champion_bundle, controls


def select_challenger_features(
    champion_features: list[str], controls: pd.DataFrame
) -> tuple[list[str], pd.DataFrame]:
    """Remove high-governance-risk features from the champion feature set."""
    controlled = controls[controls["feature_name"].isin(champion_features)].copy()
    removed = controlled[
        controlled["control_decision"].isin(REMOVED_CONTROL_DECISIONS)
    ].copy()
    removed_features = set(removed["feature_name"].tolist())
    challenger_features = [
        feature for feature in champion_features if feature not in removed_features
    ]
    if not challenger_features:
        raise ValueError("No challenger features remain after proxy-risk filtering.")
    return challenger_features, removed.sort_values(["control_decision", "feature_name"])


def challenger_params(champion_bundle: dict[str, Any], y_train: pd.Series) -> dict[str, Any]:
    """Reuse champion LightGBM parameters with refreshed class-imbalance handling."""
    params = dict(champion_bundle.get("model_params") or {})
    if not params and "model" in champion_bundle:
        params = champion_bundle["model"].get_params()
    params.update(
        {
            "objective": "binary",
            "scale_pos_weight": class_imbalance_ratio(y_train),
            "random_state": RANDOM_STATE,
            "n_jobs": -1,
            "verbose": -1,
        }
    )
    return params


def score_frame(
    X_split: pd.DataFrame,
    y_split: pd.Series,
    scores: np.ndarray,
    credit_amount: pd.Series,
) -> pd.DataFrame:
    """Build a scored frame for business-impact calculations."""
    return pd.DataFrame(
        {
            "TARGET": y_split.astype(int).to_numpy(),
            "default_probability": scores,
            "credit_amount": credit_amount.astype(float).to_numpy(),
            "expected_risk_exposure": scores * credit_amount.astype(float).to_numpy(),
        }
    ).sort_values("default_probability", ascending=False)


def evaluate_model(
    model_name: str,
    feature_count: int,
    y_valid: pd.Series,
    y_test: pd.Series,
    valid_scores: np.ndarray,
    test_scores: np.ndarray,
    X_test: pd.DataFrame,
) -> dict[str, Any]:
    """Evaluate classification, calibration, and business impact."""
    threshold = top_k_threshold(valid_scores, top_k=TOP_K)
    test_metrics = evaluate_binary_classifier(
        y_test.to_numpy(), test_scores, threshold=threshold, top_k=TOP_K
    )
    impact = evaluate_review_capacity(
        score_frame(
            X_split=X_test,
            y_split=y_test,
            scores=test_scores,
            credit_amount=X_test["AMT_CREDIT"],
        ),
        review_rates=REVIEW_RATES,
    )
    top_10 = impact.loc[np.isclose(impact["review_rate"], 0.10)].iloc[0]
    return {
        "model_name": model_name,
        "feature_count": feature_count,
        "validation_top_10pct_threshold": threshold,
        "test_roc_auc": test_metrics["roc_auc"],
        "test_pr_auc": test_metrics["pr_auc"],
        "test_precision": test_metrics["precision"],
        "test_recall": test_metrics["recall"],
        "test_f1_score": test_metrics["f1_score"],
        "test_recall_at_top_10pct": test_metrics["recall_at_top_10pct"],
        "test_ks_statistic": test_metrics["ks_statistic"],
        "test_brier_score": brier_score_loss(y_test, test_scores),
        "test_expected_calibration_error": expected_calibration_error(
            y_test, test_scores
        ),
        "top_10pct_applicants_reviewed": int(top_10["applicants_reviewed"]),
        "top_10pct_defaults_captured": int(top_10["defaults_captured"]),
        "top_10pct_default_capture_rate": float(top_10["default_capture_rate"]),
        "top_10pct_lift_vs_random": float(top_10["lift_vs_random_default_capture"]),
        "top_10pct_default_credit_exposure_capture_rate": float(
            top_10["default_credit_exposure_capture_rate"]
        ),
    }


def build_comparison(
    champion: dict[str, Any], challenger: dict[str, Any]
) -> pd.DataFrame:
    """Create champion/challenger comparison with challenger deltas."""
    comparison = pd.DataFrame([champion, challenger])
    metrics_for_delta = [
        "feature_count",
        "test_roc_auc",
        "test_pr_auc",
        "test_recall_at_top_10pct",
        "test_ks_statistic",
        "test_brier_score",
        "test_expected_calibration_error",
        "top_10pct_default_capture_rate",
        "top_10pct_lift_vs_random",
    ]
    champion_row = comparison[comparison["model_name"] == "champion_full_feature_model"].iloc[0]
    for metric in metrics_for_delta:
        comparison[f"delta_vs_champion_{metric}"] = (
            comparison[metric] - champion_row[metric]
        )
    return comparison


def summarize_removed_features(removed_features: pd.DataFrame) -> pd.DataFrame:
    """Summarize removed features by governance control decision."""
    if removed_features.empty:
        return pd.DataFrame(
            columns=["control_decision", "sensitivity_class", "removed_feature_count"]
        )
    return (
        removed_features.groupby(["control_decision", "sensitivity_class"])
        .size()
        .reset_index(name="removed_feature_count")
        .sort_values(["control_decision", "sensitivity_class"])
    )


def markdown_table(df: pd.DataFrame) -> str:
    """Render a DataFrame as markdown."""
    if df.empty:
        return "_No rows to display._"
    table = df.copy()
    for column in table.columns:
        if pd.api.types.is_numeric_dtype(table[column]):
            table[column] = table[column].round(4)
    table = table.replace([np.inf, -np.inf], np.nan).fillna("").astype(str)
    rows = ["| " + " | ".join(table.columns) + " |"]
    rows.append("| " + " | ".join("---" for _ in table.columns) + " |")
    rows.extend("| " + " | ".join(row) + " |" for row in table.itertuples(index=False, name=None))
    return "\n".join(rows)


def build_report(
    comparison: pd.DataFrame,
    removed_features: pd.DataFrame,
    removed_summary: pd.DataFrame,
) -> str:
    """Build business-readable challenger governance report."""
    champion = comparison[comparison["model_name"] == "champion_full_feature_model"].iloc[0]
    challenger = comparison[
        comparison["model_name"] == "less_sensitive_challenger_model"
    ].iloc[0]
    compact_columns = [
        "model_name",
        "feature_count",
        "test_pr_auc",
        "test_recall_at_top_10pct",
        "test_ks_statistic",
        "test_brier_score",
        "test_expected_calibration_error",
        "top_10pct_default_capture_rate",
        "top_10pct_lift_vs_random",
    ]
    removed_columns = [
        "feature_name",
        "sensitivity_class",
        "control_decision",
        "rationale",
    ]

    return "\n".join(
        [
            "# Challenger Model Governance Report",
            "",
            "This report compares the saved champion credit-risk model with a "
            "less-sensitive challenger model. The challenger removes features flagged "
            "as restricted or requiring enhanced fair-lending/proxy-risk review, then "
            "uses the same train/validation/test split strategy and actual computed "
            "metrics.",
            "",
            "The workflow does not change the champion model, does not invent metrics, "
            "does not create labels, and does not claim legal fair-lending certification.",
            "",
            "## Challenger Design",
            "",
            "- Champion: saved full-feature LightGBM model from `models/credit_risk_model.pkl`.",
            "- Challenger: LightGBM trained with protected/high-proxy and enhanced-review features removed.",
            "- Removed controls: `restricted_pending_fair_lending_approval`, `restricted_pending_policy_approval`, `fair_lending_review_required`, and `enhanced_review_required`.",
            f"- Champion feature count: `{int(champion['feature_count'])}`",
            f"- Challenger feature count: `{int(challenger['feature_count'])}`",
            f"- Removed feature count: `{len(removed_features)}`",
            "",
            "## Performance And Business Comparison",
            "",
            markdown_table(comparison[compact_columns]),
            "",
            "## Delta Interpretation",
            "",
            f"- PR-AUC change vs champion: `{challenger['delta_vs_champion_test_pr_auc']:.4f}`.",
            f"- Recall@Top-10% change vs champion: `{challenger['delta_vs_champion_test_recall_at_top_10pct']:.4f}`.",
            f"- KS change vs champion: `{challenger['delta_vs_champion_test_ks_statistic']:.4f}`.",
            f"- Top-10% default-capture change vs champion: `{challenger['delta_vs_champion_top_10pct_default_capture_rate']:.4f}`.",
            f"- Brier-score change vs champion: `{challenger['delta_vs_champion_test_brier_score']:.4f}`.",
            "",
            "A lower-sensitive challenger is valuable when it materially reduces "
            "fair-lending/proxy-risk exposure with acceptable loss in ranking and "
            "business impact. A champion model remains preferable only if its predictive "
            "lift is large enough to justify stronger governance controls, challenger "
            "evidence, and formal approval.",
            "",
            "## Removed Feature Controls",
            "",
            markdown_table(removed_summary),
            "",
            "## Removed Feature Detail",
            "",
            markdown_table(removed_features[removed_columns]),
            "",
            "## Governance Recommendation",
            "",
            "Use this comparison as a model-risk discussion artifact. A production "
            "credit-risk team should review the challenger alongside the champion, "
            "less-sensitive challenger variants, calibration, reject-inference limits, "
            "business review capacity, adverse-action constraints, and compliance input "
            "before approving any automated policy use.",
            "",
            "## Saved Outputs",
            "",
            f"- `{COMPARISON_PATH.as_posix()}`",
            f"- `{REPORT_PATH.as_posix()}`",
            f"- `{JSON_PATH.as_posix()}`",
            f"- `{CHALLENGER_MODEL_PATH.as_posix()}` (ignored by Git)",
            "",
        ]
    )


def run() -> dict[str, Any]:
    """Train challenger, compare with champion, and save governance artifacts."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    X, y, champion_bundle, controls = load_inputs()
    champion_features = list(champion_bundle["feature_columns"])
    challenger_features, removed_features = select_challenger_features(
        champion_features, controls
    )
    X_train, X_valid, X_test, y_train, y_valid, y_test = split_data(X, y)

    champion_model = champion_bundle["model"]
    champion_valid_scores = champion_model.predict_proba(X_valid[champion_features])[:, 1]
    champion_test_scores = champion_model.predict_proba(X_test[champion_features])[:, 1]
    champion_metrics = evaluate_model(
        model_name="champion_full_feature_model",
        feature_count=len(champion_features),
        y_valid=y_valid,
        y_test=y_test,
        valid_scores=champion_valid_scores,
        test_scores=champion_test_scores,
        X_test=X_test,
    )

    challenger_model = LGBMClassifier(
        **challenger_params(champion_bundle, y_train)
    )
    challenger_model.fit(X_train[challenger_features], y_train)
    challenger_valid_scores = challenger_model.predict_proba(
        X_valid[challenger_features]
    )[:, 1]
    challenger_test_scores = challenger_model.predict_proba(
        X_test[challenger_features]
    )[:, 1]
    challenger_metrics = evaluate_model(
        model_name="less_sensitive_challenger_model",
        feature_count=len(challenger_features),
        y_valid=y_valid,
        y_test=y_test,
        valid_scores=challenger_valid_scores,
        test_scores=challenger_test_scores,
        X_test=X_test,
    )

    comparison = build_comparison(champion_metrics, challenger_metrics)
    removed_summary = summarize_removed_features(removed_features)
    payload = {
        "analysis_type": "challenger_model_governance",
        "models_retrained": True,
        "champion_model_modified": False,
        "labels_created": False,
        "legal_certification_claimed": False,
        "removed_control_decisions": sorted(REMOVED_CONTROL_DECISIONS),
        "removed_features": removed_features["feature_name"].tolist(),
        "removed_feature_count": int(len(removed_features)),
        "champion_feature_count": int(len(champion_features)),
        "challenger_feature_count": int(len(challenger_features)),
        "comparison": comparison.to_dict(orient="records"),
        "removed_feature_summary": removed_summary.to_dict(orient="records"),
    }

    comparison.to_csv(COMPARISON_PATH, index=False)
    JSON_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    REPORT_PATH.write_text(
        build_report(comparison, removed_features, removed_summary),
        encoding="utf-8",
    )
    joblib.dump(
        {
            "model": challenger_model,
            "feature_columns": challenger_features,
            "removed_features": removed_features.to_dict(orient="records"),
            "model_params": challenger_model.get_params(),
            "random_state": RANDOM_STATE,
            "top_k": TOP_K,
            "governance_note": (
                "Less-sensitive challenger trained for governance comparison; "
                "not approved for production use."
            ),
        },
        CHALLENGER_MODEL_PATH,
    )
    return payload


def main() -> None:
    """CLI entry point."""
    payload = run()
    challenger = next(
        row
        for row in payload["comparison"]
        if row["model_name"] == "less_sensitive_challenger_model"
    )
    print("Challenger model governance workflow complete.")
    print(f"Champion model modified: {payload['champion_model_modified']}")
    print(f"Removed features: {payload['removed_feature_count']}")
    print(f"Challenger feature count: {payload['challenger_feature_count']}")
    print(f"Challenger PR-AUC: {challenger['test_pr_auc']:.4f}")
    print(
        "Challenger Recall@Top-10%: "
        f"{challenger['test_recall_at_top_10pct']:.4f}"
    )
    print(f"Comparison saved to: {COMPARISON_PATH}")
    print(f"Report saved to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
