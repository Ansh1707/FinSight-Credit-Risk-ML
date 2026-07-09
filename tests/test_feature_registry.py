from src.features import feature_registry


def test_lineage_for_known_feature_groups() -> None:
    assert (
        feature_registry.lineage_for_feature("AMT_CREDIT").feature_group
        == "base_application_numeric"
    )
    assert (
        feature_registry.lineage_for_feature("credit_to_income_ratio").feature_group
        == "derived_application_features"
    )
    assert (
        feature_registry.lineage_for_feature("CODE_GENDER_idx").feature_group
        == "encoded_application_categorical"
    )
    assert (
        feature_registry.lineage_for_feature("bureau_credit_count").feature_group
        == "bureau_credit_history"
    )
    assert (
        feature_registry.lineage_for_feature("installment_late_payment_count").leakage_risk
        == "medium_high_timing_sensitive"
    )


def test_build_registry_contains_governance_columns() -> None:
    registry = feature_registry.build_registry(
        ["AMT_CREDIT", "credit_to_income_ratio", "bureau_credit_count"]
    )

    assert set(registry["feature_name"]) == {
        "AMT_CREDIT",
        "credit_to_income_ratio",
        "bureau_credit_count",
    }
    assert "availability_time" in registry.columns
    assert "production_controls" in registry.columns
    assert registry["used_in_model"].all()
