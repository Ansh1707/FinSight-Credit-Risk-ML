"""Train baseline credit default classifiers.

Run from the project root:
    python src/models/train_baseline.py
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

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

try:
    from xgboost import XGBClassifier
except ImportError:  # pragma: no cover - depends on local optional dependency
    XGBClassifier = None

try:
    from lightgbm import LGBMClassifier
except ImportError:  # pragma: no cover - depends on local optional dependency
    LGBMClassifier = None

try:
    from src.models.metrics import evaluate_binary_classifier
except ModuleNotFoundError:  # Allows direct script execution from project root.
    from metrics import evaluate_binary_classifier


FEATURE_PATH = Path("data/processed/model_features.parquet")
MODELS_DIR = Path("models")
COMPARISON_PATH = REPORTS_DIR / "model_comparison.csv"
SUMMARY_PATH = REPORTS_DIR / "baseline_modeling_summary.md"
RANDOM_STATE = 42
TOP_K = 0.10


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Train baseline credit-risk models.")
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Optional stratified sample size for quick local experiments.",
    )
    return parser.parse_args()


def load_features(sample_size: int | None = None) -> tuple[pd.DataFrame, pd.Series]:
    """Load processed model features and return X/y."""
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
    """Return negative-to-positive ratio for boosting libraries."""
    positive_count = int((y_train == 1).sum())
    negative_count = int((y_train == 0).sum())
    if positive_count == 0:
        raise ValueError("Training labels contain no positive class examples.")
    return negative_count / positive_count


def build_models(y_train: pd.Series) -> dict[str, Any]:
    """Build baseline classifiers with documented class imbalance handling."""
    scale_pos_weight = class_imbalance_ratio(y_train)
    models: dict[str, Any] = {
        "logistic_regression": Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        class_weight="balanced",
                        max_iter=1000,
                        solver="lbfgs",
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=160,
            max_depth=10,
            min_samples_leaf=80,
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=RANDOM_STATE,
        ),
    }

    if XGBClassifier is not None:
        models["xgboost"] = XGBClassifier(
            n_estimators=250,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.85,
            colsample_bytree=0.85,
            objective="binary:logistic",
            eval_metric="aucpr",
            scale_pos_weight=scale_pos_weight,
            tree_method="hist",
            n_jobs=-1,
            random_state=RANDOM_STATE,
        )

    if LGBMClassifier is not None:
        models["lightgbm"] = LGBMClassifier(
            n_estimators=300,
            max_depth=-1,
            num_leaves=31,
            learning_rate=0.04,
            subsample=0.85,
            colsample_bytree=0.85,
            scale_pos_weight=scale_pos_weight,
            random_state=RANDOM_STATE,
            n_jobs=-1,
            verbose=-1,
        )

    return models


def predict_scores(model: Any, X: pd.DataFrame) -> np.ndarray:
    """Return positive-class probabilities."""
    return model.predict_proba(X)[:, 1]


def train_and_evaluate(
    X_train: pd.DataFrame,
    X_valid: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_valid: pd.Series,
    y_test: pd.Series,
) -> pd.DataFrame:
    """Train models, save artifacts, and return validation/test metrics."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    models = build_models(y_train)
    rows: list[dict[str, Any]] = []

    for model_name, model in models.items():
        started = perf_counter()
        model.fit(X_train, y_train)
        train_seconds = round(perf_counter() - started, 2)
        joblib.dump(model, MODELS_DIR / f"{model_name}.joblib")

        for split_name, X_split, y_split in [
            ("validation", X_valid, y_valid),
            ("test", X_test, y_test),
        ]:
            scores = predict_scores(model, X_split)
            metrics = evaluate_binary_classifier(
                y_split.to_numpy(), scores, top_k=TOP_K
            )
            rows.append(
                {
                    "model": model_name,
                    "split": split_name,
                    "train_seconds": train_seconds,
                    **metrics,
                }
            )

    metadata = {
        "feature_columns": X_train.columns.tolist(),
        "target_column": "TARGET",
        "top_k": TOP_K,
        "random_state": RANDOM_STATE,
        "class_imbalance_approach": (
            "Logistic Regression and Random Forest use balanced class weights; "
            "XGBoost and LightGBM use scale_pos_weight from the training split."
        ),
    }
    (MODELS_DIR / "baseline_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    return pd.DataFrame(rows)


def markdown_table(df: pd.DataFrame) -> str:
    """Render a small DataFrame as markdown without optional dependencies."""
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


def build_summary_report(
    comparison: pd.DataFrame,
    X: pd.DataFrame,
    y: pd.Series,
    sample_size: int | None,
) -> str:
    """Create business-readable baseline modeling report."""
    validation = comparison[comparison["split"] == "validation"].copy()
    validation = validation.sort_values(["pr_auc", "roc_auc"], ascending=False)
    best = validation.iloc[0]

    display_columns = [
        "model",
        "split",
        "roc_auc",
        "pr_auc",
        "precision",
        "recall",
        "f1_score",
        "recall_at_top_10pct",
        "ks_statistic",
        "tn",
        "fp",
        "fn",
        "tp",
    ]
    rounded = comparison[display_columns].copy()
    metric_columns = [
        "roc_auc",
        "pr_auc",
        "precision",
        "recall",
        "f1_score",
        "recall_at_top_10pct",
        "ks_statistic",
    ]
    rounded[metric_columns] = rounded[metric_columns].round(4)

    default_rate = y.mean() * 100
    mode_note = (
        f"Stratified sample mode used with `{sample_size:,}` rows."
        if sample_size
        else "Full processed feature dataset used."
    )

    return "\n".join(
        [
            "# Baseline Modeling Summary",
            "",
            "This report contains actual computed baseline model results from "
            "`data/processed/model_features.parquet`.",
            "",
            "## Scope",
            "",
            f"- {mode_note}",
            f"- Rows loaded: `{len(X):,}`",
            f"- Feature columns: `{X.shape[1]:,}`",
            f"- Default rate: `{default_rate:.2f}%`",
            "- Split strategy: stratified 60% train, 20% validation, 20% test.",
            "- Imbalance handling: balanced class weights for Logistic Regression and "
            "Random Forest; `scale_pos_weight` for XGBoost and LightGBM.",
            "- Accuracy is intentionally not used as the primary metric.",
            "",
            "## Current Best Baseline",
            "",
            f"`{best['model']}` is the current best baseline by validation PR-AUC "
            f"(`{best['pr_auc']:.4f}`), with validation ROC-AUC `{best['roc_auc']:.4f}`, "
            f"Recall@Top-10% `{best['recall_at_top_10pct']:.4f}`, and KS "
            f"`{best['ks_statistic']:.4f}`.",
            "",
            "PR-AUC is used for model selection because the default class is rare and the "
            "business problem is closer to ranking risky applicants than maximizing overall "
            "classification accuracy.",
            "",
            "## Model Comparison",
            "",
            markdown_table(rounded.sort_values(["split", "pr_auc"], ascending=[True, False])),
            "",
            "## Saved Artifacts",
            "",
            "- `reports/model_comparison.csv`",
            "- `models/logistic_regression.joblib`",
            "- `models/random_forest.joblib`",
            "- `models/xgboost.joblib` if XGBoost is installed",
            "- `models/lightgbm.joblib` if LightGBM is installed",
            "- `models/baseline_metadata.json`",
            "",
        ]
    )


def run_training(sample_size: int | None = None) -> pd.DataFrame:
    """Run baseline training and save reports."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    X, y = load_features(sample_size=sample_size)
    X_train, X_valid, X_test, y_train, y_valid, y_test = split_data(X, y)

    comparison = train_and_evaluate(
        X_train=X_train,
        X_valid=X_valid,
        X_test=X_test,
        y_train=y_train,
        y_valid=y_valid,
        y_test=y_test,
    )
    comparison.to_csv(COMPARISON_PATH, index=False)
    SUMMARY_PATH.write_text(
        build_summary_report(
            comparison=comparison,
            X=X,
            y=y,
            sample_size=sample_size,
        ),
        encoding="utf-8",
    )
    return comparison


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    comparison = run_training(sample_size=args.sample_size)
    validation = comparison[comparison["split"] == "validation"].sort_values(
        ["pr_auc", "roc_auc"], ascending=False
    )
    best = validation.iloc[0]

    print("Baseline modeling complete.")
    print(f"Model comparison saved to: {COMPARISON_PATH}")
    print(f"Summary report saved to: {SUMMARY_PATH}")
    print("Models saved under: models/")
    print(
        "Best validation baseline: "
        f"{best['model']} | PR-AUC={best['pr_auc']:.4f} | "
        f"ROC-AUC={best['roc_auc']:.4f} | "
        f"Recall@Top-10%={best['recall_at_top_10pct']:.4f} | "
        f"KS={best['ks_statistic']:.4f}"
    )


if __name__ == "__main__":
    main()
