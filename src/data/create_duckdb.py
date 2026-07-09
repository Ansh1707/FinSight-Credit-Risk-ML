"""Create a DuckDB analysis layer and run SQL business queries.

Run from the project root:
    python src/data/create_duckdb.py
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd


RAW_DATA_PATH = Path("data/raw/application_train.csv")
PROCESSED_DIR = Path("data/processed")
REPORTS_DIR = Path("reports")
SQL_DIR = Path("sql")
DUCKDB_PATH = PROCESSED_DIR / "finsight.duckdb"
REPORT_PATH = REPORTS_DIR / "sql_analysis_summary.md"
TABLE_NAME = "application_train"

QUERY_FILES = {
    "Default Rate by Income Bucket": SQL_DIR / "default_rate_by_income.sql",
    "Default Rate by Education Type": SQL_DIR / "default_rate_by_education.sql",
    "Default Rate by Credit Amount Bucket": SQL_DIR / "default_rate_by_credit_amount.sql",
    "Default Rate by Occupation Type": SQL_DIR / "default_rate_by_occupation.sql",
    "High-Risk Customer Segments": SQL_DIR / "high_risk_segments.sql",
}


def validate_inputs() -> None:
    """Validate required input files before opening DuckDB."""
    if not RAW_DATA_PATH.is_file():
        raise FileNotFoundError(
            "Missing data/raw/application_train.csv. "
            "Place the Home Credit base table under data/raw/ and rerun."
        )

    missing_queries = [path.as_posix() for path in QUERY_FILES.values() if not path.is_file()]
    if missing_queries:
        missing_list = "\n".join(f"- {path}" for path in missing_queries)
        raise FileNotFoundError(f"Missing SQL query files:\n{missing_list}")


def create_application_table(connection: duckdb.DuckDBPyConnection) -> None:
    """Create a local DuckDB table from the raw CSV without modifying raw data."""
    csv_path = RAW_DATA_PATH.as_posix()
    connection.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
    connection.execute(
        f"""
        CREATE TABLE {TABLE_NAME} AS
        SELECT *
        FROM read_csv_auto(
            '{csv_path}',
            header = true,
            sample_size = -1
        )
        """
    )


def run_sql_file(connection: duckdb.DuckDBPyConnection, sql_path: Path) -> pd.DataFrame:
    """Execute a saved SQL query and return a DataFrame."""
    query = sql_path.read_text(encoding="utf-8")
    return connection.execute(query).fetchdf()


def markdown_table(df: pd.DataFrame) -> str:
    """Render a DataFrame as a dependency-free markdown table."""
    if df.empty:
        return "_No rows returned._"

    safe_df = df.fillna("").astype(str)
    headers = safe_df.columns.tolist()
    rows = ["| " + " | ".join(headers) + " |"]
    rows.append("| " + " | ".join("---" for _ in headers) + " |")
    rows.extend(
        "| " + " | ".join(row) + " |"
        for row in safe_df.itertuples(index=False, name=None)
    )
    return "\n".join(rows)


def build_findings(results: dict[str, pd.DataFrame]) -> list[str]:
    """Create business-readable findings from actual SQL results."""
    income = results["Default Rate by Income Bucket"]
    education = results["Default Rate by Education Type"]
    credit = results["Default Rate by Credit Amount Bucket"]
    occupation = results["Default Rate by Occupation Type"]
    high_risk = results["High-Risk Customer Segments"]

    riskiest_income = income.sort_values("default_rate_percent", ascending=False).iloc[0]
    safest_income = income.sort_values("default_rate_percent", ascending=True).iloc[0]
    riskiest_education = education.iloc[0]
    riskiest_credit = credit.sort_values("default_rate_percent", ascending=False).iloc[0]
    riskiest_occupation = occupation.iloc[0]
    riskiest_segment = high_risk.iloc[0]

    return [
        (
            f"Income segmentation shows the highest default rate in the "
            f"{riskiest_income['income_bucket']} bucket at "
            f"{riskiest_income['default_rate_percent']}%, compared with "
            f"{safest_income['default_rate_percent']}% in {safest_income['income_bucket']}. "
            "This supports affordability-focused monitoring."
        ),
        (
            f"Education type has clear risk separation: "
            f"{riskiest_education['education_type']} has a "
            f"{riskiest_education['default_rate_percent']}% default rate across "
            f"{int(riskiest_education['applicant_count']):,} applicants."
        ),
        (
            f"Credit amount buckets are not monotonic; the highest bucket-level default rate is "
            f"{riskiest_credit['default_rate_percent']}% for "
            f"{riskiest_credit['credit_amount_bucket']}. Ticket size should be combined with "
            "income, annuity burden, and bureau behavior instead of used alone."
        ),
        (
            f"Occupation segmentation highlights {riskiest_occupation['occupation_type']} as "
            f"the highest-risk occupation group with a "
            f"{riskiest_occupation['default_rate_percent']}% default rate across "
            f"{int(riskiest_occupation['applicant_count']):,} applicants."
        ),
        (
            "The highest combined high-risk segment is "
            f"{riskiest_segment['income_segment']}, {riskiest_segment['credit_segment']}, "
            f"{riskiest_segment['education_type']}, {riskiest_segment['occupation_type']}, "
            f"gender {riskiest_segment['gender']}, with a "
            f"{riskiest_segment['default_rate_percent']}% default rate across "
            f"{int(riskiest_segment['applicant_count']):,} applicants. This is useful for "
            "portfolio monitoring and collections prioritization, not as a hard approval rule."
        ),
    ]


def build_report(results: dict[str, pd.DataFrame], findings: list[str]) -> str:
    """Build the markdown SQL analysis report."""
    sections = [
        "# SQL Analysis Summary",
        "",
        "This report is generated with DuckDB from `data/raw/application_train.csv`. "
        "Raw data is read only and is not modified.",
        "",
        "## Top Business Findings",
        "",
        *[f"{idx}. {finding}" for idx, finding in enumerate(findings, start=1)],
        "",
    ]

    for title, df in results.items():
        sections.extend(
            [
                f"## {title}",
                "",
                markdown_table(df),
                "",
            ]
        )

    sections.extend(
        [
            "## Notes",
            "",
            "- SQL outputs are descriptive business analysis, not model metrics.",
            "- Segment differences should guide feature engineering, validation, and monitoring.",
            "- No model training was performed in this phase.",
            "",
        ]
    )

    return "\n".join(sections)


def run_sql_analysis() -> tuple[dict[str, pd.DataFrame], list[str]]:
    """Create DuckDB database, execute SQL files, and save the markdown report."""
    validate_inputs()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(DUCKDB_PATH.as_posix()) as connection:
        create_application_table(connection)
        results = {
            title: run_sql_file(connection, sql_path)
            for title, sql_path in QUERY_FILES.items()
        }

    findings = build_findings(results)
    REPORT_PATH.write_text(build_report(results, findings), encoding="utf-8")
    return results, findings


def main() -> None:
    """CLI entry point for the SQL analysis phase."""
    results, findings = run_sql_analysis()

    print("DuckDB SQL analysis complete.")
    print(f"DuckDB database saved to: {DUCKDB_PATH}")
    print(f"Markdown report saved to: {REPORT_PATH}")
    print("\nSQL files executed:")
    for sql_path in QUERY_FILES.values():
        print(f"- {sql_path}")
    print("\nTop business findings:")
    for idx, finding in enumerate(findings, start=1):
        print(f"{idx}. {finding}")
    print("\nResult row counts:")
    for title, df in results.items():
        print(f"- {title}: {len(df)} rows")


if __name__ == "__main__":
    main()
