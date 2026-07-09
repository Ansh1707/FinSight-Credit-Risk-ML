"""PySpark feature engineering for the Home Credit risk dataset.

Run from the project root after activating the project virtual environment:
    python src/features/pyspark_feature_engineering.py

For a quick smoke test on smaller data:
    python src/features/pyspark_feature_engineering.py --debug-limit 5000
"""

from __future__ import annotations

import argparse
from pathlib import Path

from pyspark.ml import Pipeline
from pyspark.ml.feature import StringIndexer
from pyspark import StorageLevel
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


RAW_DATA_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
REPORTS_DIR = Path("reports")
OUTPUT_PARQUET_PATH = PROCESSED_DIR / "model_features.parquet"
REPORT_PATH = REPORTS_DIR / "feature_engineering_summary.md"

REQUIRED_FILES = [
    "application_train.csv",
    "bureau.csv",
    "bureau_balance.csv",
    "previous_application.csv",
    "installments_payments.csv",
    "POS_CASH_balance.csv",
    "credit_card_balance.csv",
]

BASE_CATEGORICAL_COLUMNS = [
    "NAME_CONTRACT_TYPE",
    "CODE_GENDER",
    "FLAG_OWN_CAR",
    "FLAG_OWN_REALTY",
    "NAME_TYPE_SUITE",
    "NAME_INCOME_TYPE",
    "NAME_EDUCATION_TYPE",
    "NAME_FAMILY_STATUS",
    "NAME_HOUSING_TYPE",
    "OCCUPATION_TYPE",
    "ORGANIZATION_TYPE",
]

BASE_NUMERIC_COLUMNS = [
    "CNT_CHILDREN",
    "AMT_INCOME_TOTAL",
    "AMT_CREDIT",
    "AMT_ANNUITY",
    "AMT_GOODS_PRICE",
    "REGION_POPULATION_RELATIVE",
    "DAYS_BIRTH",
    "DAYS_EMPLOYED",
    "DAYS_REGISTRATION",
    "DAYS_ID_PUBLISH",
    "OWN_CAR_AGE",
    "CNT_FAM_MEMBERS",
    "REGION_RATING_CLIENT",
    "REGION_RATING_CLIENT_W_CITY",
    "HOUR_APPR_PROCESS_START",
    "EXT_SOURCE_1",
    "EXT_SOURCE_2",
    "EXT_SOURCE_3",
    "OBS_30_CNT_SOCIAL_CIRCLE",
    "DEF_30_CNT_SOCIAL_CIRCLE",
    "OBS_60_CNT_SOCIAL_CIRCLE",
    "DEF_60_CNT_SOCIAL_CIRCLE",
    "DAYS_LAST_PHONE_CHANGE",
]

AGGREGATED_FEATURES = [
    "bureau_credit_count",
    "bureau_active_credit_count",
    "bureau_closed_credit_count",
    "bureau_overdue_credit_count",
    "bureau_credit_day_overdue_max",
    "bureau_days_credit_mean",
    "bureau_credit_sum_mean",
    "bureau_credit_debt_sum",
    "bureau_credit_debt_to_credit_ratio",
    "bureau_balance_month_count",
    "bureau_balance_late_status_count",
    "previous_application_count",
    "previous_approved_count",
    "previous_refused_count",
    "previous_credit_mean",
    "previous_application_mean",
    "previous_down_payment_mean",
    "previous_days_decision_mean",
    "installment_payment_count",
    "installment_late_payment_count",
    "installment_avg_payment_delay_days",
    "installment_max_payment_delay_days",
    "installment_avg_payment_ratio",
    "pos_cash_month_count",
    "pos_cash_late_count",
    "pos_cash_max_dpd_def",
    "pos_cash_avg_installments_future",
    "credit_card_month_count",
    "credit_card_avg_balance",
    "credit_card_max_balance",
    "credit_card_avg_drawings",
    "credit_card_max_dpd",
]

