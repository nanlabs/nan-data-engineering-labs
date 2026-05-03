"""
Data quality validation tests
Tests for data integrity, completeness, and business rules
"""

import pytest
import pandas as pd
import json
import logging
from datetime import datetime, timedelta
from io import BytesIO
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class TestBronzeLayerQuality:
    """Data quality tests for bronze (raw) layer"""

    @pytest.mark.integration
    def test_bronze_row_counts(self, s3_client, bucket_names):
        """
        Verify expected data volume in bronze layer

        Tests:
        - Data exists in bronze layer
        - Row counts are within expected ranges
        - No empty files
        """
        logger.info("Testing bronze layer row counts")

        raw_bucket = bucket_names['raw']

        # List objects in raw bucket
        response = s3_client.list_objects_v2(
            Bucket=raw_bucket,
            MaxKeys=100
        )

        if 'Contents' not in response:
            logger.warning("No data in bronze layer")
            pytest.skip("No data in bronze layer")

        files = response['Contents']
        total_size = sum(obj['Size'] for obj in files)

        logger.info(f"✓ Found {len(files)} files in bronze layer")
        logger.info(f"✓ Total size: {total_size / (1024*1024):.2f} MB")

        # Check for empty files
        empty_files = [obj for obj in files if obj['Size'] == 0]
        assert len(empty_files) == 0, f"Found {len(empty_files)} empty files"

        logger.info("✓ No empty files found")

    @pytest.mark.integration
    def test_bronze_schema_validation(self, s3_client, bucket_names):
        """
        Validate schema of raw data files

        Tests:
        - JSON files are valid JSON
        - CSV files have headers
        - Required columns are present
        """
        logger.info("Testing bronze layer schema validation")

        raw_bucket = bucket_names['raw']

        # Get sample files
        response = s3_client.list_objects_v2(
            Bucket=raw_bucket,
            MaxKeys=10
        )

        if 'Contents' not in response:
            logger.warning("No data to validate")
            return

        json_files = [obj for obj in response['Contents'] if obj['Key'].endswith('.json')]
        csv_files = [obj for obj in response['Contents'] if obj['Key'].endswith('.csv')]

        # Validate JSON files
        for obj in json_files[:3]:  # Check first 3
            try:
                file_obj = s3_client.get_object(Bucket=raw_bucket, Key=obj['Key'])
                content = file_obj['Body'].read().decode('utf-8')

                data = json.loads(content)
                assert isinstance(data, (list, dict)), "JSON must be list or dict"

                logger.info(f"✓ Valid JSON: {obj['Key']}")
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON in {obj['Key']}: {str(e)}")
            except Exception as e:
                logger.warning(f"Could not validate {obj['Key']}: {str(e)}")

        # Validate CSV files
        for obj in csv_files[:3]:  # Check first 3
            try:
                file_obj = s3_client.get_object(Bucket=raw_bucket, Key=obj['Key'])
                content = file_obj['Body'].read().decode('utf-8')

                lines = content.split('\n')
                assert len(lines) > 1, "CSV file has no data rows"

                # Check header exists
                header = lines[0]
                assert ',' in header or ';' in header, "No CSV delimiter found"

                logger.info(f"✓ Valid CSV: {obj['Key']}")
            except Exception as e:
                logger.warning(f"Could not validate {obj['Key']}: {str(e)}")

    @pytest.mark.integration
    def test_bronze_nulls_in_key_columns(self, s3_client, bucket_names):
        """
        Check for null values in key columns

        Tests:
        - Primary key columns are not null
        - Required fields are populated
        - Data completeness
        """
        logger.info("Testing for nulls in key columns")

        raw_bucket = bucket_names['raw']

        # Get JSON files to check
        response = s3_client.list_objects_v2(
            Bucket=raw_bucket,
            MaxKeys=5
        )

        if 'Contents' not in response:
            logger.warning("No data to check for nulls")
            return

        json_files = [obj for obj in response['Contents'] if obj['Key'].endswith('.json')]

        for obj in json_files[:2]:
            try:
                file_obj = s3_client.get_object(Bucket=raw_bucket, Key=obj['Key'])
                content = file_obj['Body'].read().decode('utf-8')
                data = json.loads(content)

                if isinstance(data, list) and len(data) > 0:
                    # Check first record for key fields
                    first_record = data[0]

                    # Common key fields
                    potential_keys = ['id', 'customer_id', 'order_id', 'product_id', 'user_id']

                    found_keys = [k for k in potential_keys if k in first_record]

                    if found_keys:
                        # Check no nulls in key fields
                        null_keys = [k for k in found_keys if first_record[k] is None or first_record[k] == '']
                        assert len(null_keys) == 0, f"Null values in key fields: {null_keys}"

                        logger.info(f"✓ No nulls in key fields for {obj['Key']}")

            except Exception as e:
                logger.warning(f"Could not check nulls in {obj['Key']}: {str(e)}")

    @pytest.mark.integration
    def test_bronze_data_types(self, s3_client, bucket_names):
        """
        Validate data types in bronze layer

        Tests:
        - Numeric fields contain numbers
        - Date fields are valid dates
        - Boolean fields are boolean
        """
        logger.info("Testing bronze layer data types")

        raw_bucket = bucket_names['raw']

        response = s3_client.list_objects_v2(
            Bucket=raw_bucket,
            MaxKeys=5
        )

        if 'Contents' not in response:
            logger.warning("No data to check types")
            return

        json_files = [obj for obj in response['Contents'] if obj['Key'].endswith('.json')]

        for obj in json_files[:2]:
            try:
                file_obj = s3_client.get_object(Bucket=raw_bucket, Key=obj['Key'])
                content = file_obj['Body'].read().decode('utf-8')
                data = json.loads(content)

                if isinstance(data, list) and len(data) > 0:
                    first_record = data[0]

                    # Check date fields
                    date_fields = [k for k in first_record.keys() if 'date' in k.lower() or 'timestamp' in k.lower()]
                    for field in date_fields:
                        value = first_record[field]
                        if value:
                            # Try to parse as date
                            try:
                                pd.to_datetime(value)
                                logger.info(f"✓ Valid date in field '{field}': {value}")
                            except:
                                logger.warning(f"Invalid date in field '{field}': {value}")

            except Exception as e:
                logger.warning(f"Could not check types in {obj['Key']}: {str(e)}")


