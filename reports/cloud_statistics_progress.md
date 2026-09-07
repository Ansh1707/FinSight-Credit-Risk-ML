# Cloud And Statistics Extension

## Execution Steps

1. Completed: inspected saved champion/challenger artifacts and reconstructed their original test scores before uncertainty analysis.
2. Completed: computed 1,000 paired applicant bootstrap replicates and validation-only calibration selection. See [statistical validation](statistical_validation.md).
3. Completed: corrected historical test-based calibration recommendation wording; preserved the historical measurements and documented test reuse.
4. Completed: added a separately labeled [synthetic experiment](synthetic_experiment.md), with effect size, 95% CI and hypothesis-test assumptions.
5. Prepared: public-data sample exporter, Databricks SQL/PySpark notebook, MLflow logging, cloud output storage and repeatable job configuration. See [setup guide](../cloud/databricks/README.md).
6. Pending user workspace: create Databricks account/storage, upload sample, verify dependencies and execute two successful job runs.
7. Pending actual cloud evidence: review and publish aggregate results, verify rerun agreement and update the cloud experience claim.

## Evidence Boundaries

Local tests establish implementation behavior, not cloud execution. Historical evaluation remains retrospective: no new split can undo prior model/test choices. Bootstrap uncertainty does not resolve accepted-applicant bias, historical timing assumptions or regulatory approval. The synthetic experiment is educational and supplies no real conversion uplift. Existing calibration and cross-validation evidence is retained. FinSight360 experiment records were not provided, so no claims are made about that project's results.

## Local Verification

- 53 tests passed, including paired-bootstrap identity, invalid inputs, calibration subset separation, experimental effect calculations, cloud split integrity and training-only preprocessing/model selection.
- Source compilation passed, including the exported cloud notebook. Databricks APIs, dependency installation, storage writes and bundle deployment still require workspace execution.
- The upload sample contains 20,000 actual applicants; the aggregate manifest records source size and checksum. Applicant-level sample data remains ignored by Git.
- No ranking model was retrained. Existing test PR-AUC for both champion and challenger was reproduced before resampling.
- One existing FastAPI/Starlette test-client deprecation warning remains; it did not fail tests.

## Next Task

"Help me execute FinSight's prepared Databricks workflow. I have created a workspace. Follow cloud/databricks/README.md, verify storage and notebook dependencies, run the job twice, compare aggregate evidence and publish sanitized results to GitHub. Do not claim cloud execution until the jobs succeed."