DERIVED_FEATURES = [
    "loan_to_income_ratio",
    "credit_to_income_ratio",
    "annuity_to_income_ratio",
    "annuity_to_credit_ratio",
    "goods_price_to_credit_ratio",
    "employment_years",
    "age_years",
    "external_score_mean",
    "external_score_std",
    "missing_value_count",
]


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Build PySpark model-ready features.")
    parser.add_argument(
        "--debug-limit",
        type=int,
        default=None,
        help="Optional row limit for application_train.csv during local smoke tests.",
    )
    return parser.parse_args()


def validate_required_files() -> None:
    """Raise a helpful error if required raw CSV files are missing."""
    missing_files = [
        file_name for file_name in REQUIRED_FILES if not (RAW_DATA_DIR / file_name).is_file()
    ]
    if missing_files:
        missing_list = "\n".join(f"- {file_name}" for file_name in missing_files)
        raise FileNotFoundError(
            "Missing required raw data files under data/raw/:\n"
            f"{missing_list}\n\n"
            "Place the Home Credit files in data/raw/ and rerun this script."
        )


def create_spark_session() -> SparkSession:
    """Create a local Spark session suitable for VS Code runs."""
    return (
        SparkSession.builder.appName("FinSightFeatureEngineering")
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.driver.memory", "4g")
        .config("spark.driver.extraJavaOptions", "-XX:ReservedCodeCacheSize=256m")
        .config("spark.executor.extraJavaOptions", "-XX:ReservedCodeCacheSize=256m")
        .getOrCreate()
    )


def read_csv(spark: SparkSession, file_name: str) -> DataFrame:
    """Read a raw CSV file with inferred schema."""
    return (
        spark.read.option("header", True)
        .option("inferSchema", True)
        .csv((RAW_DATA_DIR / file_name).as_posix())
    )


def safe_divide(numerator: F.Column, denominator: F.Column) -> F.Column:
    """Return numerator / denominator only when the denominator is usable."""
    return F.when(denominator.isNull() | (denominator == 0), F.lit(None)).otherwise(
        numerator / denominator
    )


def add_base_features(application_df: DataFrame) -> DataFrame:
    """Create applicant-level lending-risk features from application_train.csv."""
    missing_count_expr = sum(
        F.when(F.col(column_name).isNull(), F.lit(1)).otherwise(F.lit(0))
        for column_name in application_df.columns
    )

    ext_scores = [F.col("EXT_SOURCE_1"), F.col("EXT_SOURCE_2"), F.col("EXT_SOURCE_3")]
    ext_non_null_count = sum(
        F.when(score.isNotNull(), F.lit(1)).otherwise(F.lit(0)) for score in ext_scores
    )
    ext_sum = sum(F.coalesce(score, F.lit(0.0)) for score in ext_scores)
    ext_mean = safe_divide(ext_sum, ext_non_null_count)
    ext_variance = safe_divide(
        sum(
            F.when(score.isNotNull(), F.pow(score - ext_mean, 2)).otherwise(F.lit(0.0))
            for score in ext_scores
        ),
        ext_non_null_count,
    )

    return (
        application_df.withColumn("missing_value_count", missing_count_expr)
        .withColumn(
            "loan_to_income_ratio",
            safe_divide(F.col("AMT_CREDIT"), F.col("AMT_INCOME_TOTAL")),
        )
        .withColumn(
            "credit_to_income_ratio",
            safe_divide(F.col("AMT_CREDIT"), F.col("AMT_INCOME_TOTAL")),
        )
        .withColumn(
            "annuity_to_income_ratio",
            safe_divide(F.col("AMT_ANNUITY"), F.col("AMT_INCOME_TOTAL")),
        )
        .withColumn(
            "annuity_to_credit_ratio",
            safe_divide(F.col("AMT_ANNUITY"), F.col("AMT_CREDIT")),
        )
        .withColumn(
            "goods_price_to_credit_ratio",
            safe_divide(F.col("AMT_GOODS_PRICE"), F.col("AMT_CREDIT")),
        )
        .withColumn("age_years", (-F.col("DAYS_BIRTH") / F.lit(365.25)))
        .withColumn(
            "employment_years",
            F.when(F.col("DAYS_EMPLOYED") == 365243, F.lit(None)).otherwise(
                -F.col("DAYS_EMPLOYED") / F.lit(365.25)
            ),
        )
        .withColumn("external_score_mean", ext_mean)
        .withColumn("external_score_std", F.sqrt(ext_variance))
    )