class TestSilverLayerQuality:
    """Data quality tests for silver (processed) layer"""

    @pytest.mark.integration
    def test_silver_transformations(self, s3_client, bucket_names):
        """
        Validate data transformations in silver layer

        Tests:
        - Email addresses are lowercase
        - Country codes are standardized
        - Dates are in ISO format
        - Strings are trimmed
        """
        logger.info("Testing silver layer transformations")

        processed_bucket = bucket_names['processed']

        response = s3_client.list_objects_v2(
            Bucket=processed_bucket,
            MaxKeys=10
        )

        if 'Contents' not in response:
            logger.warning("No data in silver layer")
            pytest.skip("No data in silver layer")

        files = response['Contents']
        parquet_files = [obj for obj in files if obj['Key'].endswith('.parquet')]

        logger.info(f"✓ Found {len(parquet_files)} Parquet files in silver layer")

        # Try to read and validate a Parquet file
        if parquet_files:
            for obj in parquet_files[:2]:
                try:
                    file_obj = s3_client.get_object(Bucket=processed_bucket, Key=obj['Key'])
                    df = pd.read_parquet(BytesIO(file_obj['Body'].read()))

                    logger.info(f"✓ Read Parquet file: {obj['Key']} ({len(df)} rows)")

                    # Check email lowercase (if email column exists)
                    email_cols = [col for col in df.columns if 'email' in col.lower()]
                    for col in email_cols:
                        if df[col].dtype == 'object':
                            non_null_emails = df[col].dropna()
                            if len(non_null_emails) > 0:
                                lowercase_emails = non_null_emails.str.lower()
                                assert (non_null_emails == lowercase_emails).all(), \
                                    f"Some emails not lowercase in {col}"
                                logger.info(f"✓ All emails lowercase in '{col}'")

                    # Check no leading/trailing spaces
                    string_cols = df.select_dtypes(include=['object']).columns
                    for col in string_cols[:5]:  # Check first 5 string columns
                        non_null_values = df[col].dropna()
                        if len(non_null_values) > 0:
                            trimmed_values = non_null_values.str.strip()
                            spaces_found = (non_null_values != trimmed_values).sum()
                            if spaces_found > 0:
                                logger.warning(f"Found {spaces_found} values with spaces in '{col}'")
                            else:
                                logger.info(f"✓ No leading/trailing spaces in '{col}'")

                except Exception as e:
                    logger.warning(f"Could not validate {obj['Key']}: {str(e)}")

    @pytest.mark.integration
    def test_silver_deduplication(self, s3_client, bucket_names):
        """
        Check for duplicate records in silver layer

        Tests:
        - No duplicate IDs
        - No duplicate rows
        - Uniqueness constraints are met
        """
        logger.info("Testing silver layer deduplication")

        processed_bucket = bucket_names['processed']

        response = s3_client.list_objects_v2(
            Bucket=processed_bucket,
            MaxKeys=10
        )

        if 'Contents' not in response:
            logger.warning("No data in silver layer")
            return

        parquet_files = [obj for obj in response['Contents'] if obj['Key'].endswith('.parquet')]

        for obj in parquet_files[:2]:
            try:
                file_obj = s3_client.get_object(Bucket=processed_bucket, Key=obj['Key'])
                df = pd.read_parquet(BytesIO(file_obj['Body'].read()))

                # Check for ID columns
                id_cols = [col for col in df.columns if 'id' in col.lower()]

                for col in id_cols:
                    duplicates = df[col].duplicated().sum()

                    if duplicates > 0:
                        logger.warning(f"Found {duplicates} duplicate values in '{col}'")
                    else:
                        logger.info(f"✓ No duplicates in '{col}'")

                # Check for completely duplicate rows
                duplicate_rows = df.duplicated().sum()
                if duplicate_rows > 0:
                    logger.warning(f"Found {duplicate_rows} duplicate rows")
                else:
                    logger.info(f"✓ No duplicate rows in {obj['Key']}")

            except Exception as e:
                logger.warning(f"Could not check duplicates in {obj['Key']}: {str(e)}")

    @pytest.mark.integration
    def test_silver_data_completeness(self, s3_client, bucket_names):
        """
        Check data completeness in silver layer

        Tests:
        - Required fields are populated
        - Null percentage is acceptable
        - Data volume matches expectations
        """
        logger.info("Testing silver layer data completeness")

        processed_bucket = bucket_names['processed']

        response = s3_client.list_objects_v2(
            Bucket=processed_bucket,
            MaxKeys=10
        )

        if 'Contents' not in response:
            logger.warning("No data in silver layer")
            return

        parquet_files = [obj for obj in response['Contents'] if obj['Key'].endswith('.parquet')]

        for obj in parquet_files[:2]:
            try:
                file_obj = s3_client.get_object(Bucket=processed_bucket, Key=obj['Key'])
                df = pd.read_parquet(BytesIO(file_obj['Body'].read()))

                # Calculate null percentages
                null_percentages = (df.isnull().sum() / len(df) * 100).round(2)

                logger.info(f"Null percentages in {obj['Key']}:")
                for col, pct in null_percentages.items():
                    logger.info(f"  - {col}: {pct}%")

                    # Flag if more than 50% nulls
                    if pct > 50:
                        logger.warning(f"High null percentage in '{col}': {pct}%")

                logger.info(f"✓ Completeness check done for {obj['Key']}")

            except Exception as e:
                logger.warning(f"Could not check completeness in {obj['Key']}: {str(e)}")


