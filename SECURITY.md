# Security Policy

FinSight is a portfolio project and is not deployed as a live production service. Security guidance still matters because the project handles credit-risk-style data workflows.

## Supported Version

Only the latest `main` branch is maintained.

## Data Handling

- Raw data under `data/raw/` is ignored by Git.
- Processed data under `data/processed/` is ignored by Git.
- Trained model artifacts under `models/` are ignored by Git.
- Large generated HTML reports are ignored by Git.
- Do not commit secrets, access tokens, private URLs, or customer data.

## Reporting Issues

For a private repository, report issues directly to the repository owner. For a public fork, open a GitHub issue only if it does not expose private data, credentials, or sensitive paths.

Do not include:

- API tokens or credentials.
- Raw or processed applicant records.
- Private local filesystem paths with usernames if avoidable.
- Large model or data artifacts.

## Production Note

The included FastAPI service is a local portfolio-serving layer. A real deployment would require authentication, authorization, request logging, prediction logging, rate limiting, model registry controls, monitoring alerts, and incident response ownership.
