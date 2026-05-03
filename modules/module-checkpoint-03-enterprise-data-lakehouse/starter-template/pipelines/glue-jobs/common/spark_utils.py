"""
==============================================
Spark Utilities for Data Lakehouse Pipelines
==============================================
Common utility functions for PySpark ETL jobs.

Purpose:
- Reusable data transformation functions
- Data validation utilities
- Logging helpers
- Schema management
- Error handling utilities

Author: [Your Name]
Date: [Date]
==============================================
"""

import logging
from typing import List, Dict, Any
from datetime import date
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import (
    StructType
)

# ==============================================
# Logging Utilities
# ==============================================

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get configured logger instance.

    Args:
        name: Logger name (typically __name__)
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    # TODO: Configure logger with CloudWatch handler
    # - Set up formatting
    # - Add CloudWatch Logs handler
    # - Configure log level

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # TODO: Add handler if not already added
    # if not logger.handlers:
    #     handler = logging.StreamHandler()
    #     formatter = logging.Formatter(
    #         '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    #     )
    #     handler.setFormatter(formatter)
    #     logger.addHandler(handler)

    return logger

def log_dataframe_info(df: DataFrame, name: str = "DataFrame") -> None:
    """
    Log useful information about a DataFrame.

    Args:
        df: DataFrame to log info about
        name: Name to identify the DataFrame
    """
    # TODO: Log DataFrame statistics
    # - Row count
    # - Column count
    # - Schema
    # - Sample data

    print(f"=== {name} Info ===")
    # print(f"Row count: {df.count()}")
    # print(f"Column count: {len(df.columns)}")
    # print(f"Columns: {df.columns}")
    # print("Schema:")
    # df.printSchema()
    # print("Sample (5 rows):")
    # df.show(5, truncate=False)
    print("=" * (len(name) + 12))

# ==============================================
# Data Validation Utilities
# ==============================================

def validate_schema(df: DataFrame, expected_schema: StructType) -> bool:
    """
    Validate if DataFrame schema matches expected schema.

    Args:
        df: DataFrame to validate
        expected_schema: Expected schema

    Returns:
        True if schema matches, False otherwise
    """
    # TODO: Implement schema validation
    # - Compare field names
    # - Compare data types
    # - Handle nullable differences

    # if df.schema == expected_schema:
    #     print("Schema validation passed")
    #     return True
    # else:
    #     print("Schema validation failed")
    #     print(f"Expected: {expected_schema}")
    #     print(f"Actual: {df.schema}")
    #     return False

    return True

def validate_email(email_col: str) -> bool:
    """
    Validate email address format.

    Args:
        email_col: Column containing email addresses

    Returns:
        Boolean expression for email validation
    """
    # TODO: Implement email validation regex
    # email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    # return col(email_col).rlike(email_pattern)

    pass

def validate_phone(phone_col: str, country_code: str = "US") -> bool:
    """
    Validate phone number format.

    Args:
        phone_col: Column containing phone numbers
        country_code: Country code for validation (default: US)

    Returns:
        Boolean expression for phone validation
    """
    # TODO: Implement phone validation based on country
    # US format: (XXX) XXX-XXXX or XXX-XXX-XXXX
    # if country_code == "US":
    #     phone_pattern = r'^\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$'
    #     return col(phone_col).rlike(phone_pattern)

    pass

def validate_date_range(date_col: str, min_date: date, max_date: date) -> bool:
    """
    Validate if dates fall within specified range.

    Args:
        date_col: Column containing dates
        min_date: Minimum valid date
        max_date: Maximum valid date

    Returns:
        Boolean expression for date range validation
    """
    # TODO: Implement date range validation
    # return (col(date_col) >= lit(min_date)) & (col(date_col) <= lit(max_date))

    pass

def check_data_quality(df: DataFrame, rules: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check data quality based on defined rules.

    Args:
        df: DataFrame to check
        rules: Dictionary of quality rules
            Example: {
                "completeness": {"required_columns": ["id", "name"]},
                "uniqueness": {"unique_columns": ["id"]},
                "validity": {"email": "email_column"}
            }

    Returns:
        Dictionary with quality check results
    """
    # TODO: Implement comprehensive data quality checks
    # - Completeness: Check for nulls in required fields
    # - Uniqueness: Check for duplicates
    # - Validity: Validate formats (email, phone, etc.)
    # - Accuracy: Check value ranges
    # - Consistency: Cross-field validations

    results = {
        "passed": True,
        "checks": {}
    }

    # TODO: Implement each check type

    return results

# ==============================================
# Data Transformation Utilities
# ==============================================

def standardize_string(df: DataFrame, column: str,
                       case: str = "lower", trim_ws: bool = True) -> DataFrame:
    """
    Standardize string column.

    Args:
        df: Input DataFrame
        column: Column name to standardize
        case: Case transformation ('lower', 'upper', 'title', 'none')
        trim_ws: Whether to trim whitespace

    Returns:
        DataFrame with standardized column
    """
    # TODO: Implement string standardization
    # if trim_ws:
    #     df = df.withColumn(column, trim(col(column)))

    # if case == "lower":
    #     df = df.withColumn(column, lower(col(column)))
    # elif case == "upper":
    #     df = df.withColumn(column, upper(col(column)))
    # elif case == "title":
    #     # Implement title case
    #     pass

    return df

def remove_special_characters(df: DataFrame, column: str,
                              keep_pattern: str = "[a-zA-Z0-9 ]") -> DataFrame:
    """
    Remove special characters from string column.

    Args:
        df: Input DataFrame
        column: Column name
        keep_pattern: Regex pattern of characters to keep

    Returns:
        DataFrame with cleaned column
    """
    # TODO: Implement special character removal
    # df = df.withColumn(
    #     column,
    #     regexp_replace(col(column), f"[^{keep_pattern}]", "")
    # )

    return df

def standardize_date_format(df: DataFrame, column: str,
                           input_format: str, output_format: str = "yyyy-MM-dd") -> DataFrame:
    """
    Standardize date format.

    Args:
        df: Input DataFrame
        column: Date column name
        input_format: Current date format
        output_format: Desired date format

    Returns:
        DataFrame with standardized date
    """
    # TODO: Implement date formatting
    # df = df.withColumn(
    #     column,
    #     to_date(col(column), input_format)
    # )

    return df

def fill_missing_values(df: DataFrame, strategy: Dict[str, Any]) -> DataFrame:
    """
    Fill missing values based on strategy.

    Args:
        df: Input DataFrame
        strategy: Dict mapping columns to fill values/methods
            Example: {
                "age": {"method": "mean"},
                "city": {"value": "UNKNOWN"},
                "status": {"value": "ACTIVE"}
            }

    Returns:
        DataFrame with filled values
    """
    # TODO: Implement various fill strategies
    # - Fixed value
    # - Mean/median/mode
    # - Forward fill/backward fill
    # - Interpolation

    # for column, fill_config in strategy.items():
    #     if "value" in fill_config:
    #         df = df.fillna({column: fill_config["value"]})
    #     elif "method" in fill_config:
    #         method = fill_config["method"]
    #         if method == "mean":
    #             mean_val = df.agg({column: "mean"}).collect()[0][0]
    #             df = df.fillna({column: mean_val})

    return df

# ==============================================
# Key Generation Utilities
# ==============================================

def generate_surrogate_key(df: DataFrame, business_keys: List[str],
                          key_name: str = "surrogate_key") -> DataFrame:
    """
    Generate surrogate key from business keys.

    Args:
        df: Input DataFrame
        business_keys: List of columns forming business key
        key_name: Name for surrogate key column

    Returns:
        DataFrame with surrogate key added
    """
    # TODO: Generate surrogate key using hash
    # df = df.withColumn(
    #     key_name,
    #     md5(concat_ws("||", *[col(k) for k in business_keys]))
    # )

    return df

def generate_hash_key(df: DataFrame, columns: List[str],
                      algorithm: str = "md5") -> DataFrame:
    """
    Generate hash from specified columns for change detection.

    Args:
        df: Input DataFrame
        columns: List of columns to hash
        algorithm: Hash algorithm ('md5' or 'sha256')

    Returns:
        DataFrame with hash column added
    """
    # TODO: Generate hash for change detection
    # if algorithm == "md5":
    #     df = df.withColumn(
    #         "row_hash",
    #         md5(concat_ws("||", *[col(c) for c in columns]))
    #     )
    # elif algorithm == "sha256":
    #     df = df.withColumn(
    #         "row_hash",
    #         sha2(concat_ws("||", *[col(c) for c in columns]), 256)
    #     )

    return df

# ==============================================
# Performance Optimization Utilities
# ==============================================

def optimize_dataframe(df: DataFrame, num_partitions: int = None) -> DataFrame:
    """
    Optimize DataFrame for better performance.

    Args:
        df: Input DataFrame
        num_partitions: Target number of partitions (optional)

    Returns:
        Optimized DataFrame
    """
    # TODO: Implement optimization strategies
    # - Repartition for better parallelism
    # - Cache if used multiple times
    # - Coalesce to reduce small files

    # if num_partitions:
    #     df = df.repartition(num_partitions)
    # else:
    #     # Auto-optimize based on data size
    #     pass

    return df

def write_with_optimization(df: DataFrame, path: str,
                           format: str = "parquet",
                           partition_by: List[str] = None,
                           mode: str = "overwrite") -> None:
    """
    Write DataFrame with optimization settings.

    Args:
        df: DataFrame to write
        path: Output path
        format: Output format (parquet, delta, etc.)
        partition_by: Columns to partition by
        mode: Write mode (overwrite, append, etc.)
    """
    # TODO: Write with optimized settings
    # writer = df.write.mode(mode).format(format)

    # # Set optimization options
    # if format == "parquet":
    #     writer = writer.option("compression", "snappy")
    #     writer = writer.option("maxRecordsPerFile", 100000)

    # # Apply partitioning
    # if partition_by:
    #     writer = writer.partitionBy(*partition_by)

    # writer.save(path)

    pass

# ==============================================
# Error Handling Utilities
# ==============================================

def handle_bad_records(df: DataFrame, bad_records_path: str) -> DataFrame:
    """
    Separate and save bad records for review.

    Args:
        df: Input DataFrame
        bad_records_path: Path to save bad records

    Returns:
        DataFrame with only good records
    """
    # TODO: Implement bad record handling
    # - Define rules for bad records
    # - Filter and save bad records
    # - Return clean DataFrame

    return df

def retry_on_failure(func, max_retries: int = 3, delay: int = 60):
    """
    Decorator to retry function on failure.

    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        delay: Delay between retries in seconds

    Returns:
        Wrapped function with retry logic
    """
    # TODO: Implement retry decorator
    # def wrapper(*args, **kwargs):
    #     for attempt in range(max_retries):
    #         try:
    #             return func(*args, **kwargs)
    #         except Exception as e:
    #             if attempt < max_retries - 1:
    #                 print(f"Attempt {attempt + 1} failed: {e}")
    #                 time.sleep(delay)
    #             else:
    #                 raise
    # return wrapper

    pass

# ==============================================
# Metadata Utilities
# ==============================================

def add_audit_columns(df: DataFrame, source_system: str = None) -> DataFrame:
    """
    Add standard audit columns to DataFrame.

    Args:
        df: Input DataFrame
        source_system: Source system identifier

    Returns:
        DataFrame with audit columns added
    """
    # TODO: Add audit columns
    # - created_timestamp
    # - updated_timestamp
    # - source_system
    # - batch_id
    # - created_by

    # df = df.withColumn("created_timestamp", current_timestamp())
    # df = df.withColumn("updated_timestamp", current_timestamp())

    # if source_system:
    #     df = df.withColumn("source_system", lit(source_system))

    return df

def get_catalog_metadata(database: str, table: str,
                        glue_client = None) -> Dict[str, Any]:
    """
    Get table metadata from Glue Data Catalog.

    Args:
        database: Database name
        table: Table name
        glue_client: Boto3 Glue client (optional)

    Returns:
        Dictionary with table metadata
    """
    # TODO: Retrieve catalog metadata using boto3
    # import boto3
    # if not glue_client:
    #     glue_client = boto3.client('glue')

    # try:
    #     response = glue_client.get_table(
    #         DatabaseName=database,
    #         Name=table
    #     )
    #     return response['Table']
    # except Exception as e:
    #     print(f"Error getting catalog metadata: {e}")
    #     return {}

    pass

# ==============================================
# Testing Utilities
# ==============================================

def create_test_dataframe(spark: SparkSession,
                         data: List[tuple],
                         schema: StructType) -> DataFrame:
    """
    Create test DataFrame from data and schema.

    Args:
        spark: SparkSession
        data: List of tuples with test data
        schema: Schema for the DataFrame

    Returns:
        Test DataFrame
    """
    # TODO: Create test DataFrame
    # df = spark.createDataFrame(data, schema)
    # return df

    pass

def compare_dataframes(df1: DataFrame, df2: DataFrame,
                      key_columns: List[str]) -> Dict[str, Any]:
    """
    Compare two DataFrames and return differences.

    Args:
        df1: First DataFrame
        df2: Second DataFrame
        key_columns: Columns to join on

    Returns:
        Dictionary with comparison results
    """
    # TODO: Implement DataFrame comparison
    # - Find records only in df1
    # - Find records only in df2
    # - Find changed records
    # - Return statistics

    results = {
        "only_in_df1": 0,
        "only_in_df2": 0,
        "changed": 0,
        "identical": 0
    }

    return results

# ==============================================
# USAGE EXAMPLES:
# ==============================================
"""
# Example 1: Logging
logger = get_logger(__name__)
logger.info("Starting ETL process")

# Example 2: Schema validation
expected_schema = StructType([
    StructField("id", IntegerType(), False),
    StructField("name", StringType(), True)
])
is_valid = validate_schema(df, expected_schema)

# Example 3: String standardization
df = standardize_string(df, "customer_name", case="title", trim_ws=True)

# Example 4: Surrogate key generation
df = generate_surrogate_key(df, ["customer_id", "product_id"], "sk_sales")

# Example 5: Data quality check
quality_rules = {
    "completeness": {"required_columns": ["id", "email"]},
    "uniqueness": {"unique_columns": ["id"]}
}
quality_results = check_data_quality(df, quality_rules)
"""

# ==============================================
# IMPLEMENTATION NOTES:
# ==============================================
# 1. Add type hints to all functions for better IDE support
# 2. Write unit tests for all utilities
# 3. Document usage examples for each function
# 4. Consider creating separate modules for different utility categories
# 5. Add performance benchmarks for critical functions
# 6. Keep utilities generic and reusable across projects
# 7. Version control this file and maintain changelog
# ==============================================
