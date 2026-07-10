# FinSight Production Readiness Runbook

This runbook describes how FinSight would be moved from a portfolio prototype to a controlled pre-production credit-risk service. It is not a production approval record. It documents deployment steps, operating cadence, monitoring thresholds, rollback, incident response, retraining triggers, ownership, and final sign-off gates.

## Operating Scope

| item | current portfolio status | production requirement |
| --- | --- | --- |
| Model artifact | `models/credit_risk_model.pkl` saved locally and ignored by Git | Store in controlled registry with approval stage, version, rollback pointer, and access control |
| Model version | `0.13.0` in `reports/model_registry.json` | Promote only after risk, legal, compliance, and MLOps sign-off |
| API | FastAPI local service under `src/api/` | Deploy behind authentication, logging, rate limits, and managed secrets |
| Batch scoring | `src/api/batch_score.py` with privacy-safe sample logs | Schedule controlled production jobs with secure input/output locations |
| Monitoring | Simulated historical monitoring reports | Monitor live scoring windows and matured labels |
| Governance | Model card, governance checklist, fair-lending review, challenger comparison | Convert documented controls into enforced approval workflows |

## Deployment Steps

1. Freeze the release candidate commit and record the Git SHA.
2. Run local quality checks:

```bash
make check
```

3. Rebuild or verify required artifacts:

```bash
python src/features/leakage_checks.py
python src/models/mlflow_tracking.py
python src/models/fair_lending_governance.py
python src/models/challenger_governance.py
python src/api/batch_score.py --input data/processed/model_features.parquet --limit 1000
python src/monitoring/evidently_monitoring.py
```

4. Review core governance artifacts:

- `reports/model_card.md`
- `reports/governance_checklist.md`
- `reports/model_registry.md`
- `reports/feature_registry.md`
- `reports/leakage_audit.md`
- `reports/fair_lending_review.md`
- `reports/challenger_governance_report.md`
- `reports/reject_inference_note.md`
- `reports/batch_scoring_summary.md`

5. Validate Docker/API startup:

```bash
docker build -t finsight-credit-risk .
docker run -p 8000:8000 finsight-credit-risk
```

6. Smoke-test endpoints:

- `GET /health`
- `GET /model_info`
- `POST /predict`
- `POST /batch_predict`
- `POST /explain`

7. Promote the model only after all pre-production sign-off checklist items are complete.

## Batch Scoring Operations

| operation | required control |
| --- | --- |
| Input handoff | Input files must come from approved source tables or feature store snapshots |
| Schema validation | Required model features must match `reports/batch_scoring_schema.json` |
| Job identity | Every run must create one `batch_id` |
| Record identity | Every scored applicant must receive one `request_id` |
| Score timestamp | Store `score_timestamp_utc` for every prediction |
| Model metadata | Store model name, version, stage, feature count, and schema version |
| Output fields | Store default probability, risk band, threshold flag, priority score, and reason-code fields |
| Privacy | Hash applicant identifiers and do not store raw feature values in review samples |
| Storage | Production logs must be outside Git in encrypted, access-controlled storage |
| Reconciliation | Row counts, missing-feature counts, and failed records must be reconciled after every batch |

Suggested local command:

```bash
python src/api/batch_score.py --input data/processed/model_features.parquet --limit 1000
```

## Monitoring Cadence

| monitoring area | cadence | owner | evidence artifact |
| --- | --- | --- | --- |
| Schema validation failures | Every batch | MLOps / Data Engineering | Batch scoring logs |
| Missingness changes | Every batch and weekly summary | Data Science | `reports/monitoring_summary.md` pattern |
| Feature drift | Weekly, and after source-system changes | Data Science / Data Engineering | PSI/drift report |
| Prediction drift | Every batch and weekly trend | Data Science | Prediction PSI and score quantiles |
| Segment review rates | Weekly | Credit Risk / Fair Lending | Segment monitoring table |
| Reason-code distribution | Weekly | Data Science / Compliance | Reason-code monitoring table |
| Calibration drift | Monthly when labels mature | Data Science | Calibration report |
| Labeled performance | Monthly or after outcome maturation | Data Science / Credit Risk | ROC-AUC, PR-AUC, Recall@Top-K, KS |
| Business impact | Monthly | Credit Risk / Collections | Review capacity table |

## Alert Thresholds

These thresholds are proposed pre-production guardrails. They must be approved by business, risk, compliance, and MLOps before real deployment.

| alert | warning threshold | critical threshold | action |
| --- | ---: | ---: | --- |
| Schema validation failure rate | > 0% | >= 1% of rows | Stop batch if critical; investigate input contract |
| Missing required features | > 0 features | Any model-critical feature missing | Stop scoring until schema is corrected |
| Feature PSI | >= 0.10 | >= 0.20 | Review source changes; critical requires model-risk review |
| Prediction PSI | >= 0.10 | >= 0.20 | Review score distribution and recent input shifts |
| Mean score shift | >= 5% relative | >= 10% relative | Compare input mix, model version, and data quality |
| Top-decile review-rate segment gap | >= 5 percentage points | >= 10 percentage points | Fair-lending/proxy-risk review |
| Missingness-rate change | >= 3 percentage points | >= 5 percentage points | Data quality investigation |
| PR-AUC degradation | >= 5% relative | >= 10% relative | Champion/challenger review and retraining assessment |
| Recall@Top-10% degradation | >= 5% relative | >= 10% relative | Collections capacity impact review |
| KS degradation | >= 0.03 absolute | >= 0.05 absolute | Model performance review |
| Calibration ECE | >= 0.03 | >= 0.05 | Recalibration assessment |

