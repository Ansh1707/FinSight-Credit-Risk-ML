# Synthetic Randomized Experiment

Educational simulation of a product-message conversion experiment. These are generated outcomes, not Home Credit labels, measured customer outcomes, or evidence of business uplift. No FinSight360 dataset was supplied.

Seed 42; 5,000 users randomly assigned to each arm. Assumed probabilities: control 10%, treatment 12%. Observed control 9.94%; treatment 12.28%.

Treatment minus control: 2.340 percentage points; 95% unpooled normal CI [1.109, 3.571]. Two-sided pooled two-proportion z-test p=0.000196807.

Null hypothesis: equal conversion probabilities. Fixed horizon of 10,000 users, alpha 0.05, one predeclared outcome, no peeking or multiple tests. Independent users, random assignment, stable treatment, no interference and complete outcome capture are assumed. Counts support the normal approximation. A p-value is not the probability the null is true. A confidence interval describes repeated-procedure coverage, not certainty about a single experiment.

In simple language: randomly give two groups different messages, count conversions, and ask whether the observed gap is too large to explain comfortably by sampling noise. Real rollout decisions also require costs, guardrail metrics, power analysis, sample-ratio checks and replication. This simulation cannot justify a real product launch.
