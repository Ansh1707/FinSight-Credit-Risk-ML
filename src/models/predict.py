"""Prediction utility for the saved final credit-risk model.

Examples:
    python src/models/predict.py --input data/processed/model_features.parquet --limit 5
    python src/models/predict.py --input applicants.csv --output reports/predictions.csv
"""

from __future__ import annotations

import argparse
import os
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


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Score applicants with the final model.")
    parser.add_argument("--input", required=True, help="CSV or Parquet file to score.")
    parser.add_argument("--output", default=None, help="Optional CSV output path.")
    parser.add_argument("--limit", type=int, default=None, help="Optional row limit.")
    return parser.parse_args()


def load_model(model_path: Path = MODEL_PATH) -> dict[str, Any]:
    """Load final model bundle."""
    if not model_path.exists():
        raise FileNotFoundError(
            "Missing models/credit_risk_model.pkl. "
            "Run python src/models/train_final_model.py first."
        )
    return joblib.load(model_path)


def load_input(path: Path, limit: int | None = None) -> pd.DataFrame:
    """Load input records from CSV or Parquet."""
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    if path.suffix.lower() == ".csv":
        data = pd.read_csv(path)
    elif path.suffix.lower() == ".parquet" or path.is_dir():
        data = pd.read_parquet(path)
    else:
        raise ValueError("Input must be a CSV file or Parquet path.")

    if limit:
        data = data.head(limit)
    return data.replace([np.inf, -np.inf], np.nan).fillna(0)


def risk_band(probability: float) -> str:
    """Map default probability to a simple business risk band."""
    if probability >= 0.50:
        return "high"
    if probability >= 0.25:
        return "medium"
    return "low"


def score_applicants(data: pd.DataFrame, model_bundle: dict[str, Any]) -> pd.DataFrame:
    """Score applicants and return probabilities, bands, and threshold decisions."""
    feature_columns = model_bundle["feature_columns"]
    missing_columns = [column for column in feature_columns if column not in data.columns]
    if missing_columns:
        raise ValueError(
            "Input data is missing required feature columns: "
            + ", ".join(missing_columns[:20])
        )

    ids = data["SK_ID_CURR"] if "SK_ID_CURR" in data.columns else pd.Series(range(len(data)))
    scores = model_bundle["model"].predict_proba(data[feature_columns])[:, 1]
    threshold = model_bundle["threshold"]

    return pd.DataFrame(
        {
            "SK_ID_CURR": ids,
            "default_probability": scores,
            "risk_band": [risk_band(score) for score in scores],
            "above_operational_threshold": scores >= threshold,
        }
    )


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    model_bundle = load_model()
    data = load_input(Path(args.input), limit=args.limit)
    predictions = score_applicants(data, model_bundle)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        predictions.to_csv(output_path, index=False)
        print(f"Predictions saved to: {output_path}")
    else:
        print(predictions.to_string(index=False))


if __name__ == "__main__":
    main()
