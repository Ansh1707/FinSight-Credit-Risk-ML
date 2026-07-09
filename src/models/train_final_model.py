"""Tune, validate, and save the final credit-risk model.

Run from the project root:
    python src/models/train_final_model.py
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from time import perf_counter
from typing import Any

REPORTS_DIR = Path("reports")
FIGURES_DIR = REPORTS_DIR / "figures"
MPL_CACHE_DIR = REPORTS_DIR / ".matplotlib-cache"
MPL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE_DIR))

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    precision_recall_curve,
    roc_curve,
)
from sklearn.model_selection import train_test_split

try:
    from src.models.metrics import evaluate_binary_classifier
except ModuleNotFoundError:  # Allows direct script execution from project root.
    from metrics import evaluate_binary_classifier


FEATURE_PATH = Path("data/processed/model_features.parquet")
MODEL_PATH = Path("models/credit_risk_model.pkl")
METRICS_PATH = REPORTS_DIR / "final_model_metrics.json"
REPORT_PATH = REPORTS_DIR / "final_model_report.md"
RANDOM_STATE = 42
TOP_K = 0.10


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Train and validate final model.")
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Optional stratified sample size for quick smoke tests.",
    )
    return parser.parse_args()


def load_features(sample_size: int | None = None) -> tuple[pd.DataFrame, pd.Series]:
    """Load processed features."""
    if not FEATURE_PATH.exists():
        raise FileNotFoundError(
            "Missing data/processed/model_features.parquet. "
            "Run python src/features/pyspark_feature_engineering.py first."
        )

    data = pd.read_parquet(FEATURE_PATH)
    if "TARGET" not in data.columns:
        raise ValueError("TARGET column was not found in model_features.parquet.")

    data = data.replace([np.inf, -np.inf], np.nan).fillna(0)
    if sample_size and sample_size < len(data):
        _, data = train_test_split(
            data,
            test_size=sample_size,
            stratify=data["TARGET"],
            random_state=RANDOM_STATE,
        )

    y = data["TARGET"].astype(int)
    X = data.drop(columns=["TARGET", "SK_ID_CURR"], errors="ignore")
    return X, y


def split_data(
    X: pd.DataFrame, y: pd.Series
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """Create stratified train, validation, and test splits."""
    X_train, X_temp, y_train, y_temp = train_test_split(
        X,
        y,
        test_size=0.40,
        stratify=y,
        random_state=RANDOM_STATE,
    )
    X_valid, X_test, y_valid, y_test = train_test_split(
        X_temp,
        y_temp,
        test_size=0.50,
        stratify=y_temp,
        random_state=RANDOM_STATE,
    )
    return X_train, X_valid, X_test, y_train, y_valid, y_test


def class_imbalance_ratio(y_train: pd.Series) -> float:
    """Return negative-to-positive ratio for class-imbalance handling."""
    positive_count = int((y_train == 1).sum())
    negative_count = int((y_train == 0).sum())
    if positive_count == 0:
        raise ValueError("Training split has no positive examples.")
    return negative_count / positive_count


def candidate_params(scale_pos_weight: float) -> list[dict[str, Any]]:
    """Return a compact LightGBM tuning grid."""
    base = {
        "objective": "binary",
        "scale_pos_weight": scale_pos_weight,
        "random_state": RANDOM_STATE,
        "n_jobs": -1,
        "verbose": -1,
    }
    grid = [
        {
            "n_estimators": 350,
            "learning_rate": 0.035,
            "num_leaves": 31,
            "min_child_samples": 60,
            "subsample": 0.85,
            "colsample_bytree": 0.85,
            "reg_alpha": 0.0,
            "reg_lambda": 1.0,
        },
        {
            "n_estimators": 500,
            "learning_rate": 0.025,
            "num_leaves": 31,
            "min_child_samples": 80,
            "subsample": 0.9,
            "colsample_bytree": 0.9,
            "reg_alpha": 0.1,
            "reg_lambda": 2.0,
        },
        {
            "n_estimators": 450,
            "learning_rate": 0.03,
            "num_leaves": 45,
            "min_child_samples": 100,
            "subsample": 0.8,
            "colsample_bytree": 0.85,
            "reg_alpha": 0.1,
            "reg_lambda": 3.0,
        },
        {
            "n_estimators": 600,
            "learning_rate": 0.02,
            "num_leaves": 63,
            "min_child_samples": 120,
            "subsample": 0.85,
            "colsample_bytree": 0.8,
            "reg_alpha": 0.2,
            "reg_lambda": 4.0,
        },
    ]
    return [{**base, **params} for params in grid]


def tune_lightgbm(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_valid: pd.DataFrame,
    y_valid: pd.Series,
) -> tuple[LGBMClassifier, pd.DataFrame]:
    """Train candidate LightGBM models and choose by validation PR-AUC."""
    rows = []
    best_model: LGBMClassifier | None = None
    best_pr_auc = -np.inf

    for idx, params in enumerate(candidate_params(class_imbalance_ratio(y_train)), start=1):
        started = perf_counter()
        model = LGBMClassifier(**params)
        model.fit(X_train, y_train)
        valid_scores = model.predict_proba(X_valid)[:, 1]
        pr_auc = average_precision_score(y_valid, valid_scores)
        train_seconds = round(perf_counter() - started, 2)
        rows.append(
            {
                "candidate": idx,
                "validation_pr_auc": pr_auc,
                "train_seconds": train_seconds,
                **params,
            }
        )
        if pr_auc > best_pr_auc:
            best_pr_auc = pr_auc
            best_model = model

    if best_model is None:
        raise RuntimeError("No LightGBM model was trained.")

    tuning_results = pd.DataFrame(rows).sort_values(
        "validation_pr_auc", ascending=False
    )
    return best_model, tuning_results


def top_k_threshold(scores: np.ndarray, top_k: float = TOP_K) -> float:
    """Return the score threshold that flags the top-k highest-risk applicants."""
    return float(np.quantile(scores, 1 - top_k))


def calibration_metrics(y_true: pd.Series, scores: np.ndarray) -> dict[str, Any]:
    """Compute calibration table and Brier score."""
    fraction_positive, mean_predicted = calibration_curve(
        y_true, scores, n_bins=10, strategy="quantile"
    )
    table = [
        {
            "mean_predicted_probability": float(predicted),
            "observed_default_rate": float(observed),
        }
        for predicted, observed in zip(mean_predicted, fraction_positive)
    ]
    return {
        "brier_score": float(brier_score_loss(y_true, scores)),
        "calibration_table": table,
    }


def plot_roc_curve(y_true: pd.Series, scores: np.ndarray) -> Path:
    """Save ROC curve plot."""
    output_path = FIGURES_DIR / "final_model_roc_curve.png"
    fpr, tpr, _ = roc_curve(y_true, scores)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(fpr, tpr, label="Final LightGBM")
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Random")
    ax.set_title("Final Model ROC Curve")
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path


def plot_pr_curve(y_true: pd.Series, scores: np.ndarray) -> Path:
    """Save precision-recall curve plot."""
    output_path = FIGURES_DIR / "final_model_precision_recall_curve.png"
    precision, recall, _ = precision_recall_curve(y_true, scores)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(recall, precision, label="Final LightGBM")
    ax.axhline(y_true.mean(), linestyle="--", color="gray", label="Default rate")
    ax.set_title("Final Model Precision-Recall Curve")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path


def plot_calibration_curve(y_true: pd.Series, scores: np.ndarray) -> Path:
    """Save calibration curve plot."""
    output_path = FIGURES_DIR / "final_model_calibration_curve.png"
    fraction_positive, mean_predicted = calibration_curve(
        y_true, scores, n_bins=10, strategy="quantile"
    )
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(mean_predicted, fraction_positive, marker="o", label="Final LightGBM")
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Perfect calibration")
    ax.set_title("Final Model Calibration Curve")
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Observed default rate")
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
    rows = ["| " + " | ".join(safe_df.columns) + " |"]
    rows.append("| " + " | ".join("---" for _ in safe_df.columns) + " |")
    rows.extend(
        "| " + " | ".join(row) + " |"
        for row in safe_df.itertuples(index=False, name=None)
    )
    return "\n".join(rows)


def build_report(
    metrics: dict[str, Any],
    tuning_results: pd.DataFrame,
    feature_columns: list[str],
    figure_paths: list[Path],
    sample_size: int | None,
) -> str:
    """Build business-readable final model report."""
    summary_rows = []
    for split in ["validation", "test"]:
        row = {"split": split}
        row.update(metrics["splits"][split]["classification"])
        row["brier_score"] = metrics["splits"][split]["calibration"]["brier_score"]
        summary_rows.append(row)

    summary_df = pd.DataFrame(summary_rows)
    display_columns = [
        "split",
        "roc_auc",
        "pr_auc",
        "precision",
        "recall",
        "f1_score",
        "recall_at_top_10pct",
        "ks_statistic",
        "brier_score",
        "tn",
        "fp",
        "fn",
        "tp",
    ]
    rounded = summary_df[display_columns].copy()
    rounded[
        [
            "roc_auc",
            "pr_auc",
            "precision",
            "recall",
            "f1_score",
            "recall_at_top_10pct",
            "ks_statistic",
            "brier_score",
        ]
    ] = rounded[
        [
            "roc_auc",
            "pr_auc",
            "precision",
            "recall",
            "f1_score",
            "recall_at_top_10pct",
            "ks_statistic",
            "brier_score",
        ]
    ].round(4)

    tuning_display = tuning_results.head(4).copy()
    tuning_display["validation_pr_auc"] = tuning_display["validation_pr_auc"].round(4)

    mode_note = (
        f"Stratified sample mode used with `{sample_size:,}` rows."
        if sample_size
        else "Full processed feature dataset used."
    )

    return "\n".join(
        [
            "# Final Model Report",
            "",
            "The final credit-risk model is a tuned LightGBM classifier trained on "
            "`data/processed/model_features.parquet`.",
            "",
            "## Why LightGBM Was Chosen",
            "",
            "LightGBM was selected because it was the strongest baseline by validation "
            "PR-AUC, which is more appropriate than accuracy for rare-default credit "
            "risk ranking. The final phase tuned important tree and regularization "
            "hyperparameters and retained the model with the best validation PR-AUC.",
            "",
            "## Scope",
            "",
            f"- {mode_note}",
            f"- Feature columns: `{len(feature_columns):,}`",
            "- Split strategy: stratified 60% train, 20% validation, 20% test.",
            "- Class imbalance handling: `scale_pos_weight` from the training split.",
            f"- Operational threshold: validation top `{int(TOP_K * 100)}%` risk cutoff "
            f"at score `{metrics['threshold']:.6f}`.",
            "- Model selection metric: validation PR-AUC.",
            "",
            "## Final Validation and Test Metrics",
            "",
            markdown_table(rounded),
            "",
            "## Hyperparameter Tuning Results",
            "",
            markdown_table(tuning_display),
            "",
            "## Calibration Analysis",
            "",
            f"- Validation Brier score: `{metrics['splits']['validation']['calibration']['brier_score']:.4f}`",
            f"- Test Brier score: `{metrics['splits']['test']['calibration']['brier_score']:.4f}`",
            "- The calibration curve should be reviewed before using raw probabilities as "
            "customer-facing or policy thresholds. Ranking metrics are stronger than "
            "probability calibration at this stage.",
            "",
            "## Business Interpretation",
            "",
            "The model is suitable as a portfolio risk-ranking baseline: it identifies a "
            "top-risk applicant slice that captures a materially larger share of defaults "
            "than random selection. For lending or collections use, the score should feed "
            "review queues, monitoring, and explainability workflows rather than act as an "
            "automatic approval or rejection rule.",
            "",
            "## Saved Artifacts",
            "",
            f"- `{MODEL_PATH.as_posix()}`",
            f"- `{METRICS_PATH.as_posix()}`",
            f"- `{REPORT_PATH.as_posix()}`",
            *[f"- `{path.as_posix()}`" for path in figure_paths],
            "",
        ]
    )


def run_final_training(sample_size: int | None = None) -> dict[str, Any]:
    """Train, tune, evaluate, and save final model artifacts."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    X, y = load_features(sample_size=sample_size)
    X_train, X_valid, X_test, y_train, y_valid, y_test = split_data(X, y)
    model, tuning_results = tune_lightgbm(X_train, y_train, X_valid, y_valid)

    valid_scores = model.predict_proba(X_valid)[:, 1]
    test_scores = model.predict_proba(X_test)[:, 1]
    threshold = top_k_threshold(valid_scores, TOP_K)

    metrics = {
        "model_type": "lightgbm",
        "selection_metric": "validation_pr_auc",
        "threshold_strategy": "validation_top_10_percent_score_cutoff",
        "threshold": threshold,
        "top_k": TOP_K,
        "random_state": RANDOM_STATE,
        "rows_loaded": int(len(X)),
        "feature_count": int(X.shape[1]),
        "best_params": model.get_params(),
        "splits": {
            "validation": {
                "classification": evaluate_binary_classifier(
                    y_valid.to_numpy(),
                    valid_scores,
                    threshold=threshold,
                    top_k=TOP_K,
                ),
                "calibration": calibration_metrics(y_valid, valid_scores),
            },
            "test": {
                "classification": evaluate_binary_classifier(
                    y_test.to_numpy(),
                    test_scores,
                    threshold=threshold,
                    top_k=TOP_K,
                ),
                "calibration": calibration_metrics(y_test, test_scores),
            },
        },
    }

    figure_paths = [
        plot_roc_curve(y_test, test_scores),
        plot_pr_curve(y_test, test_scores),
        plot_calibration_curve(y_test, test_scores),
    ]

    model_bundle = {
        "model": model,
        "feature_columns": X.columns.tolist(),
        "threshold": threshold,
        "top_k": TOP_K,
        "model_type": "lightgbm",
        "metrics": metrics,
    }
    joblib.dump(model_bundle, MODEL_PATH)

    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    REPORT_PATH.write_text(
        build_report(
            metrics=metrics,
            tuning_results=tuning_results,
            feature_columns=X.columns.tolist(),
            figure_paths=figure_paths,
            sample_size=sample_size,
        ),
        encoding="utf-8",
    )
    return metrics


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    metrics = run_final_training(sample_size=args.sample_size)
    valid = metrics["splits"]["validation"]["classification"]
    test = metrics["splits"]["test"]["classification"]

    print("Final model training complete.")
    print("Final model selected: lightgbm")
    print(f"Model saved to: {MODEL_PATH}")
    print(f"Metrics saved to: {METRICS_PATH}")
    print(f"Report saved to: {REPORT_PATH}")
    print(
        "Validation metrics: "
        f"PR-AUC={valid['pr_auc']:.4f}, ROC-AUC={valid['roc_auc']:.4f}, "
        f"Recall@Top-10%={valid['recall_at_top_10pct']:.4f}, KS={valid['ks_statistic']:.4f}"
    )
    print(
        "Test metrics: "
        f"PR-AUC={test['pr_auc']:.4f}, ROC-AUC={test['roc_auc']:.4f}, "
        f"Recall@Top-10%={test['recall_at_top_10pct']:.4f}, KS={test['ks_statistic']:.4f}"
    )


if __name__ == "__main__":
    main()
