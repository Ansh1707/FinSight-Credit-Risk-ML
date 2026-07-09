"""Run stratified cross-validation for the final LightGBM credit-risk model.

Run from the project root:
    python src/models/cross_validate_model.py
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from time import perf_counter
from typing import Any

REPORTS_DIR = Path("reports")
MPL_CACHE_DIR = REPORTS_DIR / ".matplotlib-cache"
MPL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE_DIR))

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.model_selection import StratifiedKFold, train_test_split

try:
    from src.models.metrics import evaluate_binary_classifier
except ModuleNotFoundError:  # Allows direct script execution from project root.
    from metrics import evaluate_binary_classifier


FEATURE_PATH = Path("data/processed/model_features.parquet")
FINAL_METRICS_PATH = REPORTS_DIR / "final_model_metrics.json"
CV_RESULTS_PATH = REPORTS_DIR / "cross_validation_results.csv"
CV_SUMMARY_PATH = REPORTS_DIR / "cross_validation_summary.md"
RANDOM_STATE = 42
TOP_K = 0.10


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Run stratified K-fold validation for the final model."
    )
    parser.add_argument("--folds", type=int, default=5, help="Number of CV folds.")
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Optional stratified sample size for quick smoke tests.",
    )
    return parser.parse_args()


def load_features(sample_size: int | None = None) -> tuple[pd.DataFrame, pd.Series]:
    """Load processed model features and target."""
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


def class_imbalance_ratio(y_train: pd.Series) -> float:
    """Return negative-to-positive ratio for class-imbalance handling."""
    positive_count = int((y_train == 1).sum())
    negative_count = int((y_train == 0).sum())
    if positive_count == 0:
        raise ValueError("Training fold has no positive class examples.")
    return negative_count / positive_count


def load_final_model_params(scale_pos_weight: float) -> dict[str, Any]:
    """Load final LightGBM parameters and refresh fold-specific class weight."""
    if FINAL_METRICS_PATH.exists():
        metrics = json.loads(FINAL_METRICS_PATH.read_text(encoding="utf-8"))
        params = dict(metrics.get("best_params", {}))
    else:
        params = {
            "objective": "binary",
            "n_estimators": 600,
            "learning_rate": 0.02,
            "num_leaves": 63,
            "min_child_samples": 120,
            "subsample": 0.85,
            "colsample_bytree": 0.8,
            "reg_alpha": 0.2,
            "reg_lambda": 4.0,
            "random_state": RANDOM_STATE,
            "n_jobs": -1,
            "verbose": -1,
        }

    params["scale_pos_weight"] = scale_pos_weight
    params["random_state"] = RANDOM_STATE
    params["n_jobs"] = -1
    params["verbose"] = -1
    return params


def top_k_threshold(scores: np.ndarray, top_k: float = TOP_K) -> float:
    """Return threshold that flags the top-k highest-scored applicants."""
    return float(np.quantile(scores, 1 - top_k))


def run_cross_validation(
    X: pd.DataFrame, y: pd.Series, folds: int = 5
) -> pd.DataFrame:
    """Run stratified K-fold validation with the final LightGBM configuration."""
    if folds < 2:
        raise ValueError("folds must be at least 2.")

    splitter = StratifiedKFold(
        n_splits=folds, shuffle=True, random_state=RANDOM_STATE
    )
    rows: list[dict[str, Any]] = []

    for fold, (train_idx, valid_idx) in enumerate(splitter.split(X, y), start=1):
        X_train = X.iloc[train_idx]
        X_valid = X.iloc[valid_idx]
        y_train = y.iloc[train_idx]
        y_valid = y.iloc[valid_idx]

        params = load_final_model_params(class_imbalance_ratio(y_train))
        model = LGBMClassifier(**params)
        started = perf_counter()
        model.fit(X_train, y_train)
        train_seconds = round(perf_counter() - started, 2)

        valid_scores = model.predict_proba(X_valid)[:, 1]
        threshold = top_k_threshold(valid_scores, top_k=TOP_K)
        metrics = evaluate_binary_classifier(
            y_valid.to_numpy(),
            valid_scores,
            threshold=threshold,
            top_k=TOP_K,
        )
        rows.append(
            {
                "fold": fold,
                "train_rows": len(X_train),
                "validation_rows": len(X_valid),
                "train_default_rate": round(float(y_train.mean()), 6),
                "validation_default_rate": round(float(y_valid.mean()), 6),
                "scale_pos_weight": params["scale_pos_weight"],
                "top_10pct_threshold": threshold,
                "train_seconds": train_seconds,
                **metrics,
            }
        )

    return pd.DataFrame(rows)


def summarize_cv_results(results: pd.DataFrame) -> pd.DataFrame:
    """Create mean/std summary for key validation metrics."""
    metrics = [
        "roc_auc",
        "pr_auc",
        "precision",
        "recall",
        "f1_score",
        "recall_at_top_10pct",
        "ks_statistic",
    ]
    rows = []
    for metric in metrics:
        rows.append(
            {
                "metric": metric,
                "mean": results[metric].mean(),
                "std": results[metric].std(ddof=1),
                "min": results[metric].min(),
                "max": results[metric].max(),
            }
        )
    return pd.DataFrame(rows)


def markdown_table(df: pd.DataFrame) -> str:
    """Render a DataFrame as a markdown table without optional dependencies."""
    if df.empty:
        return "_No rows to display._"
    safe_df = df.copy()
    for column in safe_df.select_dtypes(include=[np.number]).columns:
        safe_df[column] = safe_df[column].round(4)
    safe_df = safe_df.fillna("").astype(str)
    rows = ["| " + " | ".join(safe_df.columns) + " |"]
    rows.append("| " + " | ".join("---" for _ in safe_df.columns) + " |")
    rows.extend(
        "| " + " | ".join(row) + " |"
        for row in safe_df.itertuples(index=False, name=None)
    )
    return "\n".join(rows)


def build_summary_report(
    results: pd.DataFrame,
    summary: pd.DataFrame,
    rows_loaded: int,
    feature_count: int,
    sample_size: int | None,
) -> str:
    """Build the cross-validation markdown summary."""
    compact_fold_columns = [
        "fold",
        "validation_rows",
        "validation_default_rate",
        "roc_auc",
        "pr_auc",
        "precision",
        "recall_at_top_10pct",
        "ks_statistic",
        "top_10pct_threshold",
        "train_seconds",
    ]

    return "\n".join(
        [
            "# Cross-Validation Summary",
            "",
            "This report evaluates the final tuned LightGBM configuration with "
            "stratified K-fold validation. It is a stability check around the "
            "selected champion model, not a new model-selection exercise.",
            "",
            "## Scope",
            "",
            f"- Rows used: `{rows_loaded:,}`",
            f"- Feature columns: `{feature_count:,}`",
            f"- Folds: `{results['fold'].nunique()}`",
            f"- Top-K policy: top `{int(TOP_K * 100)}%` of validation scores per fold",
            f"- Sample size: `{sample_size:,}`" if sample_size else "- Sample size: full processed dataset",
            "",
            "## Stability Summary",
            "",
            markdown_table(summary),
            "",
            "## Fold-Level Results",
            "",
            markdown_table(results[compact_fold_columns]),
            "",
            "## Business Interpretation",
            "",
            "Cross-validation checks whether the selected LightGBM model is stable "
            "across different stratified slices of the applicant population. For a "
            "credit-risk ranking workflow, PR-AUC, Recall@Top-10%, and KS stability "
            "matter more than accuracy because the default class is rare and the "
            "business action is prioritizing the riskiest applicants for review.",
            "",
            "## Saved Outputs",
            "",
            f"- `{CV_RESULTS_PATH.as_posix()}`",
            f"- `{CV_SUMMARY_PATH.as_posix()}`",
            "",
        ]
    )


def run(sample_size: int | None = None, folds: int = 5) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run cross-validation and save outputs."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    X, y = load_features(sample_size=sample_size)
    results = run_cross_validation(X, y, folds=folds)
    summary = summarize_cv_results(results)
    results.to_csv(CV_RESULTS_PATH, index=False)
    CV_SUMMARY_PATH.write_text(
        build_summary_report(
            results=results,
            summary=summary,
            rows_loaded=len(X),
            feature_count=X.shape[1],
            sample_size=sample_size,
        ),
        encoding="utf-8",
    )
    return results, summary


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    results, summary = run(sample_size=args.sample_size, folds=args.folds)
    print("Cross-validation complete.")
    print(f"Results saved to: {CV_RESULTS_PATH}")
    print(f"Summary saved to: {CV_SUMMARY_PATH}")
    print("\nStability summary:")
    print(summary.to_string(index=False))
    print("\nFold-level metrics:")
    print(
        results[
            [
                "fold",
                "roc_auc",
                "pr_auc",
                "recall_at_top_10pct",
                "ks_statistic",
                "train_seconds",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()

