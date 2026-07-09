import numpy as np
import pandas as pd
import pytest

from src.models import fairness_analysis


def test_age_and_income_bands_are_readable() -> None:
    age_bands = fairness_analysis.age_band_from_days(pd.Series([-3652, -14610, -25567]))
    income_bands = fairness_analysis.income_band(pd.Series([80_000, 175_000, 500_000]))

    assert age_bands.tolist() == ["18-25", "36-45", "65+"]
    assert income_bands.tolist() == ["<100k", "150k-200k", "300k+"]


def test_summarize_segments_computes_review_and_performance_metrics() -> None:
    scored = pd.DataFrame(
        {
            "TARGET": [1, 0, 1, 0, 0, 1],
            "default_probability": [0.9, 0.8, 0.7, 0.2, 0.1, 0.6],
            "gender_proxy": ["A", "A", "A", "B", "B", "B"],
            "global_top_10pct_review": [True, True, False, False, False, False],
        }
    )

    metrics = fairness_analysis.summarize_segments(
        scored,
        segment_columns=["gender_proxy"],
        min_segment_size=1,
    )

    segment_a = metrics[metrics["segment_value"] == "A"].iloc[0]
    assert segment_a["applicant_count"] == 3
    assert segment_a["observed_default_rate"] == 2 / 3
    assert segment_a["global_top10_review_rate"] == 2 / 3
    assert segment_a["default_capture_rate_within_segment"] == 0.5
    assert np.isfinite(segment_a["roc_auc"])


def test_summarize_disparities_returns_gap_rows() -> None:
    metrics = pd.DataFrame(
        {
            "segment_type": ["gender_proxy", "gender_proxy"],
            "segment_value": ["A", "B"],
            "observed_default_rate": [0.1, 0.2],
            "mean_default_probability": [0.3, 0.5],
            "global_top10_review_rate": [0.05, 0.15],
            "default_capture_rate_within_segment": [0.2, 0.4],
            "non_default_review_rate": [0.01, 0.03],
        }
    )

    disparities = fairness_analysis.summarize_disparities(metrics)

    row = disparities[
        (disparities["segment_type"] == "gender_proxy")
        & (disparities["metric"] == "global_top10_review_rate")
    ].iloc[0]
    assert row["absolute_gap"] == pytest.approx(0.10)