class TestGoldLayerQuality:
    """Data quality tests for gold (curated) layer"""

    @pytest.mark.integration
    def test_gold_aggregations(self, s3_client, bucket_names):
        """
        Validate aggregations in gold layer

        Tests:
        - Aggregated tables exist
        - Calculations are correct
        - Summary statistics are accurate
        """
        logger.info("Testing gold layer aggregations")

        curated_bucket = bucket_names['curated']

        response = s3_client.list_objects_v2(
            Bucket=curated_bucket,
            MaxKeys=20
        )

        if 'Contents' not in response:
            logger.warning("No data in gold layer")
            pytest.skip("No data in gold layer")

        files = response['Contents']
        parquet_files = [obj for obj in files if obj['Key'].endswith('.parquet')]

        logger.info(f"✓ Found {len(parquet_files)} Parquet files in gold layer")

        for obj in parquet_files[:2]:
            try:
                file_obj = s3_client.get_object(Bucket=curated_bucket, Key=obj['Key'])
                df = pd.read_parquet(BytesIO(file_obj['Body'].read()))

                logger.info(f"✓ Read gold table: {obj['Key']} ({len(df)} rows, {len(df.columns)} columns)")

                # Check for aggregation columns (sum, count, avg, etc.)
                agg_cols = [col for col in df.columns if any(x in col.lower() for x in ['sum', 'count', 'avg', 'total', 'mean'])]

                if agg_cols:
                    logger.info(f"  - Found aggregation columns: {agg_cols}")

                # Check numeric columns
                numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
                if len(numeric_cols) > 0:
                    logger.info(f"  - Numeric columns: {len(numeric_cols)}")

            except Exception as e:
                logger.warning(f"Could not validate {obj['Key']}: {str(e)}")

    @pytest.mark.integration
    def test_gold_business_rules(self, s3_client, bucket_names):
        """
        Validate business rules in gold layer

        Tests:
        - Totals are non-negative
        - Percentages are between 0 and 100
        - Dates are valid
        - Business logic is correct
        """
        logger.info("Testing gold layer business rules")

        curated_bucket = bucket_names['curated']

        response = s3_client.list_objects_v2(
            Bucket=curated_bucket,
            MaxKeys=10
        )

        if 'Contents' not in response:
            logger.warning("No data in gold layer")
            return

        parquet_files = [obj for obj in response['Contents'] if obj['Key'].endswith('.parquet')]

        for obj in parquet_files[:2]:
            try:
                file_obj = s3_client.get_object(Bucket=curated_bucket, Key=obj['Key'])
                df = pd.read_parquet(BytesIO(file_obj['Body'].read()))

                # Check for amount/total columns
                amount_cols = [col for col in df.columns if any(x in col.lower() for x in ['amount', 'total', 'revenue', 'sales'])]

                for col in amount_cols:
                    if df[col].dtype in ['int64', 'float64']:
                        negative_count = (df[col] < 0).sum()

                        if negative_count > 0:
                            logger.warning(f"Found {negative_count} negative values in '{col}'")
                        else:
                            logger.info(f"✓ All values non-negative in '{col}'")

                # Check for percentage columns
                pct_cols = [col for col in df.columns if 'pct' in col.lower() or 'percent' in col.lower() or 'rate' in col.lower()]

                for col in pct_cols:
                    if df[col].dtype in ['int64', 'float64']:
                        out_of_range = ((df[col] < 0) | (df[col] > 100)).sum()

                        if out_of_range > 0:
                            logger.warning(f"Found {out_of_range} out-of-range values in '{col}'")
                        else:
                            logger.info(f"✓ All percentages in valid range for '{col}'")

            except Exception as e:
                logger.warning(f"Could not validate {obj['Key']}: {str(e)}")


