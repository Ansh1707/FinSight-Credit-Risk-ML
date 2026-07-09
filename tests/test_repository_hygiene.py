from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_expected_project_files_exist() -> None:
    expected_paths = [
        "README.md",
        "PROJECT_BRIEF.md",
        "ROADMAP.md",
        "requirements.txt",
        "Dockerfile",
        ".github/workflows/ci.yml",
        "reports/model_card.md",
        "reports/governance_checklist.md",
        "src/data/load_data.py",
        "src/features/pyspark_feature_engineering.py",
        "src/features/leakage_checks.py",
        "src/models/train_baseline.py",
        "src/models/train_final_model.py",
        "src/models/cross_validate_model.py",
        "src/models/calibrate_model.py",
        "src/models/fairness_analysis.py",
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
        "Architecture",
        "Final Metrics",
        "Explainability",
        "Collections Scoring Logic",
        "API Instructions",
        "Monitoring Summary",
        "Model Governance",
        "Dashboard Instructions",
        "Governance Artifacts",
        "Resume-Ready Impact Bullets",
        "Limitations",
    ]

    missing = [section for section in required_sections if section not in readme]
    assert not missing, f"Missing README sections: {missing}"
