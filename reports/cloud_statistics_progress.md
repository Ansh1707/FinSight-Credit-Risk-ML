# Cloud And Statistics Extension

## Execution Steps

1. Completed: inspected saved champion/challenger artifacts and reconstructed their original test scores before uncertainty analysis.
2. Completed: computed 1,000 paired applicant bootstrap replicates and validation-only calibration selection. See [statistical validation](statistical_validation.md).
3. Completed: corrected historical test-based calibration recommendation wording; preserved the historical measurements and documented test reuse.
4. Completed: added a separately labeled [synthetic experiment](synthetic_experiment.md), with effect size, 95% CI and hypothesis-test assumptions.
5. Completed implementation: public-data sample exporter, Databricks SQL/PySpark notebook, MLflow logging, cloud output storage and job configuration. See [setup guide](../cloud/databricks/README.md).
6. User-reported completion: configured workspace and executed two manual jobs successfully; supported by the supplied job-list screenshot.
7. Completed evidence review: two aggregate exports match exactly on data fingerprints, declared code revision, parameters, package versions, split counts, missingness and all six metrics. Published [cloud evidence](cloud_execution_summary.md) documents differences and verification limits.

## Evidence Boundaries

Local tests establish implementation behavior, not cloud execution. Historical evaluation remains retrospective: no new split can undo prior model/test choices. Bootstrap uncertainty does not resolve accepted-applicant bias, historical timing assumptions or regulatory approval. The synthetic experiment is educational and supplies no real conversion uplift. Existing calibration and cross-validation evidence is retained. FinSight360 experiment records were not provided, so no claims are made about that project's results.

## Local Verification

- 53 tests passed, including paired-bootstrap identity, invalid inputs, calibration subset separation, experimental effect calculations, cloud split integrity and training-only preprocessing/model selection.
- Source compilation passed, including the exported cloud notebook. Supplied completed run exports now support cloud execution; direct workspace inspection and CLI bundle deployment remain unverified.
- The upload sample contains 20,000 actual applicants; the aggregate manifest records source size and checksum. Applicant-level sample data remains ignored by Git.
- No local ranking model was retrained for statistical analysis. The separate cloud notebook trains its small logistic baseline per run. Existing local test PR-AUC for both champion and challenger was reproduced before resampling.
- One existing FastAPI/Starlette test-client deprecation warning remains; it did not fail tests.

## Remaining Optional Evidence Improvements

Capture job IDs, measured notebook hashes, runtime versions and model/prediction checksums in future runs. These are improvements to traceability, not prerequisites for accurately describing the current sample workflow demonstration. No additional cloud run is required merely to publish the supplied aggregate evidence.
