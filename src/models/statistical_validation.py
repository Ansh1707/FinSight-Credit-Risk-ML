"""Retrospective paired uncertainty and validation-only calibration selection.

Run: python -m src.models.statistical_validation --bootstrap 1000
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score, roc_curve
from sklearn.model_selection import train_test_split

from src.models.calibrate_model import (
    expected_calibration_error, fit_calibrators, markdown_table, split_data,
)
from src.models.metrics import recall_at_top_k


def metric_values(y, scores):
    """KS evaluates complete score ties together, using ROC thresholds."""
    fpr, tpr, _ = roc_curve(y, scores)
    return np.array([
        roc_auc_score(y, scores), average_precision_score(y, scores),
        recall_at_top_k(y, scores), np.max(tpr - fpr),
        brier_score_loss(y, scores), expected_calibration_error(y, scores),
    ])


METRICS = ["roc_auc", "average_precision", "recall_at_top_10pct", "ks", "brier", "ece"]


def paired_bootstrap(y, first, second, repetitions=1000, seed=42):
    """Applicant-level percentile CIs, paired across models, stratified by label.

    Conditions on observed prevalence and fitted models. It does not estimate
    training variability or uncertainty from model selection.
    """
    y, first, second = map(np.asarray, (y, first, second))
    if y.ndim != 1 or first.shape != y.shape or second.shape != y.shape:
        raise ValueError("Labels and both probability vectors must be aligned 1D arrays.")
    if set(np.unique(y)) != {0, 1} or repetitions < 100:
        raise ValueError("Both binary classes and at least 100 bootstrap replicates are required.")
    for scores in (first, second):
        if not np.isfinite(scores).all() or ((scores < 0) | (scores > 1)).any():
            raise ValueError("Probabilities must be finite and in [0, 1].")
    rng = np.random.default_rng(seed)
    groups = [np.flatnonzero(y == label) for label in (0, 1)]
    draws = np.empty((repetitions, 3, len(METRICS)))
    for i in range(repetitions):
        idx = np.concatenate([rng.choice(g, len(g), replace=True) for g in groups])
        rng.shuffle(idx)
        a, b = metric_values(y[idx], first[idx]), metric_values(y[idx], second[idx])
        draws[i] = [a, b, b - a]
    a, b = metric_values(y, first), metric_values(y, second)
    rows = []
    for j, (name, point) in enumerate(zip(("champion", "challenger", "challenger_minus_champion"), (a, b, b-a))):
        for k, metric in enumerate(METRICS):
            lower, upper = np.quantile(draws[:, j, k], [0.025, 0.975])
            rows.append(dict(comparison=name, metric=metric, estimate=float(point[k]),
                             lower_95=float(lower), upper_95=float(upper)))
    return pd.DataFrame(rows)


def select_calibration(y_valid, valid_scores, seed=42):
    """Fit on one validation half; choose by Brier on the other half only."""
    fit, select = train_test_split(np.arange(len(y_valid)), test_size=0.5,
                                   stratify=y_valid, random_state=seed)
    transforms = fit_calibrators(pd.Series(np.asarray(y_valid)[fit]), valid_scores[fit])
    rows = [{"method": name, "selection_brier": float(brier_score_loss(
        np.asarray(y_valid)[select], transform(valid_scores[select])))}
        for name, transform in transforms.items()]
    selected = min(rows, key=lambda row: (row["selection_brier"], row["method"]))["method"]
    return selected, rows, fit, select


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(repetitions=1000):
    data_path = Path("data/processed/model_features.parquet")
    paths = [Path("models/credit_risk_model.pkl"), Path("models/less_sensitive_challenger_model.pkl")]
    for path in [data_path, *paths]:
        if not path.exists():
            raise FileNotFoundError(f"Required existing artifact missing: {path}. No automatic retraining is performed.")
    data = pd.read_parquet(data_path)
    if data.SK_ID_CURR.isna().any() or data.SK_ID_CURR.duplicated().any():
        raise ValueError("Applicant bootstrap requires one non-null unique SK_ID_CURR per row.")
    if set(data.TARGET.unique()) != {0, 1}:
        raise ValueError("TARGET must contain only 0 and 1, without missing labels.")
    bundles = [joblib.load(path) for path in paths]
    metadata = bundles[0]["metrics"]
    if metadata["rows_loaded"] != len(data) or metadata["random_state"] != 42:
        raise ValueError("Data size or split seed differs from champion training metadata.")
    X = data.drop(columns=["SK_ID_CURR", "TARGET"]).replace([np.inf, -np.inf], np.nan).fillna(0)
    _, valid, test, _, yv, yt = split_data(X, data.TARGET)
    scores = [bundle["model"].predict_proba(test[bundle["feature_columns"]])[:, 1] for bundle in bundles]
    # Fail closed if reconstructed split does not reproduce recorded test performance.
    recorded = metadata["splits"]["test"]["classification"]["pr_auc"]
    if not np.isclose(average_precision_score(yt, scores[0]), recorded, atol=1e-8, rtol=0):
        raise ValueError("Test performance does not match saved evidence; verify dataset order and split provenance.")
    challenger_reference = pd.read_csv("reports/challenger_model_comparison.csv")
    challenger_ap = challenger_reference.loc[challenger_reference.model_name == "less_sensitive_challenger_model", "test_pr_auc"].iloc[0]
    if not np.isclose(average_precision_score(yt, scores[1]), challenger_ap, atol=1e-8, rtol=0):
        raise ValueError("Challenger predictions differ from saved test evidence.")
    intervals = paired_bootstrap(yt, *scores, repetitions=repetitions)
    valid_scores = bundles[0]["model"].predict_proba(valid[bundles[0]["feature_columns"]])[:, 1]
    selected, selection, fit, select = select_calibration(yv, valid_scores)
    transform = fit_calibrators(yv, valid_scores)[selected]
    calibrated = transform(scores[0])
    payload = {
        "analysis": "retrospective; previously inspected test set", "seed": 42,
        "rows": len(data), "test_rows": len(test), "test_defaults": int(yt.sum()),
        "bootstrap_repetitions": repetitions, "confidence_level": 0.95,
        "bootstrap_unit": "unique applicant; label-stratified paired resampling",
        "model_sha256": {p.name: file_hash(p) for p in paths},
        "data_order_sha256": hashlib.sha256(pd.util.hash_pandas_object(data, index=False).values.tobytes()).hexdigest(),
        "calibration_fit_rows": len(fit), "calibration_selection_rows": len(select),
        "calibration_selection": selection, "selected_calibration": selected,
        "selected_calibration_test_metrics": dict(zip(METRICS, metric_values(yt, calibrated).tolist())),
        "intervals": intervals.to_dict(orient="records"),
    }
    out = Path("reports")
    out.mkdir(exist_ok=True)
    intervals.to_csv(out / "statistical_intervals.csv", index=False)
    (out / "statistical_validation.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    report = "\n".join([
        "# Statistical Validation", "",
        f"Actual saved-model predictions: {len(test):,} test applicants; {int(yt.sum()):,} defaults. No ranking model was retrained.", "",
        "## Paired 95% Confidence Intervals", "",
        f"{repetitions:,} label-stratified applicant bootstrap replicates, seed 42. Both models use the same resampled applicants. PR-AUC here means average precision.", "",
        markdown_table(intervals), "",
        "Positive challenger-minus-champion differences favor the challenger for ranking; negative differences favor it for Brier/ECE. Intervals containing zero do not establish a directional difference. These are marginal intervals, without multiplicity adjustment; fairness and financial impact are not established by predictive differences.", "",
        "## Calibration Selection", "", markdown_table(pd.DataFrame(selection)), "",
        f"Selected `{selected}` by Brier on a held-out half of the original validation split. Calibrators fit on the other half. Refit the selected method on the whole validation split before reporting test metrics.", "",
        markdown_table(pd.DataFrame([payload["selected_calibration_test_metrics"]])), "",
        "This corrects future method-selection logic, not historical test reuse. The champion was already tuned using this validation set, and test results were previously inspected. This is retrospective supporting analysis, not a new untouched evaluation. A future experiment needs development-only tuning, out-of-fold calibration selection, and a locked temporal test cohort.", "",
        "## Assumptions And Limits", "",
        "One independent applicant per row is assumed. Household dependence requires cluster bootstrap; temporal dependence requires time-block evaluation. Intervals condition on observed class prevalence, fixed trained models and preprocessing; they exclude training, selection and future distribution-shift uncertainty. Historical source timing assumptions remain unresolved. Reconstructed splits reproduce stored PR-AUC but original artifacts lack row-level split manifests.", "",
        "## Probability In Plain Language", "",
        "Among many comparable applicants scored at 70%, about 70 out of 100 should default over the defined outcome window if probabilities are calibrated. It is not a guarantee for one person. A reliability plot compares average predicted probability with observed default frequency in each bin; points above the diagonal indicate underestimated risk. Brier measures squared probability error and reflects discrimination as well as calibration. ECE depends on binning. Calibration cannot repair missing populations, timing leakage or a changed outcome window.", "",
        "The selected transform is evaluated here only; the deployed champion artifact is unchanged. Do not describe API scores as newly calibrated based on this report.", "",
    ])
    (out / "statistical_validation.md").write_text(report)
    print(f"Saved statistical validation and intervals. Calibration selected: {selected}")
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bootstrap", type=int, default=1000)
    run(parser.parse_args().bootstrap)
