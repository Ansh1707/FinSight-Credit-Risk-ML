import numpy as np
import pandas as pd
import pytest

from src.business import collections_scoring


class DummyProbabilityModel:
    def __init__(self, probabilities: list[float]) -> None:
        self.probabilities = probabilities

    def predict_proba(self, frame: pd.DataFrame) -> np.ndarray:
        assert list(frame.columns) == ["feature_a", "feature_b"]
        return np.column_stack([1 - np.array(self.probabilities), self.probabilities])


def test_assign_risk_band_boundaries() -> None:
    assert collections_scoring.assign_risk_band(0.24) == "Low Risk"
    assert collections_scoring.assign_risk_band(0.25) == "Medium Risk"
    assert collections_scoring.assign_risk_band(0.50) == "High Risk"
    assert collections_scoring.assign_risk_band(0.70) == "Critical Risk"


def test_min_max_normalize_handles_constant_values() -> None:
    normalized = collections_scoring.min_max_normalize(pd.Series([5.0, 5.0, 5.0]))

    assert normalized.tolist() == [0.0, 0.0, 0.0]


def test_build_top_reason_codes_deduplicates_reason_text() -> None:
    reason_df = pd.DataFrame(
        {
            "SK_ID_CURR": [101],
            "reason_code_1": ["Low external credit score"],
            "reason_code_2": ["Low external credit score"],
            "reason_code_3": ["High annuity burden"],
        }
    )

    output = collections_scoring.build_top_reason_codes(reason_df)

    assert output.loc[0, "top_reason_codes"] == (
        "Low external credit score; High annuity burden"
    )


def test_create_collections_scores_ranks_by_priority(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        collections_scoring,
        "load_reason_codes",
        lambda: pd.DataFrame(columns=["SK_ID_CURR", "top_reason_codes"]),
    )
    data = pd.DataFrame(
        {
            "SK_ID_CURR": [1, 2, 3],
            "AMT_CREDIT": [100_000.0, 300_000.0, 500_000.0],
            "feature_a": [1.0, 2.0, 3.0],
            "feature_b": [4.0, 5.0, 6.0],
        }
    )
    bundle = {
        "feature_columns": ["feature_a", "feature_b"],
        "model": DummyProbabilityModel([0.20, 0.60, 0.80]),
    }

    scored = collections_scoring.create_collections_scores(data, bundle)

    assert scored.iloc[0]["SK_ID_CURR"] == 3
    assert scored.iloc[0]["risk_band"] == "Critical Risk"
    assert scored["collections_priority_score"].is_monotonic_decreasing
    assert scored["top_reason_codes"].str.contains("not available").all()


def test_band_summary_orders_business_risk_bands() -> None:
    scored = pd.DataFrame(
        {
            "SK_ID_CURR": [1, 2, 3, 4],
            "risk_band": ["Critical Risk", "Low Risk", "High Risk", "Medium Risk"],
            "default_probability": [0.8, 0.1, 0.6, 0.3],
            "credit_amount": [400.0, 100.0, 300.0, 200.0],
            "collections_priority_score": [80.0, 10.0, 60.0, 30.0],
        }
    )

    summary = collections_scoring.band_summary(scored)

    assert summary["risk_band"].tolist() == [
        "Low Risk",
        "Medium Risk",
        "High Risk",
        "Critical Risk",
    ]

