"""Pydantic schemas for the FinSight credit-risk API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """Applicant feature payload.

    `features` should contain model-ready feature names from the PySpark pipeline.
    Missing model features are defaulted to 0.0 and returned in the response for
    transparency.
    """

    sk_id_curr: int | None = Field(
        default=None,
        description="Optional applicant ID. Used to join sample SHAP reason codes when available.",
        examples=[406244],
    )
    features: dict[str, float] = Field(
        ...,
        description="Model-ready feature values keyed by feature name.",
        examples=[
            {
                "AMT_INCOME_TOTAL": 135000.0,
                "AMT_CREDIT": 675000.0,
                "AMT_ANNUITY": 33750.0,
                "credit_to_income_ratio": 5.0,
                "annuity_to_income_ratio": 0.25,
                "external_score_mean": 0.22,
                "employment_years": 1.5,
                "bureau_credit_count": 0.0,
                "installment_late_payment_count": 2.0,
            }
        ],
    )


class RootResponse(BaseModel):
    """Helpful landing response for the API root."""

    project: str
    status: str
    docs_url: str
    health_url: str
    endpoints: list[str]


class PredictionResponse(BaseModel):
    """Prediction response for `/predict`."""

    default_probability: float
    risk_band: str
    collections_priority_score: float
    credit_amount: float
    missing_features_defaulted: int
    missing_feature_names: list[str]


class ExplainResponse(PredictionResponse):
    """Explanation response for `/explain`."""

    top_reason_codes: list[str]
    reason_code_source: str


class BatchPredictionRequest(BaseModel):
    """Batch scoring payload for `/batch_predict`."""

    applicants: list[PredictionRequest] = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Applicants to score. Each applicant uses the same payload shape as /predict.",
    )


class BatchPredictionResponse(BaseModel):
    """Batch prediction response."""

    applicant_count: int
    predictions: list[PredictionResponse]


class HealthResponse(BaseModel):
    """Health response."""

    status: str
    model_loaded: bool


class ModelInfoResponse(BaseModel):
    """Model metadata response."""

    model_name: str
    model_type: str
    model_version: str
    feature_count: int
    threshold: float
    metric_summary: dict[str, Any]
