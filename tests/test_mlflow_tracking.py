from src.models import mlflow_tracking


def test_flatten_metrics_extracts_split_metrics() -> None:
    metrics = {
        "splits": {
            "validation": {
                "classification": {"roc_auc": 0.7, "tp": 12},
                "calibration": {"brier_score": 0.2},
            },
            "test": {
                "classification": {"pr_auc": 0.3},
                "calibration": {"brier_score": 0.25},
            },
        }
    }

    flattened = mlflow_tracking.flatten_metrics(metrics)

    assert flattened["validation_roc_auc"] == 0.7
    assert flattened["validation_tp"] == 12.0
    assert flattened["validation_brier_score"] == 0.2
    assert flattened["test_pr_auc"] == 0.3
    assert flattened["test_brier_score"] == 0.25


def test_registry_entry_documents_model_stage() -> None:
    metrics = {
        "model_type": "lightgbm",
        "selection_metric": "validation_pr_auc",
        "threshold": 0.7,
        "top_k": 0.1,
        "rows_loaded": 100,
        "feature_count": 12,
        "splits": {
            "validation": {"classification": {"roc_auc": 0.8}},
            "test": {"classification": {"roc_auc": 0.78}},
        },
    }
    mlflow_status = {"status": "skipped_by_user", "run_id": None}

    entry = mlflow_tracking.registry_entry(metrics, mlflow_status)

    assert entry["model_type"] == "lightgbm"
    assert entry["model_stage"] == "portfolio_ready_not_production_approved"
    assert entry["validation_metrics"]["roc_auc"] == 0.8
    assert entry["test_metrics"]["roc_auc"] == 0.78
    assert entry["mlflow"]["status"] == "skipped_by_user"