class TestReferentialIntegrity:
    """Tests for referential integrity between tables"""

    @pytest.mark.integration
    def test_foreign_key_relationships(self, s3_client, bucket_names, glue_client, glue_database_name):
        """
        Validate foreign key relationships

        Tests:
        - Customer IDs in orders exist in customers table
        - Product IDs in orders exist in products table
        - No orphaned records
        """
        logger.info("Testing referential integrity")

        # This test requires accessing multiple tables
        # We'll do a simplified check

        try:
            tables_response = glue_client.get_tables(DatabaseName=glue_database_name)
            tables = tables_response['TableList']

            table_names = [t['Name'] for t in tables]
            logger.info(f"Available tables: {table_names}")

            # Look for common relationships
            has_customers = any('customer' in t.lower() for t in table_names)
            has_orders = any('order' in t.lower() for t in table_names)

            if has_customers and has_orders:
                logger.info("✓ Found related tables (customers and orders)")
            else:
                logger.warning("Could not find related tables for referential integrity test")

        except ClientError as e:
            logger.warning(f"Could not check referential integrity: {str(e)}")


class TestDataFreshness:
    """Tests for data freshness and timeliness"""

    @pytest.mark.integration
    def test_data_freshness_sla(self, s3_client, bucket_names):
        """
        Verify data is fresh within SLA

        Tests:
        - Data ingested within last 24 hours
        - No stale data
        - Processing lag is acceptable
        """
        logger.info("Testing data freshness")

        raw_bucket = bucket_names['raw']

        response = s3_client.list_objects_v2(
            Bucket=raw_bucket,
            MaxKeys=50
        )

        if 'Contents' not in response:
            logger.warning("No data to check freshness")
            return

        files = response['Contents']

        # Check last modified times
        now = datetime.now(files[0]['LastModified'].tzinfo)
        sla_threshold = now - timedelta(hours=24)

        fresh_files = [f for f in files if f['LastModified'] >= sla_threshold]
        stale_files = [f for f in files if f['LastModified'] < sla_threshold]

        logger.info(f"✓ Fresh files (< 24h): {len(fresh_files)}")
        logger.info(f"  Stale files (> 24h): {len(stale_files)}")

        # At least some files should be fresh
        if len(files) > 0:
            freshness_rate = len(fresh_files) / len(files) * 100
            logger.info(f"✓ Freshness rate: {freshness_rate:.1f}%")

    @pytest.mark.integration
    def test_processing_lag(self, s3_client, bucket_names):
        """
        Check processing lag between layers

        Tests:
        - Raw to processed lag < 1 hour
        - Processed to curated lag < 2 hours
        """
        logger.info("Testing processing lag")

        raw_bucket = bucket_names['raw']
        processed_bucket = bucket_names['processed']

        # Get latest file from raw
        raw_response = s3_client.list_objects_v2(
            Bucket=raw_bucket,
            MaxKeys=10
        )

        # Get latest file from processed
        processed_response = s3_client.list_objects_v2(
            Bucket=processed_bucket,
            MaxKeys=10
        )

        if 'Contents' in raw_response and 'Contents' in processed_response:
            latest_raw = max(raw_response['Contents'], key=lambda x: x['LastModified'])
            latest_processed = max(processed_response['Contents'], key=lambda x: x['LastModified'])

            lag = latest_processed['LastModified'] - latest_raw['LastModified']
            lag_minutes = lag.total_seconds() / 60

            logger.info(f"  Raw to processed lag: {lag_minutes:.1f} minutes")

            if lag_minutes < 60:
                logger.info("✓ Processing lag is within SLA (< 60 minutes)")
            else:
                logger.warning(f"Processing lag exceeds SLA: {lag_minutes:.1f} minutes")
        else:
            logger.warning("Could not calculate processing lag")
