import numpy as np
import pytest
from sklearn.metrics import brier_score_loss

from src.models.statistical_validation import paired_bootstrap, metric_values, select_calibration
from src.business.experiment_analysis import compare_conversion


def test_paired_identical_models_have_exact_zero_difference():
    y = np.tile([0, 0, 0, 1], 30)
    scores = np.linspace(.01, .99, len(y))
    result = paired_bootstrap(y, scores, scores, repetitions=100)
    delta = result[result.comparison == "challenger_minus_champion"]
    assert np.all(delta[["estimate", "lower_95", "upper_95"]].to_numpy() == 0)


def test_bootstrap_rejects_bad_inputs():
    with pytest.raises(ValueError):
        paired_bootstrap([0, 1], [0.1, np.nan], [.1, .9])
    with pytest.raises(ValueError):
        paired_bootstrap([0, 0], [.1, .2], [.1, .2])
    with pytest.raises(ValueError):
        paired_bootstrap([0, 1], [.1], [.1, .2])


def test_ks_ties_do_not_create_separation():
    result = metric_values(np.array([0, 1, 0, 1]), np.full(4, .5))
    assert result[3] == 0


def test_calibration_selection_subsets_disjoint_and_brier_based():
    y = np.tile([0, 0, 0, 1], 100)
    p = np.linspace(.1, .8, len(y))
    selected, rows, fit, selection = select_calibration(y, p)
    assert not set(fit) & set(selection)
    assert set(fit) | set(selection) == set(range(len(y)))
    assert selected == min(rows, key=lambda r: (r["selection_brier"], r["method"]))["method"]
    raw = next(r for r in rows if r["method"] == "uncalibrated")
    assert raw["selection_brier"] == pytest.approx(brier_score_loss(y[selection], p[selection]))


def test_conversion_effect_and_null():
    control = [0] * 90 + [1] * 10
    treatment = [0] * 80 + [1] * 20
    assert compare_conversion(control, treatment)["absolute_effect"] == pytest.approx(.1)
    assert compare_conversion(control, control)["two_sided_p_value"] == 1
    with pytest.raises(ValueError):
        compare_conversion([0, 0], [1, 1])
