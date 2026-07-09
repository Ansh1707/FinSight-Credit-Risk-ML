"""Validate and summarize the Home Credit raw data files.

Run from the project root:
    python src/data/load_data.py
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


RAW_DATA_DIR = Path("data/raw")
REPORTS_DIR = Path("reports")
REPORT_PATH = REPORTS_DIR / "data_schema_summary.md"
BASE_TABLE = "application_train.csv"
TARGET_COLUMN = "TARGET"
CSV_ENCODINGS = ("utf-8", "latin1")

REQUIRED_RAW_FILES = [
    "application_train.csv",
    "HomeCredit_columns_description.csv",
    "bureau.csv",
    "bureau_balance.csv",
    "previous_application.csv",
    "installments_payments.csv",
    "POS_CASH_balance.csv",
    "credit_card_balance.csv",
]


@dataclass(frozen=True)
class CsvSchema:
    """Lightweight schema details for a raw CSV file."""

    file_name: str
    columns: list[str]

    @property
    def column_count(self) -> int:
        return len(self.columns)


def validate_required_files(raw_data_dir: Path = RAW_DATA_DIR) -> list[Path]:
    """Return required CSV paths or raise a helpful error listing missing files."""
    missing_files = [
        file_name
        for file_name in REQUIRED_RAW_FILES
        if not (raw_data_dir / file_name).is_file()
    ]

    if missing_files:
        missing_list = "\n".join(f"- {file_name}" for file_name in missing_files)
        raise FileNotFoundError(
            "Missing required raw data files under data/raw/:\n"
            f"{missing_list}\n\n"
            "Place the Home Credit CSV files in data/raw/ and rerun:\n"
            "python src/data/load_data.py"
        )

    return [raw_data_dir / file_name for file_name in REQUIRED_RAW_FILES]


def read_csv_schema(csv_path: Path) -> CsvSchema:
    """Read only the header row to avoid loading large auxiliary tables."""
    header = read_csv_with_encoding_fallback(csv_path, nrows=0)
    return CsvSchema(file_name=csv_path.name, columns=header.columns.tolist())


def load_base_table(raw_data_dir: Path = RAW_DATA_DIR) -> pd.DataFrame:
    """Load application_train.csv, the base modeling table for this project."""
    base_path = raw_data_dir / BASE_TABLE
    return read_csv_with_encoding_fallback(base_path)


def read_csv_with_encoding_fallback(csv_path: Path, **kwargs: object) -> pd.DataFrame:
    """Read a CSV with a small encoding fallback for source metadata files."""
    last_error: UnicodeDecodeError | None = None

    for encoding in CSV_ENCODINGS:
        try:
            return pd.read_csv(csv_path, encoding=encoding, **kwargs)
        except UnicodeDecodeError as exc:
            last_error = exc

    raise UnicodeDecodeError(
        last_error.encoding if last_error else "unknown",
        last_error.object if last_error else b"",
        last_error.start if last_error else 0,
        last_error.end if last_error else 0,
        f"Could not read {csv_path} with encodings: {', '.join(CSV_ENCODINGS)}",
    )


def summarize_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Build a missing-value summary sorted by most missing values first."""
    missing_count = df.isna().sum()
    missing_percent = (missing_count / len(df) * 100).round(2)

    return (
        pd.DataFrame(
            {
                "column": missing_count.index,
                "missing_count": missing_count.values,
                "missing_percent": missing_percent.values,
                "dtype": df.dtypes.astype(str).values,
            }
        )
        .sort_values(["missing_count", "column"], ascending=[False, True])
        .reset_index(drop=True)
    )


def summarize_target(df: pd.DataFrame) -> pd.DataFrame:
    """Return TARGET class counts and percentages."""
    if TARGET_COLUMN not in df.columns:
        raise ValueError(
            f"Expected target column '{TARGET_COLUMN}' was not found in {BASE_TABLE}."
        )

    counts = df[TARGET_COLUMN].value_counts(dropna=False).sort_index()
    percentages = (counts / len(df) * 100).round(2)

    return pd.DataFrame(
        {
            TARGET_COLUMN: counts.index.astype(str),
            "count": counts.values,
            "percent": percentages.values,
        }
    )


