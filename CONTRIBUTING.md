# Contributing

FinSight is a portfolio-grade data science project. Contributions should preserve reproducibility, raw-data safety, and business-readable documentation.

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run local checks:

```bash
make check
```

## Data Safety Rules

- Do not commit raw Home Credit files from `data/raw/`.
- Do not commit processed Parquet files from `data/processed/`.
- Do not commit trained model binaries from `models/` unless explicitly approved.
- Do not commit local notebooks with private paths, credentials, or large embedded outputs.
- Do not modify raw data files in place.

## Development Rules

- Keep code runnable from the VS Code terminal.
- Use relative paths.
- Keep scripts modular and command-line runnable.
- Do not use accuracy as the main model metric.
- Do not invent metrics or business results.
- Document assumptions in the relevant report or README section.
- Update tests when changing shared behavior.

## Pull Request Checklist

Before opening a pull request:

- [ ] `make check` passes.
- [ ] No raw data, processed data, model artifacts, virtual environments, or large HTML reports are staged.
- [ ] README or relevant report files are updated.
- [ ] Any new metrics are computed from actual outputs.
- [ ] Any model or feature change includes leakage and validation considerations.

## Documentation Style

Write for a fintech data science reviewer:

- Explain business meaning, not only technical implementation.
- Be explicit about limitations.
- Separate portfolio evidence from production claims.
- Avoid overstating fairness, compliance, or financial impact.
