import pandas as pd
import pytest
import numpy as np

from src.api import batch_score


def test_validate_schema_reports_missing_and_unknown_features() -> None:
    data = pd.DataFrame(
        {
            "SK_ID_CURR": [1],
            "feature_a": [0.2],
            "extra_column": [10],
        }
    )

    validation = batch_score.validate_schema(data, ["feature_a", "feature_b"])

    assert validation["schema_validation_status"] == "failed"
    assert validation["missing_features"] == ["feature_b"]
    assert validation["unknown_features"] == ["extra_column"]
    assert validation["duplicate_sk_id_curr_count"] == 0


def test_stable_hash_is_deterministic_and_masks_identifier() -> None:
    first = batch_score.stable_hash("100001")
    second = batch_score.stable_hash("100001")

    assert first == second
    assert first != "100001"
    assert len(first) == 16


def test_score_batch_outputs_privacy_safe_audit_columns() -> None:
    class DummyModel:
        def predict_proba(self, frame: pd.DataFrame):
            return np.array([[0.8, 0.2], [0.3, 0.7]])

    data = pd.DataFrame(
        {
            "SK_ID_CURR": [100001, 100002],
            "feature_a": [0.1, 0.5],
            "AMT_CREDIT": [100000.0, 200000.0],
            "external_score_mean": [0.3, 0.8],
        }
    )
    model_bundle = {
        "model": DummyModel(),
        "feature_columns": ["feature_a", "AMT_CREDIT", "external_score_mean"],
        "threshold": 0.5,
    }
    registry = {
        "model_name": "Test Model",
        "model_version": "test_v1",
        "model_stage": "unit_test",
    }

    predictions, audit, metadata = batch_score.score_batch(
        data,
        model_bundle,
        registry,
        batch_id="batch_test",
        score_timestamp_utc="2026-07-10T00:00:00+00:00",
    )

    assert metadata["schema_validation_status"] == "passed"
    assert "SK_ID_CURR" not in audit.columns
    assert "feature_a" not in audit.columns
    assert set(batch_score.AUDIT_COLUMNS) == set(audit.columns)
    assert predictions.loc[0, "applicant_hash"] != "100001"
    assert audit.loc[1, "model_version"] == "test_v1"
    assert audit.loc[1, "risk_band"] == "Critical Risk"
    assert audit.loc[0, "reason_code_1"] == "Low external credit score"


def test_fail_on_invalid_schema_raises_helpful_error() -> None:
    with pytest.raises(ValueError, match="missing required features"):
        batch_score.fail_on_invalid_schema(
            {
                "schema_validation_status": "failed",
                "missing_feature_count": 1,
                "missing_features": ["feature_b"],
                "non_numeric_feature_count": 0,
                "non_numeric_features": [],
            }
        )