## Rollback Plan

1. Stop new scoring jobs or route API traffic away from the suspect model version.
2. Preserve the incident batch inputs, prediction logs, model version, Git SHA, and monitoring snapshots in secure storage.
3. Revert to the last approved model registry version and schema version.
4. Re-run schema validation and a small shadow scoring batch.
5. Notify business, credit risk, compliance, MLOps, and data owners.
6. Document customer or operational impact if any decisions were affected.
7. Restart scoring only after owner approval and post-rollback validation.

Rollback must not use unapproved local model files or untracked artifacts.

## Incident Response

| severity | example | response time | required action |
| --- | --- | --- | --- |
| SEV-1 | Wrong model version used, sensitive data exposed, or scores materially incorrect | Immediate | Stop scoring, escalate to all owners, preserve evidence, start rollback |
| SEV-2 | Batch failed, schema contract broken, critical drift alert triggered | Same business day | Pause affected batch, investigate, approve restart |
| SEV-3 | Warning drift, moderate metric movement, reason-code distribution shift | Within 3 business days | Document root cause and monitoring plan |
| SEV-4 | Documentation or dashboard issue without scoring impact | Next planning cycle | Fix and record in changelog |

Incident notes should include:

- Incident ID
- Detection time
- Affected model version
- Affected batch IDs or API time window
- Impacted record count
- Root cause
- Decision impact assessment
- Rollback or mitigation action
- Owners and sign-off
- Follow-up controls

## Retraining And Recalibration Triggers

Retraining or recalibration review should be opened when any of the following occur:

- Critical feature or prediction drift persists for two consecutive monitoring windows.
- PR-AUC, Recall@Top-10%, or KS crosses the critical degradation threshold after labels mature.
- Calibration ECE crosses the approved critical threshold.
- Business policy, applicant mix, bureau source, or collections strategy changes materially.
- New rejected-applicant outcome data becomes available for approved reject-inference work.
- Fair-lending/proxy-risk review rejects a champion feature group and requires a new challenger.
- Reason-code distribution shifts enough to affect analyst or compliance interpretation.
- Data lineage controls change for bureau, previous application, repayment, POS, or credit-card features.

Retraining must repeat baseline comparison, final model validation, calibration, leakage audit, feature registry review, fair-lending/proxy-risk review, challenger comparison, model card update, and registry approval.

## Ownership Matrix

| function | responsibilities |
| --- | --- |
| Data Science | Model validation, challenger analysis, calibration, reason codes, monitoring interpretation |
| Credit Risk | Threshold strategy, review capacity, risk-band policy, business impact review |
| Collections Operations | Queue capacity, contact prioritization, operational feedback |
| Data Engineering | Source data contracts, feature pipelines, batch inputs, data quality |
| MLOps / Platform | API deployment, batch jobs, model registry, logging, rollback, monitoring jobs |
| Compliance / Fair Lending | Protected/proxy feature review, adverse-action review, policy restrictions |
| Legal | Regulatory interpretation, customer-facing constraints, data-use approvals |
| Security / Privacy | Access control, secrets, audit log retention, privacy review |
| Product / Business Owner | Intended use, launch decision, success criteria, sign-off |

## Final Pre-Production Sign-Off Checklist

- [ ] Business owner approved intended use and prohibited use.
- [ ] Credit risk owner approved threshold and review-capacity strategy.
- [ ] Compliance/fair-lending owner reviewed proxy-risk, protected features, and reason-code use.
- [ ] Legal owner reviewed adverse-action and customer-facing limitations.
- [ ] Data owner approved source data contracts and feature availability timestamps.
- [ ] MLOps owner approved deployment, batch scoring, logging, monitoring, and rollback plan.
- [ ] Security/privacy owner approved log fields, hashed identifiers, storage, retention, and access controls.
- [ ] Model registry entry includes model artifact, version, metrics, Git SHA, approval stage, and rollback pointer.
- [ ] Feature registry and leakage audit are current.
- [ ] Batch scoring schema validation passes on representative pre-production input.
- [ ] API smoke tests pass in the target environment.
- [ ] Monitoring jobs and alert routing are configured.
- [ ] Incident response owners and escalation channels are documented.
- [ ] Champion/challenger tradeoff is reviewed.
- [ ] Reject-inference limitation is acknowledged.
- [ ] Final launch approval is recorded.

## Portfolio Boundary

FinSight is portfolio-ready and production-style, but not production-approved. Real deployment would still require lender-specific data contracts, secure infrastructure, formal fair-lending and legal review, adverse-action approval, live monitoring, incident ownership, and documented approval workflow.
