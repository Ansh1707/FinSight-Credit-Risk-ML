"""Create fair-lending and proxy-risk governance documentation.

Run from the project root:
    python src/models/fair_lending_governance.py

This script does not certify legal compliance. It converts existing
portfolio artifacts into a formal governance review that documents segment
signals, protected/proxy feature controls, limitations, and production
approval requirements.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPORTS_DIR = Path("reports")
FAIRNESS_METRICS_PATH = REPORTS_DIR / "fairness_proxy_metrics.csv"
FEATURE_REGISTRY_PATH = REPORTS_DIR / "feature_registry.csv"
OUTPUT_MD_PATH = REPORTS_DIR / "fair_lending_review.md"
OUTPUT_CONTROLS_PATH = REPORTS_DIR / "proxy_feature_controls.csv"
OUTPUT_JSON_PATH = REPORTS_DIR / "fair_lending_governance.json"


SEGMENT_METRICS = [
    "observed_default_rate",
    "mean_default_probability",
    "global_top10_review_rate",
    "default_capture_rate_within_segment",
    "non_default_review_rate",
]


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load existing fairness and feature-registry artifacts."""
    if not FAIRNESS_METRICS_PATH.exists():
        raise FileNotFoundError(
            "Missing reports/fairness_proxy_metrics.csv. "
            "Run python src/models/fairness_analysis.py first."
        )
    if not FEATURE_REGISTRY_PATH.exists():
        raise FileNotFoundError(
            "Missing reports/feature_registry.csv. "
            "Run python src/features/feature_registry.py first."
        )
    fairness = pd.read_csv(FAIRNESS_METRICS_PATH)
    registry = pd.read_csv(FEATURE_REGISTRY_PATH)
    return fairness, registry


def build_segment_disparities(fairness: pd.DataFrame) -> pd.DataFrame:
    """Summarize largest within-segment-type metric ranges."""
    rows: list[dict[str, Any]] = []
    for segment_type, group in fairness.groupby("segment_type"):
        for metric in SEGMENT_METRICS:
            values = group[metric].dropna()
            if values.empty:
                continue
            min_idx = values.idxmin()
            max_idx = values.idxmax()
            rows.append(
                {
                    "segment_type": segment_type,
                    "metric": metric,
                    "min_segment": fairness.loc[min_idx, "segment_value"],
                    "min_value": float(values.min()),
                    "max_segment": fairness.loc[max_idx, "segment_value"],
                    "max_value": float(values.max()),
                    "absolute_gap": float(values.max() - values.min()),
                    "max_to_min_ratio": (
                        float(values.max() / values.min()) if values.min() > 0 else np.nan
                    ),
                }
            )
    return pd.DataFrame(rows).sort_values("absolute_gap", ascending=False)


