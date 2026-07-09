# FinSight GitHub Release Checklist

Use this checklist before sharing the repository link with recruiters, interviewers, or GitHub reviewers.

## Repository Safety

- [ ] Raw data files are not tracked.
- [ ] Processed data files are not tracked.
- [ ] Trained model binaries are not tracked if large.
- [ ] Virtual environment files are not tracked.
- [ ] Large HTML monitoring reports are ignored.
- [ ] No local absolute paths appear in code or documentation.
- [ ] No secrets, tokens, or credentials are committed.
- [ ] License, security policy, contributing guide, changelog, and GitHub templates are present.

Suggested check:

```bash
git status --ignored
```

## Local Quality Checks

- [ ] Source files compile.
- [ ] Unit and smoke tests pass.
- [ ] Repository hygiene tests pass.
- [ ] API tests pass with mocked model service.
- [ ] Documentation links point to existing files.

Suggested check:

```bash
make check
```

Current verified result: `30` tests passed.

## Portfolio Evidence

- [ ] README explains the business problem, architecture, metrics, and run commands.
- [ ] Final case study is present.
- [ ] Model card is present.
- [ ] Governance checklist is present.
- [ ] Leakage audit report is present.
- [ ] Fairness/proxy-risk report is present.
- [ ] Calibration report is present.
- [ ] Business impact report is present.
- [ ] Dashboard-ready outputs are present.
- [ ] Reviewer guide is present.
- [ ] Changelog summarizes project maturity milestones.
- [ ] Final submission note and final project audit are present.
- [ ] MLflow tracking and model registry documentation are present.
- [ ] Feature registry and timestamp-lineage documentation are present.

## GitHub Presentation

- [ ] Repository name is clear and professional.
- [ ] README appears correctly on GitHub.
- [ ] Badges render correctly.
- [ ] License is visible on GitHub.
- [ ] Final reviewer links are visible near the top of README.
- [ ] Project description mentions credit risk, collections, explainability, monitoring, and FastAPI.
- [ ] Repo topics include relevant keywords such as `credit-risk`, `machine-learning`, `pyspark`, `fastapi`, `shap`, `model-monitoring`, and `fintech`.
- [ ] If the repository is private, access is granted to anyone expected to review it.

## Interview Readiness

- [ ] You can explain why accuracy is not the main metric.
- [ ] You can explain why LightGBM was selected.
- [ ] You can explain how Recall@Top-10% maps to collections capacity.
- [ ] You can explain what the leakage audit did and did not prove.
- [ ] You can explain proxy-risk findings carefully without overstating fairness claims.
- [ ] You can explain why calibration matters for credit-risk probabilities.
- [ ] You can explain how monitoring would work in real production.
- [ ] You can describe the next production steps: feature registry, timestamp controls, compliance review, model registry, and live monitoring.

## Final Push Flow

```bash
git status
make check
git add README.md PROJECT_BRIEF.md ROADMAP.md REVIEW_GUIDE.md RELEASE_CHECKLIST.md reports/ tests/
git commit -m "Polish repository review guide"
git push origin main
```

Only stage files intentionally changed for the current step. Do not force-add ignored raw data, processed data, models, virtual environments, or HTML reports.
