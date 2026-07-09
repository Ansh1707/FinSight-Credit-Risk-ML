from pathlib import Path

import pandas as pd
import pytest

from src.data import load_data


def test_validate_required_files_reports_missing_files(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError) as exc_info:
        load_data.validate_required_files(tmp_path)

    message = str(exc_info.value)
    assert "Missing required raw data files" in message
    assert "application_train.csv" in message


def test_validate_required_files_returns_all_required_paths(tmp_path: Path) -> None:
    for file_name in load_data.REQUIRED_RAW_FILES:
        (tmp_path / file_name).write_text("col\n1\n", encoding="utf-8")

    paths = load_data.validate_required_files(tmp_path)

    assert len(paths) == len(load_data.REQUIRED_RAW_FILES)
    assert all(path.is_file() for path in paths)


def test_summarize_target_counts_and_percentages() -> None:
    frame = pd.DataFrame({"TARGET": [0, 0, 1, 1, 1]})

    summary = load_data.summarize_target(frame)

    assert summary.loc[summary["TARGET"] == "0", "count"].item() == 2
    assert summary.loc[summary["TARGET"] == "1", "count"].item() == 3
    assert summary.loc[summary["TARGET"] == "1", "percent"].item() == 60.0


def test_summarize_target_requires_target_column() -> None:
    with pytest.raises(ValueError, match="TARGET"):
        load_data.summarize_target(pd.DataFrame({"not_target": [0, 1]}))


def test_missing_and_dtype_summaries_are_business_readable() -> None:
    frame = pd.DataFrame(
        {
            "TARGET": [0, 1, 0],
            "income": [100.0, None, 200.0],
            "segment": ["A", None, "B"],
        }
    )

    missing = load_data.summarize_missing_values(frame)
    dtypes = load_data.summarize_dtypes(frame)

    assert missing.iloc[0]["missing_count"] == 1
    assert set(dtypes["dtype"]) >= {"int64", "float64"}
    assert {"object", "str"} & set(dtypes["dtype"])