def feature_control_for(feature_name: str, feature_group: str, leakage_risk: str) -> dict[str, str]:
    """Assign governance treatment for a model feature."""
    name = feature_name.upper()
    group = feature_group.lower()

    if "CODE_GENDER" in name:
        return {
            "sensitivity_class": "protected_or_high_proxy",
            "control_decision": "restricted_pending_fair_lending_approval",
            "rationale": "Gender is directly sensitive or high-risk proxy information.",
            "production_control": (
                "Exclude or require formal fair-lending, policy, legal, and compliance "
                "approval before any underwriting or collections policy use."
            ),
        }
    if name == "OWN_CAR_AGE":
        return {
            "sensitivity_class": "asset_or_wealth_proxy",
            "control_decision": "allowed_with_monitoring",
            "rationale": "Vehicle age can be credit-relevant but may proxy wealth or socioeconomic status.",
            "production_control": (
                "Retain only with business justification; monitor distribution, "
                "missingness, and review impacts across protected/proxy segments."
            ),
        }
    if name in {"DAYS_BIRTH", "AGE_YEARS"}:
        return {
            "sensitivity_class": "protected_or_policy_sensitive",
            "control_decision": "restricted_pending_policy_approval",
            "rationale": "Age can be a protected or policy-sensitive attribute.",
            "production_control": (
                "Use only where legally permitted and policy-approved; monitor score, "
                "review-rate, and reason-code differences by age band."
            ),
        }
    if any(token in name for token in ["EDUCATION", "FAMILY_STATUS", "HOUSING", "OCCUPATION", "ORGANIZATION"]):
        return {
            "sensitivity_class": "proxy_sensitive",
            "control_decision": "fair_lending_review_required",
            "rationale": "Categorical socioeconomic or employment variables may proxy protected groups.",
            "production_control": (
                "Require documented business necessity, alternative-feature review, "
                "segment monitoring, and approval before production use."
            ),
        }
    if any(token in name for token in ["INCOME", "ANNUITY", "CREDIT_TO_INCOME"]):
        return {
            "sensitivity_class": "credit_capacity_with_proxy_risk",
            "control_decision": "allowed_with_monitoring",
            "rationale": "Affordability is credit-relevant but may create socioeconomic segmentation.",
            "production_control": (
                "Retain with clear business justification; monitor distribution and "
                "approval/review impacts by protected and proxy segments."
            ),
        }
    if any(token in name for token in ["SOCIAL_CIRCLE", "REGION"]):
        return {
            "sensitivity_class": "geographic_or_network_proxy",
            "control_decision": "enhanced_review_required",
            "rationale": "Regional or social-network signals can encode neighborhood or network proxies.",
            "production_control": (
                "Require proxy-risk review, adverse-impact monitoring, and documented "
                "justification against less sensitive alternatives."
            ),
        }
    if "EXT_SOURCE" in name or "EXTERNAL_SCORE" in name:
        return {
            "sensitivity_class": "third_party_score",
            "control_decision": "vendor_governance_required",
            "rationale": "External scores are strong predictors but need source transparency and stability checks.",
            "production_control": (
                "Require source documentation, refresh cadence, drift monitoring, "
                "and compliance review of upstream score construction."
            ),
        }
    if leakage_risk == "medium" or "history" in group or "repayment" in group:
        return {
            "sensitivity_class": "historical_credit_behavior",
            "control_decision": "allowed_with_timestamp_controls",
            "rationale": "Historical credit behavior is credit-relevant but timing-sensitive.",
            "production_control": (
                "Enforce source-record cutoff timestamps and monitor segment-level "
                "availability/missingness before production use."
            ),
        }
    return {
        "sensitivity_class": "standard_credit_feature",
        "control_decision": "allowed_with_standard_controls",
        "rationale": "No direct protected/proxy marker identified by the current governance screen.",
        "production_control": "Apply schema, missingness, drift, and reason-code monitoring.",
    }


def build_proxy_feature_controls(registry: pd.DataFrame) -> pd.DataFrame:
    """Create feature-level protected/proxy governance controls."""
    rows: list[dict[str, Any]] = []
    for record in registry.to_dict(orient="records"):
        control = feature_control_for(
            str(record["feature_name"]),
            str(record["feature_group"]),
            str(record["leakage_risk"]),
        )
        rows.append(
            {
                "feature_name": record["feature_name"],
                "feature_group": record["feature_group"],
                "source_tables": record["source_tables"],
                "availability_time": record["availability_time"],
                "leakage_risk": record["leakage_risk"],
                **control,
            }
        )
    return pd.DataFrame(rows)


def summarize_control_counts(controls: pd.DataFrame) -> pd.DataFrame:
    """Summarize features by governance decision."""
    return (
        controls.groupby(["control_decision", "sensitivity_class"], dropna=False)
        .size()
        .reset_index(name="feature_count")
        .sort_values(["control_decision", "sensitivity_class"])
    )


def markdown_table(df: pd.DataFrame, percent_columns: set[str] | None = None) -> str:
    """Render a DataFrame as a markdown table."""
    if df.empty:
        return "_No rows to display._"
    percent_columns = percent_columns or set()
    table = df.copy()
    for column in table.columns:
        if pd.api.types.is_numeric_dtype(table[column]):
            if column in percent_columns or column.endswith("_rate") or column.endswith("_share"):
                table[column] = (table[column] * 100).round(2)
            else:
                table[column] = table[column].round(4)
    table = table.replace([np.inf, -np.inf], np.nan).fillna("").astype(str)
    rows = ["| " + " | ".join(table.columns) + " |"]
    rows.append("| " + " | ".join("---" for _ in table.columns) + " |")
    rows.extend("| " + " | ".join(row) + " |" for row in table.itertuples(index=False, name=None))
    return "\n".join(rows)


