from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_expected_project_files_exist() -> None:
    expected_paths = [
        "README.md",
        "FINAL_SUBMISSION.md",
        "REVIEW_GUIDE.md",
        "RELEASE_CHECKLIST.md",
        "LICENSE",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "PROJECT_BRIEF.md",
        "ROADMAP.md",
        "requirements.txt",
        "Dockerfile",
        ".github/workflows/ci.yml",
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/ISSUE_TEMPLATE/reproducibility_issue.md",
        ".github/ISSUE_TEMPLATE/model_governance_review.md",
        "reports/model_card.md",
        "reports/final_project_audit.md",
        "reports/governance_checklist.md",
        "reports/mlflow_experiment_summary.md",
        "reports/model_registry.md",
        "reports/model_registry.json",
        "reports/feature_registry.md",
        "reports/feature_registry.csv",
        "reports/reject_inference_note.md",
        "reports/reject_inference_methodology.json",
        "reports/fair_lending_review.md",
        "reports/proxy_feature_controls.csv",
        "reports/fair_lending_governance.json",
        "reports/challenger_model_comparison.csv",
        "reports/challenger_governance_report.md",
        "reports/challenger_governance.json",
        "src/data/load_data.py",
        "src/features/pyspark_feature_engineering.py",
        "src/features/feature_registry.py",
        "src/features/leakage_checks.py",
        "src/models/train_baseline.py",
        "src/models/train_final_model.py",
        "src/models/cross_validate_model.py",
        "src/models/calibrate_model.py",
        "src/models/mlflow_tracking.py",
        "src/models/reject_inference.py",
        "src/models/fairness_analysis.py",
        "src/models/fair_lending_governance.py",
        "src/models/challenger_governance.py",
        "src/explainability/shap_reason_codes.py",
        "src/business/collections_scoring.py",
        "src/business/business_impact.py",
        "src/monitoring/evidently_monitoring.py",
        "src/api/main.py",
        "dashboard/build_dashboard_data.py",
    ]

    missing = [path for path in expected_paths if not (ROOT / path).exists()]
    assert not missing, f"Missing expected project files: {missing}"


def test_gitignore_protects_large_or_sensitive_artifacts() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    required_patterns = [
        "data/raw/",
        "data/processed/",
        "/models/",
        "reports/*.html",
        "mlruns/",
        ".venv/",
        "__pycache__/",
        "*.pyc",
        ".ipynb_checkpoints/",
    ]

    missing = [pattern for pattern in required_patterns if pattern not in gitignore]
    assert not missing, f"Missing .gitignore patterns: {missing}"


def test_readme_contains_portfolio_sections() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    required_sections = [
        "Business Problem",
        "Reviewer Quick Links",
        "Architecture",
        "Feature Registry And Timestamp Lineage",
        "Final Metrics",
        "Reject Inference Methodology",
        "Fair-Lending Governance Review",
        "Challenger Model Governance",
        "MLflow Tracking And Model Registry",
        "Explainability",
        "Collections Scoring Logic",
        "API Instructions",
        "Monitoring Summary",
        "Model Governance",
        "Dashboard Instructions",
        "Governance Artifacts",
        "Repository Maintenance",
        "Resume-Ready Impact Bullets",
        "Limitations",
    ]

    missing = [section for section in required_sections if section not in readme]
    assert not missing, f"Missing README sections: {missing}"
