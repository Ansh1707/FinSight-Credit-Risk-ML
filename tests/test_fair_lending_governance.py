import pandas as pd

from src.models import fair_lending_governance


def test_feature_controls_restrict_sensitive_and_proxy_features() -> None:
    registry = pd.DataFrame(
        [
            {
                "feature_name": "CODE_GENDER_idx",
                "feature_group": "encoded_application_categorical",
                "source_tables": "application_train.csv",
                "availability_time": "Known at application time.",
                "leakage_risk": "low_to_medium_proxy_risk",
            },
            {
                "feature_name": "age_years",
                "feature_group": "derived_application_risk",
                "source_tables": "application_train.csv",
                "availability_time": "Known at application time.",
                "leakage_risk": "low",
            },
            {
                "feature_name": "credit_to_income_ratio",
                "feature_group": "derived_application_risk",
                "source_tables": "application_train.csv",
                "availability_time": "Known at application time.",
                "leakage_risk": "low",
            },
            {
                "feature_name": "OWN_CAR_AGE",
                "feature_group": "base_application_numeric",
                "source_tables": "application_train.csv",
                "availability_time": "Known at application time.",
                "leakage_risk": "low",
            },
        ]
    )

    controls = fair_lending_governance.build_proxy_feature_controls(registry)
    decisions = dict(zip(controls["feature_name"], controls["control_decision"]))

    assert decisions["CODE_GENDER_idx"] == "restricted_pending_fair_lending_approval"
    assert decisions["age_years"] == "restricted_pending_policy_approval"
    assert decisions["credit_to_income_ratio"] == "allowed_with_monitoring"
    assert decisions["OWN_CAR_AGE"] == "allowed_with_monitoring"


def test_payload_does_not_claim_legal_certification_or_create_labels() -> None:
    fairness = pd.DataFrame(
        [
            {
                "segment_type": "gender_proxy",
                "segment_value": "A",
                "applicant_count": 100,
                "observed_default_rate": 0.1,
                "mean_default_probability": 0.2,
                "global_top10_review_rate": 0.15,
                "default_capture_rate_within_segment": 0.5,
                "non_default_review_rate": 0.1,
            },
            {
                "segment_type": "gender_proxy",
                "segment_value": "B",
                "applicant_count": 120,
                "observed_default_rate": 0.05,
                "mean_default_probability": 0.1,
                "global_top10_review_rate": 0.04,
                "default_capture_rate_within_segment": 0.2,
                "non_default_review_rate": 0.03,
            },
        ]
    )
    disparities = fair_lending_governance.build_segment_disparities(fairness)
    controls = pd.DataFrame(
        [
            {
                "feature_name": "CODE_GENDER_idx",
                "control_decision": "restricted_pending_fair_lending_approval",
                "sensitivity_class": "protected_or_high_proxy",
            }
        ]
    )

    payload = fair_lending_governance.build_payload(fairness, disparities, controls)

    assert payload["legal_certification_claimed"] is False
    assert payload["adverse_action_certification_claimed"] is False
    assert payload["labels_created"] is False
    assert payload["models_retrained"] is False
    assert payload["feature_count_reviewed"] == 1