def build_payload(
    fairness: pd.DataFrame,
    disparities: pd.DataFrame,
    controls: pd.DataFrame,
) -> dict[str, Any]:
    """Build machine-readable governance metadata."""
    top_review = fairness.sort_values("global_top10_review_rate", ascending=False).head(5)
    control_counts = summarize_control_counts(controls)
    return {
        "analysis_type": "fair_lending_and_proxy_risk_governance",
        "legal_certification_claimed": False,
        "adverse_action_certification_claimed": False,
        "models_retrained": False,
        "labels_created": False,
        "segment_metric_file": FAIRNESS_METRICS_PATH.as_posix(),
        "feature_registry_file": FEATURE_REGISTRY_PATH.as_posix(),
        "segments_reviewed": sorted(fairness["segment_type"].dropna().unique().tolist()),
        "segment_count": int(len(fairness)),
        "feature_count_reviewed": int(len(controls)),
        "control_decision_counts": control_counts.to_dict(orient="records"),
        "highest_review_rate_segments": top_review[
            [
                "segment_type",
                "segment_value",
                "applicant_count",
                "observed_default_rate",
                "global_top10_review_rate",
                "non_default_review_rate",
            ]
        ].to_dict(orient="records"),
        "largest_disparities": disparities.head(10).to_dict(orient="records"),
        "required_production_signoffs": [
            "business_owner",
            "credit_risk_owner",
            "fair_lending_or_compliance_owner",
            "legal_owner",
            "data_governance_owner",
            "mlops_owner",
        ],
    }