def aggregate_bureau(bureau_df: DataFrame) -> DataFrame:
    """Aggregate bureau credit history to applicant level."""
    return bureau_df.groupBy("SK_ID_CURR").agg(
        F.count("*").alias("bureau_credit_count"),
        F.sum(F.when(F.col("CREDIT_ACTIVE") == "Active", 1).otherwise(0)).alias(
            "bureau_active_credit_count"
        ),
        F.sum(F.when(F.col("CREDIT_ACTIVE") == "Closed", 1).otherwise(0)).alias(
            "bureau_closed_credit_count"
        ),
        F.sum(F.when(F.col("CREDIT_DAY_OVERDUE") > 0, 1).otherwise(0)).alias(
            "bureau_overdue_credit_count"
        ),
        F.max("CREDIT_DAY_OVERDUE").alias("bureau_credit_day_overdue_max"),
        F.avg("DAYS_CREDIT").alias("bureau_days_credit_mean"),
        F.avg("AMT_CREDIT_SUM").alias("bureau_credit_sum_mean"),
        F.sum("AMT_CREDIT_SUM_DEBT").alias("bureau_credit_debt_sum"),
        safe_divide(
            F.sum("AMT_CREDIT_SUM_DEBT"), F.sum("AMT_CREDIT_SUM")
        ).alias("bureau_credit_debt_to_credit_ratio"),
    )


def aggregate_bureau_balance(bureau_df: DataFrame, bureau_balance_df: DataFrame) -> DataFrame:
    """Aggregate bureau balance status history to applicant level."""
    bureau_keys = bureau_df.select("SK_ID_CURR", "SK_ID_BUREAU")
    return (
        bureau_balance_df.join(bureau_keys, on="SK_ID_BUREAU", how="inner")
        .groupBy("SK_ID_CURR")
        .agg(
            F.count("*").alias("bureau_balance_month_count"),
            F.sum(F.when(F.col("STATUS").isin("1", "2", "3", "4", "5"), 1).otherwise(0)).alias(
                "bureau_balance_late_status_count"
            ),
        )
    )


def aggregate_previous_applications(previous_df: DataFrame) -> DataFrame:
    """Aggregate previous applications to applicant level."""
    return previous_df.groupBy("SK_ID_CURR").agg(
        F.count("*").alias("previous_application_count"),
        F.sum(F.when(F.col("NAME_CONTRACT_STATUS") == "Approved", 1).otherwise(0)).alias(
            "previous_approved_count"
        ),
        F.sum(F.when(F.col("NAME_CONTRACT_STATUS") == "Refused", 1).otherwise(0)).alias(
            "previous_refused_count"
        ),
        F.avg("AMT_CREDIT").alias("previous_credit_mean"),
        F.avg("AMT_APPLICATION").alias("previous_application_mean"),
        F.avg("AMT_DOWN_PAYMENT").alias("previous_down_payment_mean"),
        F.avg("DAYS_DECISION").alias("previous_days_decision_mean"),
    )


def aggregate_installments(installments_df: DataFrame) -> DataFrame:
    """Aggregate installment payment behavior to applicant level."""
    enriched = installments_df.withColumn(
        "payment_delay_days",
        F.col("DAYS_ENTRY_PAYMENT") - F.col("DAYS_INSTALMENT"),
    ).withColumn(
        "payment_ratio",
        safe_divide(F.col("AMT_PAYMENT"), F.col("AMT_INSTALMENT")),
    )

    return enriched.groupBy("SK_ID_CURR").agg(
        F.count("*").alias("installment_payment_count"),
        F.sum(F.when(F.col("payment_delay_days") > 0, 1).otherwise(0)).alias(
            "installment_late_payment_count"
        ),
        F.avg("payment_delay_days").alias("installment_avg_payment_delay_days"),
        F.max("payment_delay_days").alias("installment_max_payment_delay_days"),
        F.avg("payment_ratio").alias("installment_avg_payment_ratio"),
    )


