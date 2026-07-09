import numpy as np
import pandas as pd
import pytest

from src.models import predict


class DummyProbabilityModel:
    def predict_proba(self, frame: pd.DataFrame) -> np.ndarray:
        probabilities = np.linspace(0.2, 0.8, len(frame))
        return np.column_stack([1 - probabilities, probabilities])


def test_risk_band_mapping() -> None:
    assert predict.risk_band(0.10) == "low"
    assert predict.risk_band(0.25) == "medium"
    assert predict.risk_band(0.50) == "high"


def test_score_applicants_returns_expected_columns() -> None:
    data = pd.DataFrame(
        {
            "SK_ID_CURR": [1001, 1002],
            "feature_a": [1.0, 2.0],
            "feature_b": [3.0, 4.0],
        }
    )
    bundle = {
        "feature_columns": ["feature_a", "feature_b"],
        "threshold": 0.5,
        "model": DummyProbabilityModel(),
    }

    output = predict.score_applicants(data, bundle)

    assert output["SK_ID_CURR"].tolist() == [1001, 1002]
    assert output["default_probability"].tolist() == pytest.approx([0.2, 0.8])
    assert output["risk_band"].tolist() == ["low", "high"]
    assert output["above_operational_threshold"].tolist() == [False, True]


def test_score_applicants_rejects_missing_model_features() -> None:
    data = pd.DataFrame({"feature_a": [1.0]})
    bundle = {
        "feature_columns": ["feature_a", "feature_b"],
        "threshold": 0.5,
        "model": DummyProbabilityModel(),
    }

    with pytest.raises(ValueError, match="missing required feature columns"):
        predict.score_applicants(data, bundle)

