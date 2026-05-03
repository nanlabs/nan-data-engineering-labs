"""
AWS Glue ETL Job: Bronze to Silver - Orders Processing - STARTER TEMPLATE
Reads raw orders data from Bronze layer, applies transformations and data quality checks,
and writes cleaned data to Silver layer.

LEARNING OBJECTIVES:
- Read data from Glue Catalog tables
- Apply schema transformations with PySpark
- Implement data quality checks
- Write partitioned Parquet files
- Use Glue job bookmarks for incremental processing

TODO SECTIONS:
1. Read from Bronze layer using Glue Catalog
2. Apply schema mapping and type conversions
3. Implement data quality checks
4. Clean and transform data
5. Write to Silver layer with partitioning
"""

import sys
from pyspark.sql import DataFrame

from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext


def get_job_parameters():
    """
    Extract job parameters from Glue arguments

    TODO: Understand what parameters are needed:
    - JOB_NAME: Name of this Glue job
    - source_database: Bronze layer database name
    - source_table: Bronze orders table name
    - target_s3_path: S3 path for Silver layer output
    - target_database: Silver layer database name
    - target_table: Silver orders table name
    """
    args = getResolvedOptions(
        sys.argv,
        [
            'JOB_NAME',
            'source_database',
            'source_table',
            'target_s3_path',
            'target_database',
            'target_table'
        ]
    )
    return args


def read_bronze_orders(glue_context: GlueContext, database: str, table: str) -> DataFrame:
    """
    Read orders data from Bronze layer (Glue Catalog table)

    Args:
        glue_context: AWS Glue context
        database: Source database name
        table: Source table name

    Returns:
        Spark DataFrame with raw orders data
    """
    print(f"Reading from Bronze layer: {database}.{table}")

    # ===================================================================
    # TODO 1: Read from Glue Catalog
    # ===================================================================
    # HINT: Use glue_context.create_dynamic_frame.from_catalog()
    # This automatically handles job bookmarks for incremental processing
    # Reference: https://docs.aws.amazon.com/glue/latest/dg/aws-glue-api-crawler-pyspark-extensions-dynamic-frame.html

    try:
        # TODO: Read from catalog with job bookmark support
        # dynamic_frame = glue_context.create_dynamic_frame.from_catalog(
        #     database=database,
        #     table_name=table,
        #     transformation_ctx="read_bronze_orders"  # Important for bookmarks!
        # )

        # TODO: Convert DynamicFrame to DataFrame
        # df = dynamic_frame.toDF()

        # Placeholder - replace with actual implementation
        df = None  # TODO: Implement reading from catalog

        if df:
            row_count = df.count()
            print(f"Successfully read {row_count} records from Bronze")

        return df

    except Exception as e:
        print(f"ERROR: Failed to read Bronze orders data: {str(e)}")
        raise


def apply_schema_mapping(df: DataFrame) -> DataFrame:
    """
    Apply schema mapping to standardize column names and types

    Args:
        df: Input DataFrame from Bronze layer

    Returns:
        DataFrame with standardized schema
    """
    print("Applying schema mapping and standardization")

    # ===================================================================
    # TODO 2: Map and Cast Columns
    # ===================================================================
    # HINT: Use withColumn() and cast() to transform types
    # Common transformations:
    # - Rename columns if needed (withColumnRenamed)
    # - Convert dates to DateType
    # - Convert amounts to DoubleType
    # - Convert IDs to StringType
    # - Trim and standardize text fields

    # TODO: Cast order_date to DateType
    # df = df.withColumn('order_date', to_date(col('order_date')))

    # TODO: Cast numeric columns
    # df = df.withColumn('total_amount', col('total_amount').cast(DoubleType()))
    # df = df.withColumn('quantity', col('quantity').cast(IntegerType()))

    # TODO: Standardize text fields
    # df = df.withColumn('status', upper(trim(col('status'))))
    # df = df.withColumn('order_id', trim(col('order_id')))
    # df = df.withColumn('customer_id', trim(col('customer_id')))

    # Placeholder
    df_typed = df  # TODO: Apply transformations

    print(f"Schema mapping completed. Columns: {len(df_typed.columns)}")
    return df_typed


def apply_data_quality_checks(df: DataFrame) -> DataFrame:
    """
    Apply data quality checks and filter invalid records

    Args:
        df: Input DataFrame

    Returns:
        DataFrame with only valid records
    """
    print("Applying data quality checks")

    initial_count = df.count()

    # ===================================================================
    # TODO 3: Implement Data Quality Rules
    # ===================================================================
    # HINT: Use filter() to remove invalid records
    # Quality rules for orders:
    # 1. order_id must not be null or empty
    # 2. total_amount must be >= 0
    # 3. order_date must be valid and not in future
    # 4. status must be in valid list

    # TODO: Filter out null order_ids
    # df = df.filter(col('order_id').isNotNull())
    # df = df.filter(trim(col('order_id')) != '')

    # TODO: Filter out negative amounts
    # df = df.filter(col('total_amount') >= 0)

    # TODO: Filter out future dates
    # df = df.filter(col('order_date') <= current_timestamp())

    # TODO: Filter valid statuses
    # valid_statuses = ['PENDING', 'CONFIRMED', 'SHIPPED', 'DELIVERED', 'CANCELLED']
    # df = df.filter(col('status').isin(valid_statuses))

    # Placeholder
    df_valid = df  # TODO: Apply quality checks

    final_count = df_valid.count()
    rejected_count = initial_count - final_count

    print(f"Quality checks complete: {final_count} valid, {rejected_count} rejected")

    return df_valid


