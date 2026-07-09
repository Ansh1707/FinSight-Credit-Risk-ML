"""Model loading and scoring utilities for the FastAPI service."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

REPORTS_DIR = Path("reports")
MPL_CACHE_DIR = REPORTS_DIR / ".matplotlib-cache"
MPL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE_DIR))

import joblib
import numpy as np
import pandas as pd


MODEL_PATH = Path("models/credit_risk_model.pkl")
METRICS_PATH = Path("reports/final_model_metrics.json")
REASON_CODES_PATH = Path("reports/sample_reason_codes.csv")
FEATURE_PATH = Path("data/processed/model_features.parquet")

RISK_BAND_WEIGHTS = {
    "Low Risk": 0.75,
    "Medium Risk": 1.00,
    "High Risk": 1.30,
    "Critical Risk": 1.60,
}

REASON_FEATURES = [
    "external_score_mean",
    "EXT_SOURCE_1",
    "EXT_SOURCE_2",
    "EXT_SOURCE_3",
    "credit_to_income_ratio",
    "loan_to_income_ratio",
    "annuity_to_income_ratio",
    "annuity_to_credit_ratio",
    "employment_years",
    "bureau_credit_count",
    "installment_late_payment_count",
    "installment_max_payment_delay_days",
    "pos_cash_late_count",
    "pos_cash_max_dpd_def",
    "credit_card_max_dpd",
    "previous_refused_count",
    "bureau_credit_debt_to_credit_ratio",
]


def assign_risk_band(default_probability: float) -> str:
    """Assign business risk band from predicted default probability."""
    if default_probability >= 0.70:
        return "Critical Risk"
    if default_probability >= 0.50:
        return "High Risk"
    if default_probability >= 0.25:
        return "Medium Risk"
    return "Low Risk"


class CreditRiskModelService:
    """Thin service wrapper around the saved model bundle."""

    def __init__(self) -> None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                "Missing models/credit_risk_model.pkl. "
                "Run python src/models/train_final_model.py first."
            )
        self.bundle = joblib.load(MODEL_PATH)
        self.model = self.bundle["model"]
        self.feature_columns = self.bundle["feature_columns"]
        self.threshold = float(self.bundle["threshold"])
        self.metrics = self._load_metrics()
        self.reason_codes = self._load_reason_codes()
        self.credit_min, self.credit_max = self._load_credit_amount_bounds()

    def _load_metrics(self) -> dict[str, Any]:
        if METRICS_PATH.exists():
            return json.loads(METRICS_PATH.read_text(encoding="utf-8"))
        return self.bundle.get("metrics", {})

    def _load_reason_codes(self) -> dict[int, list[str]]:
        if not REASON_CODES_PATH.exists():
            return {}
        reason_df = pd.read_csv(REASON_CODES_PATH)
        output: dict[int, list[str]] = {}
        for _, row in reason_df.iterrows():
            codes = []
            for column in ["reason_code_1", "reason_code_2", "reason_code_3"]:
                value = row.get(column)
                if pd.notna(value) and str(value) and str(value) not in codes:
                    codes.append(str(value))
            output[int(row["SK_ID_CURR"])] = codes
        return output

    def _load_credit_amount_bounds(self) -> tuple[float, float]:
        if FEATURE_PATH.exists():
            try:
                credit = pd.read_parquet(FEATURE_PATH, columns=["AMT_CREDIT"])["AMT_CREDIT"]
                return float(credit.min()), float(credit.max())
            except Exception:
                pass
        return 0.0, 4_000_000.0

    def prepare_features(self, features: dict[str, float]) -> tuple[pd.DataFrame, list[str]]:
        """Create a one-row model input frame and track defaulted columns."""
        unknown = sorted(set(features) - set(self.feature_columns))
        if unknown:
            raise ValueError(
                "Unknown feature names: "
                + ", ".join(unknown[:20])
                + ". Use model_info to inspect required features."
            )

        missing = [column for column in self.feature_columns if column not in features]
        row = {column: float(features.get(column, 0.0)) for column in self.feature_columns}
        return pd.DataFrame([row], columns=self.feature_columns), missing

    def predict(self, features: dict[str, float]) -> dict[str, Any]:
        """Score one applicant."""
        frame, missing = self.prepare_features(features)
        probability = float(self.model.predict_proba(frame)[:, 1][0])
        risk_band = assign_risk_band(probability)
        credit_amount = float(features.get("AMT_CREDIT", features.get("credit_amount", 0.0)))
        priority_score = self.collections_priority_score(
            default_probability=probability,
            credit_amount=credit_amount,
            risk_band=risk_band,
        )
        return {
            "default_probability": probability,
            "risk_band": risk_band,
            "collections_priority_score": priority_score,
            "credit_amount": credit_amount,
            "missing_features_defaulted": len(missing),
            "missing_feature_names": missing[:20],
        }

    def explain(self, sk_id_curr: int | None, features: dict[str, float]) -> dict[str, Any]:
        """Score one applicant and attach reason codes."""
        prediction = self.predict(features)
        if sk_id_curr is not None and sk_id_curr in self.reason_codes:
            return {
                **prediction,
                "top_reason_codes": self.reason_codes[sk_id_curr],
                "reason_code_source": "sample_shap_reason_codes",
            }

        return {
            **prediction,
            "top_reason_codes": self.rule_based_reason_codes(features),
            "reason_code_source": "feature_rule_fallback",
        }

    def collections_priority_score(
        self, default_probability: float, credit_amount: float, risk_band: str
    ) -> float:
        """Compute collections priority score using the documented formula."""
        denominator = self.credit_max - self.credit_min
        normalized_credit = 0.0 if denominator <= 0 else (credit_amount - self.credit_min) / denominator
        normalized_credit = float(np.clip(normalized_credit, 0.0, 1.0))
        score = (
            100
            * default_probability
            * (0.70 + 0.30 * normalized_credit)
            * RISK_BAND_WEIGHTS[risk_band]
        )
        return round(float(score), 2)

    def rule_based_reason_codes(self, features: dict[str, float]) -> list[str]:
        """Return business-readable reason codes from submitted feature values."""
        candidates: list[tuple[float, str]] = []

        external_score = features.get("external_score_mean")
        if external_score is not None and external_score <= 0.40:
            candidates.append((1 - external_score, "Low external credit score"))

        for feature in ["EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3"]:
            value = features.get(feature)
            if value is not None and value <= 0.35:
                candidates.append((1 - value, "Low external credit score"))

        for feature in ["credit_to_income_ratio", "loan_to_income_ratio"]:
            value = features.get(feature)
            if value is not None and value >= 3:
                candidates.append((value / 10, "High credit-to-income ratio"))

        for feature in ["annuity_to_income_ratio", "annuity_to_credit_ratio"]:
            value = features.get(feature)
            if value is not None and value >= 0.20:
                candidates.append((value, "High annuity burden"))

        employment_years = features.get("employment_years")
        if employment_years is not None and employment_years <= 2:
            candidates.append((1 / max(employment_years, 0.25), "Short employment duration"))

        bureau_count = features.get("bureau_credit_count")
        if bureau_count is not None and bureau_count <= 0:
            candidates.append((1.0, "Missing credit bureau signal"))

        for feature in [
            "installment_late_payment_count",
            "installment_max_payment_delay_days",
            "pos_cash_late_count",
            "pos_cash_max_dpd_def",
            "credit_card_max_dpd",
        ]:
            value = features.get(feature)
            if value is not None and value > 0:
                candidates.append((value, "Prior repayment delay"))

        previous_refused = features.get("previous_refused_count")
        if previous_refused is not None and previous_refused > 0:
            candidates.append((previous_refused, "Prior refused application history"))

        debt_ratio = features.get("bureau_credit_debt_to_credit_ratio")
        if debt_ratio is not None and debt_ratio >= 0.50:
            candidates.append((debt_ratio, "High bureau debt burden"))

        if not candidates:
            for feature in REASON_FEATURES:
                if feature in features:
                    candidates.append((abs(float(features[feature])), f"Model input signal: {feature}"))

        reason_codes: list[str] = []
        for _, reason in sorted(candidates, reverse=True):
            if reason not in reason_codes:
                reason_codes.append(reason)
            if len(reason_codes) == 3:
                break
        return reason_codes or ["No dominant submitted risk driver identified"]

    def model_info(self) -> dict[str, Any]:
        """Return compact model metadata for API consumers."""
        validation = self.metrics.get("splits", {}).get("validation", {}).get("classification", {})
        test = self.metrics.get("splits", {}).get("test", {}).get("classification", {})
        return {
            "model_name": "FinSight Credit Risk Model",
            "model_type": self.bundle.get("model_type", "lightgbm"),
            "model_version": "final_lightgbm_v1",
            "feature_count": len(self.feature_columns),
            "threshold": self.threshold,
            "metric_summary": {
                "validation": {
                    "roc_auc": validation.get("roc_auc"),
                    "pr_auc": validation.get("pr_auc"),
                    "recall_at_top_10pct": validation.get("recall_at_top_10pct"),
                    "ks_statistic": validation.get("ks_statistic"),
                },
                "test": {
                    "roc_auc": test.get("roc_auc"),
                    "pr_auc": test.get("pr_auc"),
                    "recall_at_top_10pct": test.get("recall_at_top_10pct"),
                    "ks_statistic": test.get("ks_statistic"),
                },
            },
        }


@lru_cache(maxsize=1)
def get_model_service() -> CreditRiskModelService:
    """Load and cache the model service once per API process."""
    return CreditRiskModelService()
