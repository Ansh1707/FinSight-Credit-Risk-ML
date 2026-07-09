import pandas as pd
import pytest

from src.models import challenger_governance


def test_select_challenger_features_removes_restricted_controls() -> None:
    champion_features = [
        "CODE_GENDER_idx",
        "DAYS_BIRTH",
        "EXT_SOURCE_1",
        "credit_to_income_ratio",
    ]
    controls = pd.DataFrame(
        [
            {
                "feature_name": "CODE_GENDER_idx",
                "control_decision": "restricted_pending_fair_lending_approval",
                "sensitivity_class": "protected_or_high_proxy",
            },
            {
                "feature_name": "DAYS_BIRTH",
                "control_decision": "restricted_pending_policy_approval",
                "sensitivity_class": "protected_or_policy_sensitive",
            },
            {
                "feature_name": "EXT_SOURCE_1",
                "control_decision": "vendor_governance_required",
                "sensitivity_class": "third_party_score",
            },
            {
                "feature_name": "credit_to_income_ratio",
                "control_decision": "allowed_with_monitoring",
                "sensitivity_class": "credit_capacity_with_proxy_risk",
            },
        ]
    )

    challenger_features, removed = challenger_governance.select_challenger_features(
        champion_features, controls
    )

    assert challenger_features == ["EXT_SOURCE_1", "credit_to_income_ratio"]
    assert set(removed["feature_name"]) == {"CODE_GENDER_idx", "DAYS_BIRTH"}


def test_build_comparison_adds_challenger_deltas() -> None:
    champion = {
        "model_name": "champion_full_feature_model",
        "feature_count": 10,
        "test_roc_auc": 0.8,
        "test_pr_auc": 0.3,
        "test_precision": 0.2,
        "test_recall": 0.4,
        "test_f1_score": 0.27,
        "test_recall_at_top_10pct": 0.35,
        "test_ks_statistic": 0.45,
        "test_brier_score": 0.1,
        "test_expected_calibration_error": 0.02,
        "validation_top_10pct_threshold": 0.7,
        "top_10pct_applicants_reviewed": 100,
        "top_10pct_defaults_captured": 35,
        "top_10pct_default_capture_rate": 0.35,
        "top_10pct_lift_vs_random": 3.5,
        "top_10pct_default_credit_exposure_capture_rate": 0.36,
    }
    challenger = {
        **champion,
        "model_name": "less_sensitive_challenger_model",
        "feature_count": 7,
        "test_pr_auc": 0.28,
        "test_recall_at_top_10pct": 0.32,
        "top_10pct_default_capture_rate": 0.32,
    }

    comparison = challenger_governance.build_comparison(champion, challenger)
    challenger_row = comparison[
        comparison["model_name"] == "less_sensitive_challenger_model"
    ].iloc[0]

    assert challenger_row["delta_vs_champion_feature_count"] == -3
    assert challenger_row["delta_vs_champion_test_pr_auc"] == pytest.approx(-0.02)
    assert challenger_row[
        "delta_vs_champion_top_10pct_default_capture_rate"
    ] == pytest.approx(-0.03)
