import numpy as np
import pandas as pd
import pytest

from cloud.databricks.workflow import FEATURES, SOURCE_COLUMNS, fit_baseline, validate_frame


def fixture_frame():
    rng = np.random.default_rng(7)
    frame = pd.DataFrame({c: rng.uniform(1, 100, 300) for c in set(SOURCE_COLUMNS + FEATURES)})
    frame["SK_ID_CURR"] = np.arange(300)
    frame["TARGET"] = np.tile([0, 0, 0, 0, 1], 60)
    frame.loc[:20, "AMT_ANNUITY"] = np.nan
    return frame


def test_cloud_splits_and_preprocessing_are_training_only():
    frame = fixture_frame()
    model, metrics, scores, manifest, params = fit_baseline(frame)
    assert manifest.groupby("split").size().to_dict() == {"test": 60, "train": 180, "validation": 60}
    assert set(scores.SK_ID_CURR) == set(manifest.loc[manifest.split == "test", "SK_ID_CURR"])
    train_ids = manifest.loc[manifest.split == "train", "SK_ID_CURR"]
    expected = frame.set_index("SK_ID_CURR").loc[train_ids, FEATURES].median().to_numpy()
    assert np.allclose(model.named_steps["simpleimputer"].statistics_, expected)
    changed = frame.copy()
    changed.loc[changed.SK_ID_CURR.isin(scores.SK_ID_CURR), FEATURES] = 1e8
    other, _, _, _, other_params = fit_baseline(changed)
    assert params == other_params
    assert np.array_equal(model.named_steps["logisticregression"].coef_, other.named_steps["logisticregression"].coef_)
    assert 0 <= metrics["test_average_precision"] <= 1


def test_cloud_bad_schema_and_duplicate_ids_rejected():
    frame = fixture_frame()
    with pytest.raises(ValueError, match="Missing required"):
        validate_frame(frame.drop(columns="TARGET"))
    frame.loc[1, "SK_ID_CURR"] = frame.loc[0, "SK_ID_CURR"]
    with pytest.raises(ValueError, match="unique"):
        validate_frame(frame)
