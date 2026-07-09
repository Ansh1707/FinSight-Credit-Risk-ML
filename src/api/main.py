"""FastAPI service for FinSight credit-risk predictions."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from src.api.model_loader import get_model_service
from src.api.schemas import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    ExplainResponse,
    HealthResponse,
    ModelInfoResponse,
    PredictionRequest,
    PredictionResponse,
    RootResponse,
)


app = FastAPI(
    title="FinSight Credit Risk API",
    description=(
        "Serve default probability, risk bands, collections priority scores, "
        "and business-readable reason codes from the trained credit-risk model."
    ),
    version="1.0.0",
)


@app.get("/", response_model=RootResponse)
def root() -> RootResponse:
    """Return a friendly API landing response."""
    return RootResponse(
        project="FinSight Credit Risk API",
        status="ok",
        docs_url="/docs",
        health_url="/health",
        endpoints=[
            "GET /",
            "GET /health",
            "POST /predict",
            "POST /batch_predict",
            "POST /explain",
            "GET /model_info",
        ],
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


@app.post("/batch_predict", response_model=BatchPredictionResponse)
def batch_predict(request: BatchPredictionRequest) -> BatchPredictionResponse:
    """Return predictions for multiple applicants in one request."""
    try:
        service = get_model_service()
        predictions = [
            PredictionResponse(**service.predict(applicant.features))
            for applicant in request.applicants
        ]
        return BatchPredictionResponse(
            applicant_count=len(predictions),
            predictions=predictions,
        )
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
