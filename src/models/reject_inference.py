"""Create reject inference methodology documentation.

Run from the project root:
    python src/models/reject_inference.py

This script does not infer, fabricate, or assign labels to rejected applicants.
It documents accepted-applicant bias, missing rejected-applicant outcomes, safe
production methods, and how the limitation affects model interpretation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPORTS_DIR = Path("reports")
FINAL_METRICS_PATH = REPORTS_DIR / "final_model_metrics.json"
OUTPUT_MD_PATH = REPORTS_DIR / "reject_inference_note.md"
OUTPUT_JSON_PATH = REPORTS_DIR / "reject_inference_methodology.json"


PRODUCTION_METHODS = [
    {
        "method": "Parceling",
        "description": (
            "Assign inferred good/bad outcomes to rejected applicants within score "
            "bands using observed accepted-applicant bad rates adjusted by policy "
            "or bureau evidence."
        ),
        "benefit": "Simple to explain and commonly discussed in credit-risk workflows.",
        "risk": "Can reinforce historical policy bias if parceling assumptions are wrong.",
        "portfolio_status": "documented_only_not_applied",
    },
    {
        "method": "Fuzzy augmentation",
        "description": (
            "Add rejected applicants multiple times with fractional outcome weights "
            "based on estimated default probability or external performance signals."
        ),
        "benefit": "Captures uncertainty rather than forcing a single inferred label.",
        "risk": "Requires strong assumptions and careful calibration; can overstate certainty.",
        "portfolio_status": "documented_only_not_applied",
    },
    {
        "method": "Bureau or alternative outcome matching",
        "description": (
            "Use later bureau performance or external repayment/default signals to "
            "observe whether rejected applicants defaulted elsewhere."
        ),
        "benefit": "Anchors rejected outcomes in observed external behavior.",
        "risk": "Requires data contracts, identity matching, observation windows, and consent/legal review.",
        "portfolio_status": "production_candidate_requires_data",
    },
    {
        "method": "Exploration or randomized policy holdout",
        "description": (
            "Approve a controlled, risk-managed sample near the decision boundary to "
            "observe future repayment outcomes."
        ),
        "benefit": "Produces cleaner labels for policy expansion and bias reduction.",
        "risk": "Requires risk appetite, ethics review, operational controls, and compliance approval.",
        "portfolio_status": "production_candidate_requires_governance",
    },
    {
        "method": "Two-stage selection modeling",
        "description": (
            "Model approval/acceptance probability and use inverse-probability or "
            "selection-bias corrections when estimating default risk."
        ),
        "benefit": "Explicitly models the accepted-applicant selection mechanism.",
        "risk": "Requires rejected-applicant features and a reliable acceptance policy history.",
        "portfolio_status": "documented_only_not_applied",
    },
]


def load_project_context() -> dict[str, Any]:
    """Load available project context without requiring raw data."""
    context: dict[str, Any] = {
        "final_metrics_available": FINAL_METRICS_PATH.exists(),
        "rows_loaded": None,
        "model_type": None,
        "selection_metric": None,
        "feature_count": None,
        "test_roc_auc": None,
        "test_pr_auc": None,
        "test_recall_at_top_10pct": None,
        "test_ks_statistic": None,
    }
    if not FINAL_METRICS_PATH.exists():
        return context

    metrics = json.loads(FINAL_METRICS_PATH.read_text(encoding="utf-8"))
    test_metrics = metrics.get("splits", {}).get("test", {}).get("classification", {})
    context.update(
        {
            "rows_loaded": metrics.get("rows_loaded"),
            "model_type": metrics.get("model_type"),
            "selection_metric": metrics.get("selection_metric"),
            "feature_count": metrics.get("feature_count"),
            "test_roc_auc": test_metrics.get("roc_auc"),
            "test_pr_auc": test_metrics.get("pr_auc"),
            "test_recall_at_top_10pct": test_metrics.get("recall_at_top_10pct"),
            "test_ks_statistic": test_metrics.get("ks_statistic"),
        }
    )
    return context


def build_methodology_payload(context: dict[str, Any]) -> dict[str, Any]:
    """Build machine-readable reject inference methodology metadata."""
    return {
        "analysis_type": "reject_inference_methodology",
        "labels_created": False,
        "models_retrained": False,
        "raw_data_modified": False,
        "accepted_applicant_rows": context.get("rows_loaded"),
        "model_type": context.get("model_type"),
        "selection_metric": context.get("selection_metric"),
        "feature_count": context.get("feature_count"),
        "core_limitation": (
            "Observed default labels exist only for applicants/accounts that entered "
            "the historical booked-loan population. Rejected applicants do not have "
            "observed loan outcomes in this dataset."
        ),
        "interpretation_impact": [
            "Validation metrics are conditional on the observed accepted/booked population.",
            "Default probabilities should not be interpreted as fully through-the-door population risk.",
            "Thresholds and calibration may shift if rejected applicants are later included.",
            "Fairness and segment conclusions may be incomplete if rejected applicants differ by segment.",
        ],
        "production_methods": PRODUCTION_METHODS,
        "portfolio_decision": (
            "Do not invent rejected-applicant labels. Document the selection-bias "
            "limitation and define production methods that require additional data, "
            "policy review, and compliance approval."
        ),
    }


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    """Render selected fields from dictionaries as a markdown table."""
    if not rows:
        return "_No rows to display._"
    output = ["| " + " | ".join(columns) + " |"]
    output.append("| " + " | ".join("---" for _ in columns) + " |")
    for row in rows:
        output.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join(output)


def build_markdown_report(payload: dict[str, Any], context: dict[str, Any]) -> str:
    """Build reject inference methodology report."""
    metric_rows = [
        {"field": "accepted_applicant_rows", "value": context.get("rows_loaded")},
        {"field": "model_type", "value": context.get("model_type")},
        {"field": "selection_metric", "value": context.get("selection_metric")},
        {"field": "feature_count", "value": context.get("feature_count")},
        {"field": "test_roc_auc", "value": context.get("test_roc_auc")},
        {"field": "test_pr_auc", "value": context.get("test_pr_auc")},
        {
            "field": "test_recall_at_top_10pct",
            "value": context.get("test_recall_at_top_10pct"),
        },
        {"field": "test_ks_statistic", "value": context.get("test_ks_statistic")},
    ]

    return "\n".join(
        [
            "# Reject Inference Methodology Note",
            "",
            "This report documents accepted-applicant bias and reject inference "
            "considerations for FinSight. It does not create labels for rejected "
            "applicants, does not retrain models, and does not modify raw data.",
            "",
            "## Current Portfolio Scope",
            "",
            markdown_table(metric_rows, ["field", "value"]),
            "",
            "## Why Reject Inference Matters",
            "",
            "Credit-risk models are usually trained on applicants who were approved, "
            "booked, or otherwise observed after a lending decision. Applicants who "
            "were rejected do not generate repayment outcomes for the lender, so their "
            "true default behavior is missing. This creates accepted-applicant bias: "
            "the training data reflects historical approval policy, not the full "
            "through-the-door applicant population.",
            "",
            "## What Is Missing",
            "",
            "- Rejected-applicant repayment outcomes are not observed in this dataset.",
            "- Rejected-applicant labels are not inferable from `application_train.csv` alone.",
            "- The current validation metrics measure performance on the observed "
            "accepted/booked population.",
            "- The project does not use `application_test.csv` or Kaggle submission labels.",
            "",
            "## Portfolio-Safe Decision",
            "",
            f"{payload['portfolio_decision']}",
            "",
            "## Interpretation Impact",
            "",
            *[f"- {item}" for item in payload["interpretation_impact"]],
            "",
            "## Production Methods",
            "",
            markdown_table(
                payload["production_methods"],
                ["method", "description", "benefit", "risk", "portfolio_status"],
            ),
            "",
            "## Recommended Production Approach",
            "",
            "1. Preserve the current model as an accepted-population risk-ranking baseline.",
            "2. Store rejected-applicant application features with decision timestamp and reason.",
            "3. Obtain compliant external outcome data or create a controlled exploration policy.",
            "4. Compare baseline, parceling, fuzzy augmentation, and selection-model approaches.",
            "5. Re-evaluate PR-AUC, Recall@Top-K, KS, calibration, fairness/proxy-risk, and business impact.",
            "6. Require risk, legal, compliance, and model governance sign-off before policy use.",
            "",
            "## What This Means For FinSight",
            "",
            "FinSight should be presented as a strong accepted-applicant credit-risk "
            "and collections prioritization platform. It should not be described as "
            "a fully unbiased through-the-door underwriting model until rejected "
            "applicant outcomes or approved reject-inference assumptions are added.",
            "",
            "## Saved Outputs",
            "",
            f"- `{OUTPUT_MD_PATH.as_posix()}`",
            f"- `{OUTPUT_JSON_PATH.as_posix()}`",
            "",
        ]
    )


def run() -> dict[str, Any]:
    """Write reject inference methodology outputs."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    context = load_project_context()
    payload = build_methodology_payload(context)
    OUTPUT_JSON_PATH.write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    OUTPUT_MD_PATH.write_text(build_markdown_report(payload, context), encoding="utf-8")
    return payload


def main() -> None:
    """CLI entry point."""
    payload = run()
    print("Reject inference methodology documentation complete.")
    print(f"Labels created: {payload['labels_created']}")
    print(f"Models retrained: {payload['models_retrained']}")
    print(f"Report saved to: {OUTPUT_MD_PATH}")
    print(f"Methodology JSON saved to: {OUTPUT_JSON_PATH}")


if __name__ == "__main__":
    main()
