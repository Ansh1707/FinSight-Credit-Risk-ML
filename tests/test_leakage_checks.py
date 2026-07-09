from src.features import leakage_checks


def test_classify_forbidden_features() -> None:
    risk_level, rationale = leakage_checks.classify_feature("TARGET")

    assert risk_level == "fail"
    assert "Forbidden" in rationale


def test_classify_application_and_historical_features() -> None:
    assert leakage_checks.classify_feature("AMT_CREDIT")[0] == "low"
    assert leakage_checks.classify_feature("credit_to_income_ratio")[0] == "low"
    assert leakage_checks.classify_feature("bureau_credit_count")[0] == "medium"
    assert leakage_checks.classify_feature("mystery_feature")[0] == "review"


def test_audit_feature_set_flags_forbidden_and_missing_features() -> None:
    model_features = ["AMT_CREDIT", "TARGET", "bureau_credit_count", "missing_col"]
    processed_columns = ["AMT_CREDIT", "TARGET", "bureau_credit_count"]

    audit, summary = leakage_checks.audit_feature_set(model_features, processed_columns)

    assert summary["pass"] is False
    assert summary["forbidden_features"] == ["TARGET"]
    assert summary["missing_from_processed"] == ["missing_col"]
    assert set(audit["risk_level"]) >= {"low", "fail", "medium"}