def summarize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Return counts of pandas data types in the base table."""
    dtype_counts = df.dtypes.astype(str).value_counts().sort_index()
    return pd.DataFrame(
        {
            "dtype": dtype_counts.index,
            "column_count": dtype_counts.values,
        }
    )


def markdown_table(df: pd.DataFrame) -> str:
    """Render a pandas DataFrame as a GitHub-flavored markdown table."""
    if df.empty:
        return "_No rows to display._"

    safe_df = df.fillna("").astype(str)
    headers = safe_df.columns.tolist()
    header_row = "| " + " | ".join(headers) + " |"
    separator_row = "| " + " | ".join("---" for _ in headers) + " |"
    data_rows = [
        "| " + " | ".join(row) + " |"
        for row in safe_df.itertuples(index=False, name=None)
    ]
    return "\n".join([header_row, separator_row, *data_rows])


def build_markdown_report(
    base_df: pd.DataFrame,
    schemas: list[CsvSchema],
    target_summary: pd.DataFrame,
    missing_summary: pd.DataFrame,
    dtype_summary: pd.DataFrame,
) -> str:
    """Create the data schema summary report content."""
    schema_rows = pd.DataFrame(
        {
            "file": [schema.file_name for schema in schemas],
            "column_count": [schema.column_count for schema in schemas],
            "first_columns": [", ".join(schema.columns[:8]) for schema in schemas],
        }
    )

    column_schema = pd.DataFrame(
        {
            "column": base_df.columns,
            "dtype": base_df.dtypes.astype(str).values,
            "missing_count": base_df.isna().sum().values,
            "missing_percent": (base_df.isna().sum().values / len(base_df) * 100).round(2),
        }
    )

    top_missing = missing_summary.head(30)

    return "\n".join(
        [
            "# Data Schema Summary",
            "",
            "This report is generated from local raw CSV files under `data/raw/`.",
            "Raw data files are read only and are not modified by the loader.",
            "",
            "## Required File Check",
            "",
            markdown_table(schema_rows),
            "",
            "## Base Table",
            "",
            f"- Base table: `{BASE_TABLE}`",
            f"- Shape: `{base_df.shape[0]:,}` rows x `{base_df.shape[1]:,}` columns",
            f"- Target column detected: `{TARGET_COLUMN}`",
            "",
            "## Target Distribution",
            "",
            markdown_table(target_summary),
            "",
            "## Data Type Summary",
            "",
            markdown_table(dtype_summary),
            "",
            "## Top Missing-Value Columns",
            "",
            markdown_table(top_missing),
            "",
            "## Full Base Table Schema",
            "",
            markdown_table(column_schema),
            "",
        ]
    )


def print_console_summary(
    base_df: pd.DataFrame,
    target_summary: pd.DataFrame,
    missing_summary: pd.DataFrame,
    dtype_summary: pd.DataFrame,
    report_path: Path = REPORT_PATH,
) -> None:
    """Print a concise summary for the VS Code terminal."""
    print("Home Credit data validation complete.")
    print(f"Dataset shape: {base_df.shape[0]:,} rows x {base_df.shape[1]:,} columns")
    print(f"Number of columns: {base_df.shape[1]:,}")
    print(f"Target column detected: {TARGET_COLUMN}")
    print("\nTarget distribution:")
    print(target_summary.to_string(index=False))
    print("\nData types summary:")
    print(dtype_summary.to_string(index=False))
    print("\nMissing-value summary, top 10 columns:")
    print(missing_summary.head(10).to_string(index=False))
    print(f"\nMarkdown report saved to: {report_path}")


def main() -> None:
    """CLI entry point for raw data validation and schema reporting."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    required_paths = validate_required_files()
    schemas = [read_csv_schema(path) for path in required_paths]
    base_df = load_base_table()

    target_summary = summarize_target(base_df)
    missing_summary = summarize_missing_values(base_df)
    dtype_summary = summarize_dtypes(base_df)

    report = build_markdown_report(
        base_df=base_df,
        schemas=schemas,
        target_summary=target_summary,
        missing_summary=missing_summary,
        dtype_summary=dtype_summary,
    )
    REPORT_PATH.write_text(report, encoding="utf-8")

    print_console_summary(
        base_df=base_df,
        target_summary=target_summary,
        missing_summary=missing_summary,
        dtype_summary=dtype_summary,
    )


if __name__ == "__main__":
    main()
