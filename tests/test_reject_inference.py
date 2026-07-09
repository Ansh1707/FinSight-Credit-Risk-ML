from src.models import reject_inference


def test_reject_inference_payload_does_not_create_labels() -> None:
    payload = reject_inference.build_methodology_payload(
        {
            "rows_loaded": 100,
            "model_type": "lightgbm",
            "selection_metric": "validation_pr_auc",
            "feature_count": 12,
        }
    )

    assert payload["labels_created"] is False
    assert payload["models_retrained"] is False
    assert payload["raw_data_modified"] is False
    assert "Do not invent" in payload["portfolio_decision"]


def test_reject_inference_methods_are_documented_not_applied() -> None:
    payload = reject_inference.build_methodology_payload({})
    methods = {method["method"]: method for method in payload["production_methods"]}

    assert "Parceling" in methods
    assert "Fuzzy augmentation" in methods
    assert "Bureau or alternative outcome matching" in methods
    assert all("portfolio_status" in method for method in methods.values())
