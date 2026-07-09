"""FastAPI service for FinSight credit-risk predictions."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from src.api.model_loader import get_model_service
from src.api.schemas import (
    ExplainResponse,
    HealthResponse,
    ModelInfoResponse,
    PredictionRequest,
    PredictionResponse,
)


app = FastAPI(
    title="FinSight Credit Risk API",
    description=(
        "Serve default probability, risk bands, collections priority scores, "
        "and business-readable reason codes from the trained credit-risk model."
    ),
    version="1.0.0",
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Health check endpoint."""
    try:
        get_model_service()
        return HealthResponse(status="ok", model_loaded=True)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest) -> PredictionResponse:
    """Return default probability, risk band, and collections priority score."""
    try:
        result = get_model_service().predict(request.features)
        return PredictionResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/explain", response_model=ExplainResponse)
def explain(request: PredictionRequest) -> ExplainResponse:
    """Return prediction plus top reason codes."""
    try:
        result = get_model_service().explain(request.sk_id_curr, request.features)
        return ExplainResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/model_info", response_model=ModelInfoResponse)
def model_info() -> ModelInfoResponse:
    """Return model metadata and validation metric summary."""
    try:
        return ModelInfoResponse(**get_model_service().model_info())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