def build_report(
    fairness: pd.DataFrame,
    disparities: pd.DataFrame,
    controls: pd.DataFrame,
    payload: dict[str, Any],
) -> str:
    """Build formal fair-lending governance review report."""
    top_review = fairness.sort_values("global_top10_review_rate", ascending=False).head(10)
    largest_gaps = disparities.head(12)
    control_counts = summarize_control_counts(controls)
    restricted_controls = controls[
        controls["control_decision"].isin(
            [
                "restricted_pending_fair_lending_approval",
                "restricted_pending_policy_approval",
                "fair_lending_review_required",
                "enhanced_review_required",
            ]
        )
    ][
        [
            "feature_name",
            "feature_group",
            "sensitivity_class",
            "control_decision",
            "rationale",
            "production_control",
        ]
    ].head(25)

    return "\n".join(
        [
            "# Fair-Lending And Proxy-Risk Governance Review",
            "",
            "This report is a formal governance review for the FinSight portfolio model. "
            "It converts existing segment-performance metrics and feature-registry "
            "metadata into fair-lending review questions, protected/proxy feature "
            "controls, and production approval requirements.",
            "",
            "It is not a legal fair-lending certification, adverse-action compliance "
            "opinion, or regulatory approval. It does not retrain the model, modify raw "
            "data, infer protected-class membership, or invent labels.",
            "",
            "## Review Scope",
            "",
            f"- Segment metrics source: `{FAIRNESS_METRICS_PATH.as_posix()}`",
            f"- Feature registry source: `{FEATURE_REGISTRY_PATH.as_posix()}`",
            f"- Segment rows reviewed: `{payload['segment_count']}`",
            f"- Model features reviewed for proxy controls: `{payload['feature_count_reviewed']}`",
            "- Population: observed Home Credit accepted/booked applicant records with known `TARGET`.",
            "- Main policy lens: top-10% model-score review queue, not automatic approval or rejection.",
            "",
            "## Compliance Boundary",
            "",
            "- No legal certification is claimed.",
            "- No adverse-action notice language is approved by this report.",
            "- No protected class is inferred beyond available or encoded dataset proxies.",
            "- Segment gaps are review triggers, not proof of discrimination or compliance failure.",
            "- Production use requires fair-lending, policy, legal, risk, and model-governance sign-off.",
            "",
            "## Segment-Risk Interpretation",
            "",
            "The segment results show where the model concentrates review attention. These "
            "signals can be caused by true historical risk, historical policy selection, "
            "data quality, proxy effects, or model behavior. The correct senior data "
            "science interpretation is to route large gaps to review, not to treat them "
            "as standalone business rules.",
            "",
            "### Highest Top-10% Review-Rate Segments",
            "",
            markdown_table(
                top_review[
                    [
                        "segment_type",
                        "segment_value",
                        "applicant_count",
                        "observed_default_rate",
                        "mean_default_probability",
                        "global_top10_review_rate",
                        "non_default_review_rate",
                    ]
                ]
            ),
            "",
            "### Largest Segment Disparities",
            "",
            markdown_table(largest_gaps),
            "",
            "## Protected And Proxy Feature Controls",
            "",
            "The controls below separate standard credit-risk signals from features that "
            "need stronger governance because they are protected, policy-sensitive, or "
            "may proxy sensitive attributes.",
            "",
            "### Control Decision Summary",
            "",
            markdown_table(control_counts),
            "",
            "### Features Requiring Enhanced Review",
            "",
            markdown_table(restricted_controls),
            "",
            "Full feature-level controls are saved to "
            f"`{OUTPUT_CONTROLS_PATH.as_posix()}`.",
            "",
            "## Required Production Controls",
            "",
            "- Document intended use as ranking/manual-review support, not automated rejection.",
            "- Decide whether gender, age, education, occupation, family, housing, organization, region, and social-circle fields are excluded, restricted, or approved.",
            "- Re-run segment analysis after any feature-removal challenger model.",
            "- Evaluate less-sensitive challenger feature sets and compare PR-AUC, Recall@Top-K, KS, calibration, and business impact.",
            "- Review adverse-action reason-code language before any customer-facing use.",
            "- Monitor segment-level score distribution, top-decile review rate, non-default review rate, and reason-code distribution.",
            "- Combine this review with reject-inference analysis before making through-the-door underwriting claims.",
            "- Record business, risk, compliance, legal, data governance, and MLOps approvals before production deployment.",
            "",
            "## Limitations",
            "",
            "- The analysis uses available dataset proxies and cannot establish legal protected-class membership.",
            "- Rejected-applicant outcomes are not available; accepted-applicant bias remains documented separately.",
            "- Encoded category values may not map cleanly to human-readable categories if raw mappings are unavailable.",
            "- Segment differences may reflect historical credit-risk differences, historical policy bias, or both.",
            "- This review is evidence for portfolio governance maturity, not a substitute for a lender's formal compliance process.",
            "",
            "## Saved Outputs",
            "",
            f"- `{OUTPUT_MD_PATH.as_posix()}`",
            f"- `{OUTPUT_CONTROLS_PATH.as_posix()}`",
            f"- `{OUTPUT_JSON_PATH.as_posix()}`",
            "",
        ]
    )


def run() -> dict[str, Any]:
    """Create fair-lending governance outputs."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    fairness, registry = load_inputs()
    disparities = build_segment_disparities(fairness)
    controls = build_proxy_feature_controls(registry)
    payload = build_payload(fairness, disparities, controls)

    controls.to_csv(OUTPUT_CONTROLS_PATH, index=False)
    OUTPUT_JSON_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    OUTPUT_MD_PATH.write_text(
        build_report(fairness, disparities, controls, payload),
        encoding="utf-8",
    )
    return payload


def main() -> None:
    """CLI entry point."""
    payload = run()
    print("Fair-lending and proxy-risk governance review complete.")
    print(f"Legal certification claimed: {payload['legal_certification_claimed']}")
    print(f"Features reviewed: {payload['feature_count_reviewed']}")
    print(f"Segment rows reviewed: {payload['segment_count']}")
    print(f"Report saved to: {OUTPUT_MD_PATH}")
    print(f"Feature controls saved to: {OUTPUT_CONTROLS_PATH}")
    print(f"Governance JSON saved to: {OUTPUT_JSON_PATH}")


if __name__ == "__main__":
    main()
