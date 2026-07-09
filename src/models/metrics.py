"""Model validation metrics for credit default prediction."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def recall_at_top_k(y_true: np.ndarray, y_score: np.ndarray, top_k: float = 0.1) -> float:
    """Return share of defaults captured in the highest-scored top-k fraction."""
    if not 0 < top_k <= 1:
        raise ValueError("top_k must be in the interval (0, 1].")

    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    positives = y_true.sum()
    if positives == 0:
        return 0.0

    top_count = max(1, int(np.ceil(len(y_true) * top_k)))
    top_indices = np.argsort(y_score)[::-1][:top_count]
    return float(y_true[top_indices].sum() / positives)


def ks_statistic(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """Compute the Kolmogorov-Smirnov statistic for binary scores."""
    frame = pd.DataFrame({"target": y_true, "score": y_score}).sort_values(
        "score", ascending=False
    )
    positives = frame["target"].sum()
    negatives = len(frame) - positives
    if positives == 0 or negatives == 0:
        return 0.0

    cum_positive_rate = frame["target"].cumsum() / positives
    cum_negative_rate = (1 - frame["target"]).cumsum() / negatives
    return float((cum_positive_rate - cum_negative_rate).abs().max())


def evaluate_binary_classifier(
    y_true: np.ndarray,
    y_score: np.ndarray,
    threshold: float = 0.5,
    top_k: float = 0.1,
) -> dict[str, float | int]:
    """Evaluate ranking and threshold metrics for an imbalanced binary classifier."""
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    y_pred = (y_score >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    return {
        "roc_auc": float(roc_auc_score(y_true, y_score)),
        "pr_auc": float(average_precision_score(y_true, y_score)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_true, y_pred, zero_division=0)),
        f"recall_at_top_{int(top_k * 100)}pct": recall_at_top_k(
            y_true, y_score, top_k=top_k
        ),
        "ks_statistic": ks_statistic(y_true, y_score),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }
