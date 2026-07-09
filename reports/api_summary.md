# API Deployment Summary

The FinSight API serves the saved final LightGBM credit-risk model from `models/credit_risk_model.pkl`.

## Local Run Command

```bash
uvicorn src.api.main:app --reload
```

Interactive docs:

```text
http://127.0.0.1:8000/docs
```

## Endpoints

- `GET /health`: checks service and model availability.
- `POST /predict`: returns `default_probability`, `risk_band`, and `collections_priority_score`.
- `POST /explain`: returns prediction fields plus top reason codes.
- `GET /model_info`: returns model name, version, feature count, threshold, and validation/test metric summary.

## Request Body

The API expects model-ready feature names from `data/processed/model_features.parquet`.
Missing model features are defaulted to `0.0` and counted in the response.

```json
{
  "sk_id_curr": 406244,
  "features": {
    "AMT_INCOME_TOTAL": 135000.0,
    "AMT_CREDIT": 675000.0,
    "AMT_ANNUITY": 33750.0,
    "credit_to_income_ratio": 5.0,
    "annuity_to_income_ratio": 0.25,
    "external_score_mean": 0.22,
    "employment_years": 1.5,
    "bureau_credit_count": 0.0,
    "installment_late_payment_count": 2.0
  }
}
```

## Collections Priority Formula

```text
collections_priority_score =
100 * default_probability
    * (0.70 + 0.30 * normalized_credit_amount)
    * risk_band_weight
```

Risk band weights:

- Low Risk: `0.75`
- Medium Risk: `1.00`
- High Risk: `1.30`
- Critical Risk: `1.60`

## Docker

```bash
docker build -t finsight-credit-risk .
docker run -p 8000:8000 finsight-credit-risk
```

The Docker image copies the API code, trained model, final metrics, and sample reason-code file.