def aggregate_pos_cash(pos_cash_df: DataFrame) -> DataFrame:
    """Aggregate POS cash balance behavior to applicant level."""
    return pos_cash_df.groupBy("SK_ID_CURR").agg(
        F.count("*").alias("pos_cash_month_count"),
        F.sum(F.when(F.col("SK_DPD_DEF") > 0, 1).otherwise(0)).alias("pos_cash_late_count"),
        F.max("SK_DPD_DEF").alias("pos_cash_max_dpd_def"),
        F.avg("CNT_INSTALMENT_FUTURE").alias("pos_cash_avg_installments_future"),
    )


def aggregate_credit_card(credit_card_df: DataFrame) -> DataFrame:
    """Aggregate credit card balance behavior to applicant level."""
    return credit_card_df.groupBy("SK_ID_CURR").agg(
        F.count("*").alias("credit_card_month_count"),
        F.avg("AMT_BALANCE").alias("credit_card_avg_balance"),
        F.max("AMT_BALANCE").alias("credit_card_max_balance"),
        F.avg("AMT_DRAWINGS_CURRENT").alias("credit_card_avg_drawings"),
        F.max("SK_DPD_DEF").alias("credit_card_max_dpd"),
    )


def join_feature_tables(base_df: DataFrame, aggregate_dfs: list[DataFrame]) -> DataFrame:
    """Join applicant-level aggregate tables to the base application table."""
    result = base_df
    for aggregate_df in aggregate_dfs:
        result = result.join(aggregate_df, on="SK_ID_CURR", how="left")
    return result


def prepare_model_columns(feature_df: DataFrame) -> tuple[DataFrame, list[str], list[str]]:
    """Fill missing values and add categorical index columns for modeling."""
    available_numeric_columns = [
        column_name
        for column_name in BASE_NUMERIC_COLUMNS + DERIVED_FEATURES + AGGREGATED_FEATURES
        if column_name in feature_df.columns
    ]
    available_categorical_columns = [
        column_name for column_name in BASE_CATEGORICAL_COLUMNS if column_name in feature_df.columns
    ]

    filled_df = feature_df.fillna(0, subset=available_numeric_columns)
    filled_df = filled_df.fillna("Missing", subset=available_categorical_columns)

    indexers = [
        StringIndexer(
            inputCol=column_name,
            outputCol=f"{column_name}_idx",
            handleInvalid="keep",
        )
        for column_name in available_categorical_columns
    ]

    if indexers:
        filled_df = Pipeline(stages=indexers).fit(filled_df).transform(filled_df)

    indexed_columns = [f"{column_name}_idx" for column_name in available_categorical_columns]
    selected_columns = (
        ["SK_ID_CURR", "TARGET"]
        + available_numeric_columns
        + indexed_columns
    )

    return filled_df.select(*selected_columns), available_numeric_columns, indexed_columns