def enrich_orders_data(df: DataFrame) -> DataFrame:
    """
    Enrich orders data with calculated fields

    Args:
        df: Input DataFrame

    Returns:
        DataFrame with enriched fields
    """
    print("Enriching orders data")

    # ===================================================================
    # TODO 4: Add Calculated Columns
    # ===================================================================
    # HINT: Create derived fields that will be useful for analytics

    # TODO: Add processing timestamp
    # df = df.withColumn('processed_timestamp', current_timestamp())

    # TODO: Extract date components for partitioning and analytics
    # df = df.withColumn('year', year(col('order_date')))
    # df = df.withColumn('month', month(col('order_date')))
    # df = df.withColumn('day', dayofmonth(col('order_date')))

    # TODO: Add business logic columns
    # df = df.withColumn('is_high_value',
    #     when(col('total_amount') >= 100, True).otherwise(False))

    # TODO: Calculate days since order
    # df = df.withColumn('days_since_order',
    #     datediff(current_timestamp(), col('order_date')))

    # Placeholder
    df_enriched = df  # TODO: Add enrichments

    print(f"Enrichment complete. Total columns: {len(df_enriched.columns)}")
    return df_enriched


def write_to_silver(glue_context: GlueContext, df: DataFrame,
                    target_s3_path: str, target_database: str,
                    target_table: str):
    """
    Write DataFrame to Silver layer with partitioning

    Args:
        glue_context: AWS Glue context
        df: DataFrame to write
        target_s3_path: S3 output path
        target_database: Target database name
        target_table: Target table name
    """
    print(f"Writing to Silver layer: {target_s3_path}")

    # ===================================================================
    # TODO 5: Write Partitioned Parquet
    # ===================================================================
    # HINT: Convert DataFrame to DynamicFrame and use write_dynamic_frame
    # Partition by year, month for time-series queries

    try:
        # TODO: Convert DataFrame to DynamicFrame
        # dynamic_frame = DynamicFrame.fromDF(df, glue_context, "orders_silver")

        # TODO: Write to S3 with partitioning
        # HINT: Use glue_context.write_dynamic_frame.from_options()
        # Options:
        # - connection_type: "s3"
        # - format: "parquet"
        # - connection_options: {"path": target_s3_path, "partitionKeys": ["year", "month"]}
        # - format_options: {"compression": "snappy"}
        # - transformation_ctx: "write_silver_orders" (for bookmarks)

        # glue_context.write_dynamic_frame.from_options(
        #     frame=dynamic_frame,
        #     connection_type="s3",
        #     format="parquet",
        #     connection_options={
        #         "path": target_s3_path,
        #         "partitionKeys": ["year", "month"]
        #     },
        #     format_options={
        #         "compression": "snappy"
        #     },
        #     transformation_ctx="write_silver_orders"
        # )

        print(f"Successfully wrote {df.count()} records to Silver layer")

        # TODO: Update Glue Catalog (optional - crawler can do this too)
        # HINT: Use Boto3 Glue client to create/update table

    except Exception as e:
        print(f"ERROR: Failed to write to Silver layer: {str(e)}")
        raise


def main():
    """Main ETL job execution"""

    print("=" * 80)
    print("Starting Bronze to Silver - Orders ETL Job")
    print("=" * 80)

    # TODO: Initialize Glue context and job
    # HINT: Create SparkContext, GlueContext, and Job
    # args = get_job_parameters()
    # sc = SparkContext()
    # glue_context = GlueContext(sc)
    # spark = glue_context.spark_session
    # job = Job(glue_context)
    # job.init(args['JOB_NAME'], args)

    # Placeholder initialization
    args = None  # TODO: Get parameters
    glue_context = None  # TODO: Create GlueContext

    try:
        # Step 1: Read from Bronze
        # df_bronze = read_bronze_orders(
        #     glue_context,
        #     args['source_database'],
        #     args['source_table']
        # )

        # Step 2: Apply schema mapping
        # df_mapped = apply_schema_mapping(df_bronze)

        # Step 3: Data quality checks
        # df_quality = apply_data_quality_checks(df_mapped)

        # Step 4: Enrich data
        # df_enriched = enrich_orders_data(df_quality)

        # Step 5: Write to Silver
        # write_to_silver(
        #     glue_context,
        #     df_enriched,
        #     args['target_s3_path'],
        #     args['target_database'],
        #     args['target_table']
        # )

        print("=" * 80)
        print("ETL Job completed successfully!")
        print("=" * 80)

        # TODO: Commit job bookmark
        # job.commit()

    except Exception as e:
        print(f"CRITICAL ERROR in ETL job: {str(e)}")
        raise

    finally:
        # TODO: Stop Spark context
        # sc.stop()
        pass


if __name__ == "__main__":
    main()


# ===============================================================================
# TESTING TIPS:
# ===============================================================================
# 1. Test locally with small sample data before deploying to Glue
# 2. Use spark.read.parquet() or spark.read.csv() for local testing
# 3. Print DataFrame schemas with df.printSchema() to debug
# 4. Use df.show(5) to preview data transformations
# 5. Check record counts after each transformation
# 6. Enable Spark UI to monitor job performance
#
# COMMON ERRORS:
# - "Table not found": Check database and table names in Glue Catalog
# - "Column not found": Verify column names match your data schema
# - "Type mismatch": Ensure data types match your cast operations
# - "Path already exists": Set overwrite mode or use partitions
# - "Out of memory": Increase DPU allocation or optimize transformations
#
# PERFORMANCE TIPS:
# - Use partitioning (year/month/day) for large datasets
# - Enable compression (snappy for parquet)
# - Cache DataFrames if used multiple times: df.cache()
# - Use broadcast joins for small lookup tables
# - Monitor Spark UI for bottlenecks
# ===============================================================================
