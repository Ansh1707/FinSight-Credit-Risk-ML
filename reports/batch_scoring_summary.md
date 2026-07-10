# Batch Scoring And Prediction Logging Summary

This document describes a production-style batch scoring pattern for FinSight. It uses the saved final model, validates the input schema, scores a batch, and writes privacy-safe sample prediction and audit-log outputs. It does not retrain the model or write raw feature values to the committed audit sample.

## Run Command

```bash
python src/api/batch_score.py --input data/processed/model_features.parquet --limit 1000
```

## Schema Validation

- Status: `passed`
- Rows scored: `1000`
- Required feature count: `76`
- Missing feature count: `0`
- Unknown feature count: `0`
- Non-numeric feature count: `0`

## Model Metadata Logged

- Model name: `FinSight Credit Risk LightGBM`
- Model version: `0.13.0`
- Model stage: `portfolio_ready_not_production_approved`
- Batch ID: `batch_020425dbbc3a`
- Input schema version: `batch_scoring_schema_v1`

## Risk Band Summary

| risk_band | row_count | avg_default_probability | avg_priority_score |
| --- | --- | --- | --- |
| Critical Risk | 96 | 0.7843 | 93.1757 |
| High Risk | 170 | 0.5928 | 58.1317 |
| Low Risk | 413 | 0.1426 | 8.1423 |
| Medium Risk | 321 | 0.3647 | 27.6712 |

## Privacy-Safe Audit Log Sample

| request_id | batch_id | score_timestamp_utc | model_version | applicant_hash | risk_band | reason_code_1 | schema_validation_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| req_af95a2e13cc24147a6de4a9f1a8e8a6c | batch_020425dbbc3a | 2026-07-10T00:22:41+00:00 | 0.13.0 | ea07d4e6141c1b9d | Low Risk | High credit-to-income ratio | passed |
| req_4a21572fcd15410f94b01d45d1022eac | batch_020425dbbc3a | 2026-07-10T00:22:41+00:00 | 0.13.0 | 30eea7c146a60d4a | Medium Risk | Low external credit score | passed |
| req_141b7fc835a3492891b9a10671acc458 | batch_020425dbbc3a | 2026-07-10T00:22:41+00:00 | 0.13.0 | 158223318aa93e66 | Low Risk | High credit-to-income ratio | passed |
| req_79f712a16b964c339246e01ee4f05f29 | batch_020425dbbc3a | 2026-07-10T00:22:41+00:00 | 0.13.0 | 9027fb92295bde5a | Medium Risk | High credit-to-income ratio | passed |
| req_f31b0dda6b88406da4a1b02b4dd8f9a3 | batch_020425dbbc3a | 2026-07-10T00:22:41+00:00 | 0.13.0 | 105329ba02bfb25f | Low Risk | Prior repayment delay | passed |

## Production Logging Controls

- Generate one `request_id` per scored applicant.
- Generate one `batch_id` per scoring run.
- Store `score_timestamp_utc`, model version, model stage, and schema version with every score.
- Store risk band, operational-threshold flag, priority score, and reason-code fields.
- Hash applicant identifiers before writing review samples.
- Do not commit raw production logs, raw features, raw data, processed data, model binaries, credentials, or customer identifiers.

## Saved Outputs

- `reports/batch_scoring_sample.csv`
- `reports/prediction_audit_log_sample.csv`
- `reports/batch_scoring_schema.json`
- `reports/batch_scoring_summary.md`
