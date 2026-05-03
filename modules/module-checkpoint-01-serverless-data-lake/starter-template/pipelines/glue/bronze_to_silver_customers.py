"""
AWS Glue ETL Job: Bronze to Silver - Customers Processing - STARTER TEMPLATE
Similar to orders processing but for customer dimension data

TODO SECTIONS:
1. Read from Bronze catalog
2. Handle nested JSON structures (address fields)
3. Apply data quality checks (email validation, etc.)
4. Standardize names and contact info
5. Write to Silver without time partitions (slowly changing dimension)
"""

from pyspark.sql import DataFrame
from awsglue.transforms import *
from awsglue.context import GlueContext


def read_bronze_customers(glue_context: GlueContext, database: str, table: str) -> DataFrame:
    """Read customers from Bronze layer"""
    # TODO: Similar to orders - read from catalog
    # dynamic_frame = glue_context.create_dynamic_frame.from_catalog(...)
    # df = dynamic_frame.toDF()
    return None  # TODO: Implement


def flatten_nested_fields(df: DataFrame) -> DataFrame:
    """
    Flatten nested JSON structures like address

    TODO: If address is a struct with city, country, postal_code:
    - Extract nested fields: col('address.city').alias('city')
    - Or use pyspark.sql.functions.struct operations
    """
    # TODO: Flatten address struct
    # df = df.withColumn('city', col('address.city'))
    # df = df.withColumn('country', col('address.country'))
    # df = df.withColumn('postal_code', col('address.postal_code'))
    return df  # TODO: Implement


def apply_customer_quality_checks(df: DataFrame) -> DataFrame:
    """Apply customer-specific validation"""
    # TODO: Quality checks:
    # 1. customer_id not null
    # 2. email matches pattern (contains @ and .)
    # 3. Remove duplicates by customer_id (keep most recent)

    # TODO: Email validation
    # df = df.filter(col('email').contains('@'))
    # df = df.filter(col('email').contains('.'))

    # TODO: Deduplicate
    # window = Window.partitionBy('customer_id').orderBy(col('registration_date').desc())
    # df = df.withColumn('row_num', row_number().over(window))
    # df = df.filter(col('row_num') == 1).drop('row_num')

    return df  # TODO: Implement


def standardize_customer_data(df: DataFrame) -> DataFrame:
    """Standardize customer information"""
    # TODO: Standardization:
    # - Names to title case
    # - Email to lowercase
    # - Phone number formatting
    # - Country codes standardization

    # df = df.withColumn('first_name', initcap(trim(col('first_name'))))
    # df = df.withColumn('last_name', initcap(trim(col('last_name'))))
    # df = df.withColumn('email', lower(trim(col('email'))))

    return df  # TODO: Implement


def write_to_silver(glue_context: GlueContext, df: DataFrame, target_s3_path: str):
    """
    Write to Silver without time partitions (dimension table)

    TODO: Customers are a dimension table, consider:
    - No time partitioning (or partition by country/region)
    - Overwrite mode or merge/upsert strategy
    - Consider storing history (SCD Type 2) if needed
    """
    # TODO: Write without time partitions or partition by country
    # dynamic_frame = DynamicFrame.fromDF(df, glue_context, "customers_silver")
    # glue_context.write_dynamic_frame.from_options(...)
    pass  # TODO: Implement


def main():
    """Main ETL execution for customers"""
    # TODO: Initialize Glue context
    # TODO: Read from Bronze
    # TODO: Flatten nested fields
    # TODO: Apply quality checks
    # TODO: Standardize data
    # TODO: Write to Silver
    # TODO: Commit job
    pass  # TODO: Implement


if __name__ == "__main__":
    main()
