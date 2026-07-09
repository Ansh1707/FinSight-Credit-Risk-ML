import math

import numpy as np
import pytest

from src.models.metrics import evaluate_binary_classifier, ks_statistic, recall_at_top_k


def test_recall_at_top_k_captures_highest_scored_defaults() -> None:
    y_true = np.array([1, 0, 1, 0, 1])
    y_score = np.array([0.95, 0.20, 0.70, 0.40, 0.10])

    assert recall_at_top_k(y_true, y_score, top_k=0.4) == pytest.approx(2 / 3)


def test_recall_at_top_k_validates_top_k_range() -> None:
    with pytest.raises(ValueError, match="top_k"):
        recall_at_top_k(np.array([0, 1]), np.array([0.1, 0.9]), top_k=0)


def test_ks_statistic_returns_zero_for_single_class_input() -> None:
    assert ks_statistic(np.array([1, 1, 1]), np.array([0.2, 0.4, 0.8])) == 0.0


def test_evaluate_binary_classifier_returns_expected_confusion_counts() -> None:
    y_true = np.array([0, 0, 1, 1])
    y_score = np.array([0.10, 0.40, 0.60, 0.90])

    metrics = evaluate_binary_classifier(y_true, y_score, threshold=0.5, top_k=0.5)

    assert metrics["tn"] == 2
    assert metrics["fp"] == 0
    assert metrics["fn"] == 0
    assert metrics["tp"] == 2
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["recall_at_top_50pct"] == 1.0
    assert math.isclose(metrics["roc_auc"], 1.0)
