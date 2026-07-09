"""Compare probability calibration methods for the final credit-risk model.

Run from the project root:
    python src/models/calibrate_model.py
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Callable

REPORTS_DIR = Path("reports")
FIGURES_DIR = REPORTS_DIR / "figures"
MPL_CACHE_DIR = REPORTS_DIR / ".matplotlib-cache"
MPL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE_DIR))

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss
from sklearn.model_selection import train_test_split

try:
    from src.models.metrics import evaluate_binary_classifier
except ModuleNotFoundError:  # Allows direct script execution from project root.
    from metrics import evaluate_binary_classifier


FEATURE_PATH = Path("data/processed/model_features.parquet")
MODEL_PATH = Path("models/credit_risk_model.pkl")
COMPARISON_PATH = REPORTS_DIR / "calibration_comparison.csv"
REPORT_PATH = REPORTS_DIR / "calibration_report.md"
FIGURE_PATH = FIGURES_DIR / "calibration_comparison.png"
RANDOM_STATE = 42
TOP_K = 0.10


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Compare calibration methods for the final model."
    )
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
    """Create the same stratified 60/20/20 split used by final model training."""
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


def load_model_bundle() -> dict:
    """Load the saved final model bundle."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Missing models/credit_risk_model.pkl. "
            "Run python src/models/train_final_model.py first."
        )
    return joblib.load(MODEL_PATH)


def top_k_threshold(scores: np.ndarray, top_k: float = TOP_K) -> float:
    """Return threshold that flags the top-k highest-scored applicants."""
    return float(np.quantile(scores, 1 - top_k))


def expected_calibration_error(
    y_true: pd.Series | np.ndarray,
    scores: np.ndarray,
    n_bins: int = 10,
) -> float:
    """Compute equal-width expected calibration error."""
    y_array = np.asarray(y_true)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    total = len(scores)
    ece = 0.0
    for lower, upper in zip(bins[:-1], bins[1:]):
        if upper == 1.0:
            mask = (scores >= lower) & (scores <= upper)
        else:
            mask = (scores >= lower) & (scores < upper)
        if not np.any(mask):
            continue
        bin_weight = mask.mean()
        observed = y_array[mask].mean()
        predicted = scores[mask].mean()
        ece += bin_weight * abs(observed - predicted)
    return float(ece)


def fit_calibrators(
    y_valid: pd.Series, valid_scores: np.ndarray
) -> dict[str, Callable[[np.ndarray], np.ndarray]]:
    """Fit validation-based calibration transforms."""
    platt = LogisticRegression(solver="lbfgs", random_state=RANDOM_STATE)
    platt.fit(valid_scores.reshape(-1, 1), y_valid)

    isotonic = IsotonicRegression(out_of_bounds="clip")
    isotonic.fit(valid_scores, y_valid)

    return {
        "uncalibrated": lambda scores: scores,
        "platt_sigmoid": lambda scores: platt.predict_proba(scores.reshape(-1, 1))[:, 1],
        "isotonic": lambda scores: isotonic.predict(scores),
    }


def evaluate_calibration_methods(
    y_valid: pd.Series,
    y_test: pd.Series,
    valid_raw_scores: np.ndarray,
    test_raw_scores: np.ndarray,
) -> pd.DataFrame:
    """Evaluate raw, sigmoid-calibrated, and isotonic-calibrated probabilities."""
    calibrators = fit_calibrators(y_valid, valid_raw_scores)
    rows = []

    for method, transform in calibrators.items():
        valid_scores = np.clip(transform(valid_raw_scores), 0.0, 1.0)
        test_scores = np.clip(transform(test_raw_scores), 0.0, 1.0)
        threshold = top_k_threshold(valid_scores, top_k=TOP_K)

        for split, y_split, scores in [
            ("validation", y_valid, valid_scores),
            ("test", y_test, test_scores),
        ]:
            metrics = evaluate_binary_classifier(
                y_split.to_numpy(),
                scores,
                threshold=threshold,
                top_k=TOP_K,
            )
            rows.append(
                {
                    "method": method,
                    "split": split,
                    "brier_score": brier_score_loss(y_split, scores),
                    "expected_calibration_error": expected_calibration_error(
                        y_split, scores
                    ),
                    "validation_top_10pct_threshold": threshold,
                    **metrics,
                }
            )

    return pd.DataFrame(rows)


def calibration_table(
    y_true: pd.Series | np.ndarray,
    scores: np.ndarray,
    method: str,
    n_bins: int = 10,
) -> pd.DataFrame:
    """Build calibration bins for plotting."""
    frame = pd.DataFrame({"target": np.asarray(y_true), "score": scores})
    frame["bin"] = pd.qcut(frame["score"], q=n_bins, duplicates="drop")
    table = (
        frame.groupby("bin", observed=True)
        .agg(
            mean_predicted_probability=("score", "mean"),
            observed_default_rate=("target", "mean"),
            applicant_count=("target", "count"),
        )
        .reset_index(drop=True)
    )
    table["method"] = method
    return table


def plot_calibration_comparison(
    y_test: pd.Series,
    test_raw_scores: np.ndarray,
    calibrators: dict[str, Callable[[np.ndarray], np.ndarray]],
) -> Path:
    """Save a calibration comparison plot on the test split."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Perfect calibration")

    for method, transform in calibrators.items():
        scores = np.clip(transform(test_raw_scores), 0.0, 1.0)
        table = calibration_table(y_test, scores, method=method)
        ax.plot(
            table["mean_predicted_probability"],
            table["observed_default_rate"],
            marker="o",
            label=method,
        )

    ax.set_title("Calibration Comparison on Test Split")
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Observed default rate")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURE_PATH, dpi=160)
    plt.close(fig)
    return FIGURE_PATH


def markdown_table(df: pd.DataFrame) -> str:
    """Render a DataFrame as markdown without optional dependencies."""
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


def build_report(
    comparison: pd.DataFrame,
    rows_loaded: int,
    feature_count: int,
    sample_size: int | None,
) -> str:
    """Build calibration markdown report."""
    validation = comparison[comparison["split"] == "validation"].copy()
    test = comparison[comparison["split"] == "test"].copy()
    best_test = test.sort_values("brier_score", ascending=True).iloc[0]
    compact_columns = [
        "method",
        "split",
        "brier_score",
        "expected_calibration_error",
        "roc_auc",
        "pr_auc",
        "recall_at_top_10pct",
        "ks_statistic",
    ]

    return "\n".join(
        [
            "# Calibration Report",
            "",
            "This report compares probability calibration methods for the saved final "
            "LightGBM model. Calibrators are fit on the validation split and evaluated "
            "on both validation and test splits. The ranking model is not retrained.",
            "",
            "## Scope",
            "",
            f"- Rows used: `{rows_loaded:,}`",
            f"- Feature columns: `{feature_count:,}`",
            "- Split strategy: same stratified 60% train, 20% validation, 20% test split as final modeling",
            f"- Sample size: `{sample_size:,}`" if sample_size else "- Sample size: full processed dataset",
            "",
            "## Methods Compared",
            "",
            "- `uncalibrated`: raw saved LightGBM probabilities.",
            "- `platt_sigmoid`: logistic calibration fit on validation probabilities.",
            "- `isotonic`: non-parametric isotonic calibration fit on validation probabilities.",
            "",
            "## Metric Comparison",
            "",
            markdown_table(comparison[compact_columns]),
            "",
            "## Validation-Only View",
            "",
            markdown_table(validation[compact_columns]),
            "",
            "## Test Recommendation",
            "",
            f"The lowest test Brier score is from `{best_test['method']}` "
            f"with Brier score `{best_test['brier_score']:.4f}` and expected "
            f"calibration error `{best_test['expected_calibration_error']:.4f}`.",
            "",
            "Ranking metrics should still be reviewed alongside calibration. For collections "
            "prioritization, ROC-AUC, PR-AUC, Recall@Top-10%, and KS remain important; for "
            "policy thresholds or customer-facing probabilities, calibrated probabilities "
            "are more appropriate than raw class-weighted model scores.",
            "",
            "## Saved Outputs",
            "",
            f"- `{COMPARISON_PATH.as_posix()}`",
            f"- `{REPORT_PATH.as_posix()}`",
            f"- `{FIGURE_PATH.as_posix()}`",
            "",
        ]
    )


def run(sample_size: int | None = None) -> pd.DataFrame:
    """Run calibration comparison and save outputs."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    X, y = load_features(sample_size=sample_size)
    _, X_valid, X_test, _, y_valid, y_test = split_data(X, y)
    bundle = load_model_bundle()
    feature_columns = bundle["feature_columns"]
    missing_columns = [column for column in feature_columns if column not in X.columns]
    if missing_columns:
        raise ValueError(
            "Processed feature data is missing required model columns: "
            + ", ".join(missing_columns[:20])
        )

    model = bundle["model"]
    valid_raw_scores = model.predict_proba(X_valid[feature_columns])[:, 1]
    test_raw_scores = model.predict_proba(X_test[feature_columns])[:, 1]
    calibrators = fit_calibrators(y_valid, valid_raw_scores)
    comparison = evaluate_calibration_methods(
        y_valid=y_valid,
        y_test=y_test,
        valid_raw_scores=valid_raw_scores,
        test_raw_scores=test_raw_scores,
    )
    comparison.to_csv(COMPARISON_PATH, index=False)
    plot_calibration_comparison(y_test, test_raw_scores, calibrators)
    REPORT_PATH.write_text(
        build_report(
            comparison=comparison,
            rows_loaded=len(X),
            feature_count=len(feature_columns),
            sample_size=sample_size,
        ),
        encoding="utf-8",
    )
    return comparison


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    comparison = run(sample_size=args.sample_size)
    print("Calibration comparison complete.")
    print(f"Comparison saved to: {COMPARISON_PATH}")
    print(f"Report saved to: {REPORT_PATH}")
    print(f"Figure saved to: {FIGURE_PATH}")
    print("\nCalibration comparison:")
    print(
        comparison[
            [
                "method",
                "split",
                "brier_score",
                "expected_calibration_error",
                "roc_auc",
                "pr_auc",
                "recall_at_top_10pct",
                "ks_statistic",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()

