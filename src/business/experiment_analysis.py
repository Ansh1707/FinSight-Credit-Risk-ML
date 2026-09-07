"""Synthetic randomized experiment for statistical practice, not business evidence.

Run: python -m src.business.experiment_analysis
"""

import json
from pathlib import Path

import numpy as np
from scipy.stats import norm


def compare_conversion(control, treatment):
    control, treatment = np.asarray(control), np.asarray(treatment)
    for values in (control, treatment):
        if values.ndim != 1 or len(values) < 2 or not np.isin(values, [0, 1]).all():
            raise ValueError("Each arm requires a 1D binary outcome array with at least two users.")
        if min(values.sum(), len(values)-values.sum()) < 10:
            raise ValueError("Normal approximation requires at least 10 successes and failures per arm.")
    pc, pt = control.mean(), treatment.mean()
    effect = pt - pc
    se = np.sqrt(pc*(1-pc)/len(control) + pt*(1-pt)/len(treatment))
    pooled = (control.sum()+treatment.sum())/(len(control)+len(treatment))
    null_se = np.sqrt(pooled*(1-pooled)*(1/len(control)+1/len(treatment)))
    z = effect / null_se
    return {"control_users": len(control), "treatment_users": len(treatment),
            "control_conversions": int(control.sum()), "treatment_conversions": int(treatment.sum()),
            "control_rate": float(pc), "treatment_rate": float(pt), "absolute_effect": float(effect),
            "lower_95": float(effect - norm.ppf(.975)*se), "upper_95": float(effect + norm.ppf(.975)*se),
            "z_statistic": float(z), "two_sided_p_value": float(2*norm.sf(abs(z)))}


def run():
    rng = np.random.default_rng(42)
    # Fixed-size randomized assignment; one binary outcome per independent user.
    assignment = rng.permutation(np.repeat([0, 1], 5000))
    outcomes = rng.binomial(1, np.where(assignment == 1, .12, .10))
    result = compare_conversion(outcomes[assignment == 0], outcomes[assignment == 1])
    payload = {"synthetic": True, "seed": 42, "assumed_control_probability": .10,
               "assumed_treatment_probability": .12, **result}
    out = Path("reports")
    out.mkdir(exist_ok=True)
    (out / "synthetic_experiment.json").write_text(json.dumps(payload, indent=2) + "\n")
    (out / "synthetic_experiment.md").write_text(
        "# Synthetic Randomized Experiment\n\n"
        "Educational simulation of a product-message conversion experiment. These are generated outcomes, not Home Credit labels, measured customer outcomes, or evidence of business uplift. No FinSight360 dataset was supplied.\n\n"
        f"Seed 42; 5,000 users randomly assigned to each arm. Assumed probabilities: control 10%, treatment 12%. Observed control {result['control_rate']:.2%}; treatment {result['treatment_rate']:.2%}.\n\n"
        f"Treatment minus control: {result['absolute_effect']*100:.3f} percentage points; 95% unpooled normal CI [{result['lower_95']*100:.3f}, {result['upper_95']*100:.3f}]. Two-sided pooled two-proportion z-test p={result['two_sided_p_value']:.6g}.\n\n"
        "Null hypothesis: equal conversion probabilities. Fixed horizon of 10,000 users, alpha 0.05, one predeclared outcome, no peeking or multiple tests. Independent users, random assignment, stable treatment, no interference and complete outcome capture are assumed. Counts support the normal approximation. A p-value is not the probability the null is true. A confidence interval describes repeated-procedure coverage, not certainty about a single experiment.\n\n"
        "In simple language: randomly give two groups different messages, count conversions, and ask whether the observed gap is too large to explain comfortably by sampling noise. Real rollout decisions also require costs, guardrail metrics, power analysis, sample-ratio checks and replication. This simulation cannot justify a real product launch.\n"
    )
    print("Saved explicitly synthetic experiment report and aggregate results.")


if __name__ == "__main__":
    run()
