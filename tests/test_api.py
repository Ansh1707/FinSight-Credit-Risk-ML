from typing import Any

from fastapi.testclient import TestClient

from src.api import main


class FakeModelService:
    def predict(self, features: dict[str, float]) -> dict[str, Any]:
        return {
            "default_probability": 0.72,
            "risk_band": "Critical Risk",
            "collections_priority_score": 90.5,
            "credit_amount": features.get("AMT_CREDIT", 0.0),
            "missing_features_defaulted": 0,
            "missing_feature_names": [],
        }

    def explain(self, sk_id_curr: int | None, features: dict[str, float]) -> dict[str, Any]:
        return {
            **self.predict(features),
            "top_reason_codes": ["Low external credit score", "High annuity burden"],
            "reason_code_source": "test_fake_service",
        }

    def model_info(self) -> dict[str, Any]:
        return {
            "model_name": "FinSight Credit Risk Model",
            "model_type": "lightgbm",
            "model_version": "test",
            "feature_count": 2,
            "threshold": 0.7,
            "metric_summary": {
                "validation": {"roc_auc": 0.78},
                "test": {"roc_auc": 0.77},
            },
        }


def test_api_endpoints_with_mocked_model_service(monkeypatch) -> None:
    monkeypatch.setattr(main, "get_model_service", lambda: FakeModelService())
    client = TestClient(main.app)

    root = client.get("/")
    assert root.status_code == 200
    assert root.json()["docs_url"] == "/docs"
    assert "POST /batch_predict" in root.json()["endpoints"]

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok", "model_loaded": True}

    payload = {
        "sk_id_curr": 123,
        "features": {
            "AMT_CREDIT": 500000.0,
            "external_score_mean": 0.2,
        },
    }
    prediction = client.post("/predict", json=payload)
    assert prediction.status_code == 200
    assert prediction.json()["risk_band"] == "Critical Risk"
    assert prediction.json()["default_probability"] == 0.72

    explanation = client.post("/explain", json=payload)
    assert explanation.status_code == 200
    assert explanation.json()["top_reason_codes"] == [
        "Low external credit score",
        "High annuity burden",
    ]

    info = client.get("/model_info")
    assert info.status_code == 200
    assert info.json()["feature_count"] == 2


def test_batch_predict_scores_multiple_applicants(monkeypatch) -> None:
    monkeypatch.setattr(main, "get_model_service", lambda: FakeModelService())
    client = TestClient(main.app)

    response = client.post(
        "/batch_predict",
        json={
            "applicants": [
                {"sk_id_curr": 1, "features": {"AMT_CREDIT": 250000.0}},
                {"sk_id_curr": 2, "features": {"AMT_CREDIT": 750000.0}},
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["applicant_count"] == 2
    assert len(payload["predictions"]) == 2
    assert payload["predictions"][1]["credit_amount"] == 750000.0


def test_batch_predict_requires_at_least_one_applicant(monkeypatch) -> None:
    monkeypatch.setattr(main, "get_model_service", lambda: FakeModelService())
    client = TestClient(main.app)

    response = client.post("/batch_predict", json={"applicants": []})

    assert response.status_code == 422


def test_api_converts_value_errors_to_422(monkeypatch) -> None:
    class FailingService(FakeModelService):
        def predict(self, features: dict[str, float]) -> dict[str, Any]:
            raise ValueError("Unknown feature names: bad_feature")

    monkeypatch.setattr(main, "get_model_service", lambda: FailingService())
    client = TestClient(main.app)

    response = client.post("/predict", json={"features": {"bad_feature": 1.0}})

    assert response.status_code == 422
    assert "Unknown feature names" in response.json()["detail"]