def build_report(
    row_count: int,
    column_count: int,
    numeric_columns: list[str],
    indexed_columns: list[str],
    debug_limit: int | None,
) -> str:
    """Build a markdown summary of the feature engineering run."""
    mode_note = (
        f"Debug mode used with application row limit `{debug_limit:,}`."
        if debug_limit
        else "Full mode used; all rows from `application_train.csv` were processed."
    )

    return "\n".join(
        [
            "# Feature Engineering Summary",
            "",
            "This report describes the PySpark feature engineering pipeline. Raw data was "
            "read from `data/raw/` and was not modified.",
            "",
            "## Run Scope",
            "",
            f"- {mode_note}",
            f"- Final dataset shape: `{row_count:,}` rows x `{column_count:,}` columns",
            f"- Output Parquet: `{OUTPUT_PARQUET_PATH.as_posix()}`",
            "- Model training: not performed in this phase.",
            "",
            "## Source Tables",
            "",
            "- `application_train.csv` as the base applicant table",
            "- `bureau.csv` aggregated to `SK_ID_CURR`",
            "- `bureau_balance.csv` joined through bureau IDs and aggregated to `SK_ID_CURR`",
            "- `previous_application.csv` aggregated to `SK_ID_CURR`",
            "- `installments_payments.csv` aggregated to `SK_ID_CURR`",
            "- `POS_CASH_balance.csv` aggregated to `SK_ID_CURR`",
            "- `credit_card_balance.csv` aggregated to `SK_ID_CURR`",
            "",
            "## Created Lending-Risk Features",
            "",
            *[f"- `{column_name}`" for column_name in DERIVED_FEATURES + AGGREGATED_FEATURES],
            "",
            "## Missing-Value Handling",
            "",
            "- Numeric feature nulls were filled with `0` after deriving `missing_value_count`.",
            "- Selected categorical nulls were filled with `Missing` before indexing.",
            "- The raw files were not modified.",
            "",
            "## Prepared Feature Columns",
            "",
            f"- Numeric/model columns: `{len(numeric_columns):,}`",
            f"- Encoded categorical index columns: `{len(indexed_columns):,}`",
            "",
            "### Encoded Categorical Columns",
            "",
            *[f"- `{column_name}`" for column_name in indexed_columns],
            "",
        ]
    )


def run_feature_engineering(debug_limit: int | None = None) -> tuple[int, int, list[str], list[str]]:
    """Run the PySpark feature engineering pipeline and save the model-ready Parquet."""
    validate_required_files()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    spark = create_spark_session()
    try:
        application_df = read_csv(spark, "application_train.csv")
        if debug_limit:
            application_df = application_df.limit(debug_limit)

        application_features = add_base_features(application_df)
        bureau_df = read_csv(spark, "bureau.csv")

        aggregate_dfs = [
            aggregate_bureau(bureau_df),
            aggregate_bureau_balance(bureau_df, read_csv(spark, "bureau_balance.csv")),
            aggregate_previous_applications(read_csv(spark, "previous_application.csv")),
            aggregate_installments(read_csv(spark, "installments_payments.csv")),
            aggregate_pos_cash(read_csv(spark, "POS_CASH_balance.csv")),
            aggregate_credit_card(read_csv(spark, "credit_card_balance.csv")),
        ]

        joined_features = join_feature_tables(application_features, aggregate_dfs)
        model_features, numeric_columns, indexed_columns = prepare_model_columns(joined_features)
        model_features = model_features.persist(StorageLevel.MEMORY_AND_DISK)

        row_count = model_features.count()
        column_count = len(model_features.columns)
        model_features.write.mode("overwrite").parquet(OUTPUT_PARQUET_PATH.as_posix())
        REPORT_PATH.write_text(
            build_report(
                row_count=row_count,
                column_count=column_count,
                numeric_columns=numeric_columns,
                indexed_columns=indexed_columns,
                debug_limit=debug_limit,
            ),
            encoding="utf-8",
        )

        return row_count, column_count, numeric_columns, indexed_columns
    finally:
        spark.stop()


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    row_count, column_count, numeric_columns, indexed_columns = run_feature_engineering(
        debug_limit=args.debug_limit
    )

    print("PySpark feature engineering complete.")
    print(f"Final dataset shape: {row_count:,} rows x {column_count:,} columns")
    print(f"Parquet saved to: {OUTPUT_PARQUET_PATH}")
    print(f"Summary report saved to: {REPORT_PATH}")
    print(f"Numeric/model columns prepared: {len(numeric_columns):,}")
    print(f"Categorical index columns prepared: {len(indexed_columns):,}")


if __name__ == "__main__":
    main()
