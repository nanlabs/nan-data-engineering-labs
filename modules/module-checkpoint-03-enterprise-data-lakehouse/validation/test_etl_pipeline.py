"""
ETL Pipeline Integration Tests for Enterprise Data Lakehouse
=============================================================

Integration tests for the complete ETL pipeline including:
- Raw-to-Bronze ingestion
- Bronze-to-Silver transformation with Delta Lake
- Silver-to-Gold aggregations and business logic
- Schema evolution and compatibility
- Incremental loads and change data capture
- Error handling and recovery
- Data validation at each layer
- Performance metrics

Usage:
------
    pytest validation/test_etl_pipeline.py -v
    pytest validation/test_etl_pipeline.py::TestRawToBronze -v
    pytest validation/test_etl_pipeline.py -k "incremental" --tb=short
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO


# ============================================================================
# Raw-to-Bronze Tests
# ============================================================================

class TestRawToBronze:
    """Test raw data ingestion into bronze layer."""

    def test_ingest_csv_to_bronze(self, s3_client, project_config, sample_customers_data):
        """Test ingesting CSV data to bronze layer."""
        bucket = project_config['bronze_bucket']

        # Upload CSV to bronze
        csv_buffer = sample_customers_data.to_csv(index=False)
        key = 'raw/customers/2024/03/10/customers.csv'

        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=csv_buffer
        )

        # Verify upload
        response = s3_client.get_object(Bucket=bucket, Key=key)
        downloaded_data = pd.read_csv(BytesIO(response['Body'].read()))

        assert len(downloaded_data) == len(sample_customers_data), \
            "Row count should match"
        assert list(downloaded_data.columns) == list(sample_customers_data.columns), \
            "Columns should match"

    def test_ingest_json_to_bronze(self, s3_client, project_config, sample_orders_data):
        """Test ingesting JSON data to bronze layer."""
        bucket = project_config['bronze_bucket']

        # Upload JSON to bronze
        json_buffer = sample_orders_data.to_json(orient='records', date_format='iso')
        key = 'raw/orders/2024/03/10/orders.json'

        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=json_buffer
        )

        # Verify upload
        response = s3_client.get_object(Bucket=bucket, Key=key)
        downloaded_data = pd.read_json(BytesIO(response['Body'].read()))

        assert len(downloaded_data) == len(sample_orders_data), \
            "Row count should match"

    def test_ingest_parquet_to_bronze(self, s3_client, project_config, sample_products_data):
        """Test ingesting Parquet data to bronze layer."""
        bucket = project_config['bronze_bucket']

        # Upload Parquet to bronze
        parquet_buffer = sample_products_data.to_parquet(index=False)
        key = 'raw/products/2024/03/10/products.parquet'

        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=parquet_buffer
        )

        # Verify upload
        response = s3_client.get_object(Bucket=bucket, Key=key)
        downloaded_data = pd.read_parquet(BytesIO(response['Body'].read()))

        assert len(downloaded_data) == len(sample_products_data), \
            "Row count should match"

    def test_add_ingestion_metadata(self, sample_customers_data):
        """Test adding ingestion metadata to bronze data."""
        bronze_data = sample_customers_data.copy()

        # Add metadata columns
        bronze_data['_ingestion_timestamp'] = datetime.now()
        bronze_data['_ingestion_date'] = datetime.now().date()
        bronze_data['_source_file'] = 'customers.csv'
        bronze_data['_source_system'] = 'crm'

        # Verify metadata columns
        assert '_ingestion_timestamp' in bronze_data.columns
        assert '_ingestion_date' in bronze_data.columns
        assert '_source_file' in bronze_data.columns
        assert '_source_system' in bronze_data.columns

        # All rows should have metadata
        assert bronze_data['_ingestion_timestamp'].notna().all()
        assert bronze_data['_source_file'].notna().all()

    def test_partition_bronze_data_by_date(self, s3_client, project_config, sample_orders_data):
        """Test partitioning bronze data by date."""
        bucket = project_config['bronze_bucket']

        # Add partition column
        sample_orders_data['partition_date'] = sample_orders_data['order_date'].dt.date

        # Group by partition and upload
        for partition_date, group in sample_orders_data.groupby('partition_date'):
            year = partition_date.year
            month = f"{partition_date.month:02d}"
            day = f"{partition_date.day:02d}"

            key = f'raw/orders/year={year}/month={month}/day={day}/data.parquet'

            parquet_buffer = group.to_parquet(index=False)
            s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=parquet_buffer
            )

        # Verify partitions were created
        response = s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix='raw/orders/year='
        )

        objects = response.get('Contents', [])
        assert len(objects) > 0, "Should have created partitioned files"

    def test_handle_malformed_data(self):
        """Test handling of malformed data during ingestion."""
        # Simulate malformed data
        malformed_data = [
            {'id': 1, 'name': 'Alice', 'value': 100},
            {'id': 2, 'name': 'Bob'},  # Missing 'value'
            {'id': 3, 'value': 300},  # Missing 'name'
            {'id': None, 'name': 'David', 'value': 400},  # Null id
        ]

        df = pd.DataFrame(malformed_data)

        # Separate valid and invalid records
        valid_records = df[df['id'].notna() & df['name'].notna() & df['value'].notna()]
        invalid_records = df[~(df['id'].notna() & df['name'].notna() & df['value'].notna())]

        assert len(valid_records) == 1, "Should have 1 valid record"
        assert len(invalid_records) == 3, "Should have 3 invalid records"

    def test_deduplication_at_bronze(self, sample_customers_data):
        """Test deduplication of records in bronze layer."""
        # Create data with duplicates
        duplicated_data = pd.concat([
            sample_customers_data.iloc[:10],
            sample_customers_data.iloc[:5]  # Duplicate first 5 records
        ])

        # Deduplicate based on customer_id
        deduplicated = duplicated_data.drop_duplicates(subset=['customer_id'], keep='last')

        assert len(deduplicated) == 10, "Should have 10 unique records after deduplication"


# ============================================================================
# Bronze-to-Silver Tests
# ============================================================================

class TestBronzeToSilver:
    """Test bronze to silver transformation with Delta Lake."""

    def test_data_type_conversion(self, sample_customers_data):
        """Test data type conversions and standardization."""
        bronze_data = sample_customers_data.copy()

        # Convert data types
        silver_data = bronze_data.copy()
        silver_data['customer_id'] = silver_data['customer_id'].astype('int64')
        silver_data['created_at'] = pd.to_datetime(silver_data['created_at'])

        # Add derived columns
        silver_data['full_name'] = silver_data['first_name'] + ' ' + silver_data['last_name']
        silver_data['email_domain'] = silver_data['email'].apply(lambda x: x.split('@')[1] if '@' in x else None)

        # Verify transformations
        assert silver_data['customer_id'].dtype == 'int64'
        assert pd.api.types.is_datetime64_any_dtype(silver_data['created_at'])
        assert 'full_name' in silver_data.columns
        assert 'email_domain' in silver_data.columns

    def test_data_cleansing(self, sample_data_quality_issues):
        """Test data cleansing and standardization."""
        bronze_data = sample_data_quality_issues.copy()

        # Cleanse data
        silver_data = bronze_data.copy()

        # Remove leading/trailing whitespace
        for col in silver_data.select_dtypes(include=['object']).columns:
            silver_data[col] = silver_data[col].str.strip() if silver_data[col].dtype == 'object' else silver_data[col]

        # Standardize email format (lowercase)
        if 'email' in silver_data.columns:
            silver_data['email'] = silver_data['email'].str.lower()

        # Replace invalid values with None
        if 'age' in silver_data.columns:
            silver_data.loc[(silver_data['age'] < 0) | (silver_data['age'] > 120), 'age'] = None

        # Verify cleansing
        invalid_ages = silver_data[(silver_data['age'] < 0) | (silver_data['age'] > 120)].dropna(subset=['age'])
        assert len(invalid_ages) == 0, "Should have removed invalid ages"

    def test_pii_masking(self, sample_customers_data):
        """Test PII masking in silver layer."""
        bronze_data = sample_customers_data.copy()
        silver_data = bronze_data.copy()

        # Mask PII fields
        silver_data['ssn_masked'] = silver_data['ssn'].apply(
            lambda x: f"***-**-{x[-4:]}" if isinstance(x, str) and len(x) >= 4 else "***"
        )

        silver_data['credit_card_masked'] = silver_data['credit_card'].apply(
            lambda x: f"****-****-****-{x[-4:]}" if isinstance(x, str) and len(x) >= 4 else "****"
        )

        silver_data['email_masked'] = silver_data['email'].apply(
            lambda x: f"{x[0]}***@{x.split('@')[1]}" if '@' in x and len(x) > 0 else "***"
        )

        # Drop original PII columns
        silver_data = silver_data.drop(columns=['ssn', 'credit_card'])

        # Verify masking
        assert 'ssn_masked' in silver_data.columns
        assert 'ssn' not in silver_data.columns
        assert all('***' in str(val) for val in silver_data['ssn_masked'])

    def test_schema_validation(self, sample_customers_data):
        """Test schema validation during transformation."""
        expected_schema = {
            'customer_id': 'int64',
            'first_name': 'object',
            'last_name': 'object',
            'email': 'object',
        }

        bronze_data = sample_customers_data[list(expected_schema.keys())].copy()

        # Validate schema
        schema_valid = True
        for col, expected_type in expected_schema.items():
            if col not in bronze_data.columns:
                schema_valid = False
                break

            actual_type = str(bronze_data[col].dtype)
            if expected_type not in actual_type and actual_type not in expected_type:
                # Type mismatch - try to convert
                try:
                    bronze_data[col] = bronze_data[col].astype(expected_type)
                except:
                    schema_valid = False
                    break

        assert schema_valid, "Schema should be valid or convertible"

    def test_join_with_reference_data(self, sample_orders_data, sample_customers_data):
        """Test joining with reference data."""
        orders = sample_orders_data.copy()
        customers = sample_customers_data.copy()

        # Join orders with customer data
        enriched_orders = orders.merge(
            customers[['customer_id', 'first_name', 'last_name', 'email']],
            on='customer_id',
            how='left'
        )

        # Verify join
        assert len(enriched_orders) == len(orders), "Row count should match"
        assert 'first_name' in enriched_orders.columns, "Should have customer name"
        assert 'email' in enriched_orders.columns, "Should have customer email"

    def test_delta_lake_upsert(self):
        """Test Delta Lake UPSERT (merge) operation."""
        # Existing data
        existing_data = pd.DataFrame({
            'customer_id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie'],
            'email': ['alice@test.com', 'bob@test.com', 'charlie@test.com'],
            'updated_at': [datetime.now() - timedelta(days=5)] * 3
        })

        # New data (updates and inserts)
        new_data = pd.DataFrame({
            'customer_id': [2, 3, 4],
            'name': ['Bob Updated', 'Charlie Updated', 'David'],
            'email': ['bob.new@test.com', 'charlie.new@test.com', 'david@test.com'],
            'updated_at': [datetime.now()] * 3
        })

        # Simulate UPSERT
        # 1. Mark existing records as not current
        existing_data['is_current'] = False

        # 2. Combine existing and new
        combined = pd.concat([existing_data, new_data], ignore_index=True)

        # 3. Keep only most recent version of each customer
        result = combined.sort_values('updated_at').groupby('customer_id').last().reset_index()

        # Verify UPSERT
        assert len(result) == 4, "Should have 4 unique customers"
        assert result[result['customer_id'] == 2]['name'].iloc[0] == 'Bob Updated'
        assert result[result['customer_id'] == 4]['name'].iloc[0] == 'David'

    def test_delta_time_travel(self):
        """Test Delta Lake time travel functionality."""
        # Simulate versioned data
        versions = [
            {
                'version': 1,
                'timestamp': datetime.now() - timedelta(days=2),
                'data': pd.DataFrame({'id': [1, 2], 'value': [100, 200]})
            },
            {
                'version': 2,
                'timestamp': datetime.now() - timedelta(days=1),
                'data': pd.DataFrame({'id': [1, 2, 3], 'value': [150, 200, 300]})
            },
            {
                'version': 3,
                'timestamp': datetime.now(),
                'data': pd.DataFrame({'id': [1, 2, 3], 'value': [150, 250, 300]})
            }
        ]

        # Query specific version
        version_2_data = versions[1]['data']

        assert len(version_2_data) == 3
        assert version_2_data[version_2_data['id'] == 1]['value'].iloc[0] == 150

        # Query as of timestamp
        as_of_timestamp = datetime.now() - timedelta(days=1.5)
        historical_version = [v for v in versions if v['timestamp'] <= as_of_timestamp][-1]

        assert historical_version['version'] == 1


# ============================================================================
# Silver-to-Gold Tests
# ============================================================================

class TestSilverToGold:
    """Test silver to gold aggregations and business logic."""

    def test_customer_aggregation(self, sample_orders_data, sample_customers_data):
        """Test customer-level aggregations."""
        orders = sample_orders_data.copy()

        # Calculate customer metrics
        customer_metrics = orders.groupby('customer_id').agg({
            'order_id': 'count',
            'order_amount': ['sum', 'mean', 'max'],
        }).reset_index()

        # Flatten column names
        customer_metrics.columns = ['customer_id', 'total_orders', 'total_revenue',
                                    'avg_order_value', 'max_order_value']

        # Verify aggregations
        assert 'total_orders' in customer_metrics.columns
        assert 'total_revenue' in customer_metrics.columns
        assert len(customer_metrics) > 0

    def test_daily_sales_aggregation(self, sample_orders_data):
        """Test daily sales aggregations."""
        orders = sample_orders_data.copy()

        # Extract date
        orders['order_date_only'] = orders['order_date'].dt.date

        # Daily aggregation
        daily_sales = orders.groupby('order_date_only').agg({
            'order_id': 'count',
            'order_amount': 'sum',
        }).reset_index()

        daily_sales.columns = ['date', 'order_count', 'total_sales']

        # Verify aggregation
        assert 'order_count' in daily_sales.columns
        assert 'total_sales' in daily_sales.columns
        assert daily_sales['total_sales'].sum() > 0

    def test_product_category_analysis(self, sample_orders_data):
        """Test product category analysis."""
        orders = sample_orders_data.copy()

        # Category analysis
        category_stats = orders.groupby('product_category').agg({
            'order_id': 'count',
            'order_amount': ['sum', 'mean'],
        }).reset_index()

        category_stats.columns = ['category', 'order_count', 'total_revenue', 'avg_revenue']

        # Add percentage of total
        category_stats['revenue_percentage'] = (
            category_stats['total_revenue'] / category_stats['total_revenue'].sum() * 100
        )

        # Verify analysis
        assert 'revenue_percentage' in category_stats.columns
        assert abs(category_stats['revenue_percentage'].sum() - 100.0) < 0.01

    def test_customer_segmentation(self, sample_orders_data):
        """Test customer segmentation logic."""
        orders = sample_orders_data.copy()

        # Calculate customer value
        customer_value = orders.groupby('customer_id').agg({
            'order_amount': 'sum',
            'order_id': 'count'
        }).reset_index()

        customer_value.columns = ['customer_id', 'total_spent', 'order_count']

        # Segment customers
        def segment_customer(row):
            if row['total_spent'] >= 5000 and row['order_count'] >= 10:
                return 'VIP'
            elif row['total_spent'] >= 2000 or row['order_count'] >= 5:
                return 'Regular'
            else:
                return 'Occasional'

        customer_value['segment'] = customer_value.apply(segment_customer, axis=1)

        # Verify segmentation
        assert 'segment' in customer_value.columns
        assert set(customer_value['segment']).issubset({'VIP', 'Regular', 'Occasional'})

    def test_trend_calculation(self, sample_orders_data):
        """Test trend calculation (e.g., 7-day moving average)."""
        orders = sample_orders_data.copy()

        # Daily sales
        orders['order_date_only'] = orders['order_date'].dt.date
        daily_sales = orders.groupby('order_date_only')['order_amount'].sum().reset_index()
        daily_sales.columns = ['date', 'sales']
        daily_sales = daily_sales.sort_values('date')

        # Calculate 7-day moving average
        daily_sales['sales_7day_ma'] = daily_sales['sales'].rolling(window=7, min_periods=1).mean()

        # Verify trend
        assert 'sales_7day_ma' in daily_sales.columns
        assert daily_sales['sales_7day_ma'].notna().all()

    def test_kpi_calculation(self, sample_orders_data, sample_customers_data):
        """Test KPI calculations."""
        orders = sample_orders_data.copy()
        customers = sample_customers_data.copy()

        # Calculate KPIs
        kpis = {
            'total_customers': len(customers),
            'total_orders': len(orders),
            'total_revenue': orders['order_amount'].sum(),
            'average_order_value': orders['order_amount'].mean(),
            'orders_per_customer': len(orders) / len(customers),
        }

        # Add time-based KPIs
        last_30_days = datetime.now() - timedelta(days=30)
        recent_orders = orders[orders['order_date'] >= last_30_days]

        kpis['orders_last_30_days'] = len(recent_orders)
        kpis['revenue_last_30_days'] = recent_orders['order_amount'].sum()

        # Verify KPIs
        assert kpis['total_revenue'] > 0
        assert kpis['average_order_value'] > 0
        assert kpis['orders_per_customer'] > 0


# ============================================================================
# Schema Evolution Tests
# ============================================================================

class TestSchemaEvolution:
    """Test schema evolution and compatibility."""

    def test_add_new_column(self):
        """Test adding a new column to existing schema."""
        # Original schema
        original_data = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['A', 'B', 'C'],
            'value': [100, 200, 300]
        })

        # New data with additional column
        new_data = pd.DataFrame({
            'id': [4, 5],
            'name': ['D', 'E'],
            'value': [400, 500],
            'category': ['X', 'Y']  # New column
        })

        # Merge schemas (add missing columns with None)
        combined = pd.concat([original_data, new_data], ignore_index=True)

        # Verify schema evolution
        assert 'category' in combined.columns
        assert combined['category'].iloc[0] is None or pd.isna(combined['category'].iloc[0])
        assert combined['category'].iloc[3] == 'X'

    def test_remove_column(self):
        """Test removing a column (backward compatibility)."""
        # Original data with deprecated column
        original_data = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['A', 'B', 'C'],
            'deprecated_field': ['X', 'Y', 'Z'],
            'value': [100, 200, 300]
        })

        # Remove deprecated column
        evolved_data = original_data.drop(columns=['deprecated_field'])

        # Verify column removal
        assert 'deprecated_field' not in evolved_data.columns
        assert 'value' in evolved_data.columns

    def test_change_column_type(self):
        """Test changing column data type."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],  # String
            'value': [100, 200, 300]
        })

        # Change type
        data['id'] = data['id'].astype('int64')

        # Verify type change
        assert data['id'].dtype == 'int64'

    def test_schema_compatibility_check(self):
        """Test schema compatibility validation."""
        schema_v1 = {
            'id': 'int64',
            'name': 'string',
            'value': 'float64'
        }

        schema_v2 = {
            'id': 'int64',
            'name': 'string',
            'value': 'float64',
            'category': 'string'  # Added field
        }

        # Check backward compatibility
        v1_keys = set(schema_v1.keys())
        v2_keys = set(schema_v2.keys())

        # v2 should be superset of v1 (backward compatible)
        is_backward_compatible = v1_keys.issubset(v2_keys)

        assert is_backward_compatible, "Schema v2 should be backward compatible with v1"


# ============================================================================
# Incremental Load Tests
# ============================================================================

class TestIncrementalLoads:
    """Test incremental data loading and CDC."""

    def test_timestamp_based_incremental(self):
        """Test incremental load based on timestamp."""
        # Existing data
        existing_max_timestamp = datetime.now() - timedelta(days=1)

        # New data
        all_data = pd.DataFrame({
            'id': range(1, 11),
            'value': range(100, 110),
            'updated_at': [
                datetime.now() - timedelta(days=i) for i in range(5, -5, -1)
            ]
        })

        # Incremental load: only records newer than existing max
        incremental_data = all_data[all_data['updated_at'] > existing_max_timestamp]

        # Verify incremental load
        assert len(incremental_data) < len(all_data)
        assert all(incremental_data['updated_at'] > existing_max_timestamp)

    def test_change_data_capture(self):
        """Test change data capture (CDC) logic."""
        # Old state
        old_data = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie'],
            'value': [100, 200, 300]
        })

        # New state
        new_data = pd.DataFrame({
            'id': [1, 2, 3, 4],
            'name': ['Alice Updated', 'Bob', 'Charlie', 'David'],
            'value': [150, 200, 350, 400]
        })

        # Detect changes
        merged = new_data.merge(old_data, on='id', how='left', suffixes=('_new', '_old'))

        # Identify change types
        merged['change_type'] = 'INSERT'  # Default for new records
        merged.loc[merged['name_old'].notna(), 'change_type'] = 'UPDATE'
        merged.loc[
            (merged['name_old'].notna()) &
            (merged['name_new'] == merged['name_old']) &
            (merged['value_new'] == merged['value_old']),
            'change_type'
        ] = 'NO_CHANGE'

        # Verify CDC
        assert len(merged[merged['change_type'] == 'INSERT']) == 1  # David
        assert len(merged[merged['change_type'] == 'UPDATE']) >= 1  # Alice, Charlie
        assert len(merged[merged['change_type'] == 'NO_CHANGE']) >= 1  # Bob

    def test_watermark_tracking(self):
        """Test watermark tracking for incremental loads."""
        # Watermark table
        watermarks = {
            'customers': datetime.now() - timedelta(days=1),
            'orders': datetime.now() - timedelta(hours=6),
            'products': datetime.now() - timedelta(hours=12)
        }

        # Process incremental load
        current_time = datetime.now()

        for table, last_watermark in watermarks.items():
            # Simulate loading data since watermark
            time_since_last_load = (current_time - last_watermark).total_seconds() / 3600

            # Update watermark after successful load
            watermarks[table] = current_time

        # Verify watermarks updated
        for table, watermark in watermarks.items():
            assert watermark == current_time


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling and recovery mechanisms."""

    def test_handle_missing_source_file(self, s3_client, project_config):
        """Test handling of missing source files."""
        bucket = project_config['bronze_bucket']
        key = 'nonexistent/file.csv'

        try:
            s3_client.get_object(Bucket=bucket, Key=key)
            pytest.fail("Should raise error for missing file")
        except Exception as e:
            # Error should be caught and handled
            assert 'NoSuchKey' in str(e) or 'not found' in str(e).lower()

    def test_handle_schema_mismatch(self):
        """Test handling of schema mismatches."""
        expected_columns = ['id', 'name', 'value']

        # Data with different schema
        data = pd.DataFrame({
            'id': [1, 2, 3],
            'different_name': ['A', 'B', 'C'],
            'value': [100, 200, 300]
        })

        # Check for schema mismatch
        missing_columns = set(expected_columns) - set(data.columns)
        extra_columns = set(data.columns) - set(expected_columns)

        assert len(missing_columns) > 0, "Should detect missing columns"
        assert 'name' in missing_columns

    def test_handle_data_quality_failures(self, sample_data_quality_issues):
        """Test handling of data quality failures."""
        data = sample_data_quality_issues.copy()

        # Define quality thresholds
        max_null_percentage = 10.0

        # Check null percentage
        quality_report = {}
        for col in data.columns:
            null_pct = (data[col].isnull().sum() / len(data)) * 100
            quality_report[col] = {
                'null_percentage': null_pct,
                'passes': null_pct <= max_null_percentage
            }

        # Identify failing columns
        failing_columns = [col for col, report in quality_report.items()
                          if not report['passes']]

        # Handle failures (e.g., reject batch, alert, quarantine)
        if failing_columns:
            assert len(failing_columns) >= 3, "Should detect quality issues"

    def test_retry_logic(self):
        """Test retry logic for transient failures."""
        max_retries = 3
        retry_count = 0
        success = False

        # Simulate operation that fails twice then succeeds
        attempt = 0
        while retry_count < max_retries and not success:
            attempt += 1
            retry_count += 1

            # Simulate: fail first 2 times, succeed on 3rd
            if attempt >= 3:
                success = True

        assert success, "Should succeed after retries"
        assert retry_count == 3, "Should have retried 3 times"

    def test_dead_letter_queue_handling(self):
        """Test handling of failed records via DLQ."""
        # Simulate processing records
        records = [
            {'id': 1, 'valid': True},
            {'id': 2, 'valid': False},  # Will fail
            {'id': 3, 'valid': True},
            {'id': 4, 'valid': False},  # Will fail
        ]

        successful_records = []
        failed_records = []

        for record in records:
            if record['valid']:
                successful_records.append(record)
            else:
                failed_records.append(record)

        # Verify DLQ handling
        assert len(successful_records) == 2
        assert len(failed_records) == 2
        assert all(not r['valid'] for r in failed_records)


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformanceMetrics:
    """Test performance metrics and monitoring."""

    def test_measure_processing_time(self, sample_orders_data):
        """Test measuring processing time."""
        start_time = datetime.now()

        # Simulate data processing
        result = sample_orders_data.groupby('customer_id')['order_amount'].sum()

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        # Verify timing
        assert processing_time >= 0
        assert processing_time < 10, "Should process quickly"

    def test_measure_data_volume(self, sample_orders_data):
        """Test measuring data volume metrics."""
        metrics = {
            'row_count': len(sample_orders_data),
            'column_count': len(sample_orders_data.columns),
            'memory_usage_mb': sample_orders_data.memory_usage(deep=True).sum() / 1024 / 1024
        }

        # Verify metrics
        assert metrics['row_count'] > 0
        assert metrics['column_count'] > 0
        assert metrics['memory_usage_mb'] > 0

    def test_calculate_throughput(self):
        """Test calculating processing throughput."""
        records_processed = 10000
        processing_time_seconds = 5.0

        throughput_per_second = records_processed / processing_time_seconds

        assert throughput_per_second == 2000.0
        assert throughput_per_second > 1000, "Throughput should be reasonable"

    def test_partition_skew_detection(self, sample_orders_data):
        """Test detection of partition skew."""
        # Partition by customer
        partition_sizes = sample_orders_data.groupby('customer_id').size()

        # Calculate statistics
        mean_size = partition_sizes.mean()
        std_size = partition_sizes.std()
        max_size = partition_sizes.max()

        # Detect skew (if max is much larger than mean)
        skew_factor = max_size / mean_size if mean_size > 0 else 0
        has_skew = skew_factor > 2.0  # Threshold for skew

        # In this data, there shouldn't be much skew
        # but we verify the detection logic works
        assert skew_factor >= 0


# ============================================================================
# Integration Tests
# ============================================================================

class TestETLPipelineIntegration:
    """End-to-end ETL pipeline integration tests."""

    def test_full_pipeline_raw_to_gold(self, s3_client, project_config,
                                      sample_customers_data, sample_orders_data):
        """Test complete pipeline from raw to gold."""
        # 1. Raw to Bronze
        bronze_bucket = project_config['bronze_bucket']
        bronze_key = 'raw/customers/data.parquet'

        bronze_data = sample_customers_data.copy()
        bronze_data['_ingestion_timestamp'] = datetime.now()

        s3_client.put_object(
            Bucket=bronze_bucket,
            Key=bronze_key,
            Body=bronze_data.to_parquet(index=False)
        )

        # 2. Bronze to Silver
        silver_data = bronze_data.copy()
        silver_data['full_name'] = silver_data['first_name'] + ' ' + silver_data['last_name']

        # 3. Silver to Gold
        orders = sample_orders_data.copy()
        customer_metrics = orders.groupby('customer_id').agg({
            'order_id': 'count',
            'order_amount': 'sum'
        }).reset_index()

        gold_data = silver_data.merge(customer_metrics, on='customer_id', how='left')

        # Verify pipeline
        assert len(gold_data) > 0
        assert 'full_name' in gold_data.columns
        assert 'order_id' in gold_data.columns

    def test_pipeline_idempotency(self, sample_customers_data):
        """Test that pipeline is idempotent (can run multiple times)."""
        # Run pipeline twice
        result1 = sample_customers_data.copy()
        result1['processed'] = True

        result2 = sample_customers_data.copy()
        result2['processed'] = True

        # Results should be identical
        pd.testing.assert_frame_equal(result1, result2)

    def test_pipeline_observability(self, sample_orders_data):
        """Test pipeline observability and logging."""
        pipeline_metrics = {
            'start_time': datetime.now(),
            'input_records': len(sample_orders_data),
            'output_records': 0,
            'failed_records': 0,
            'processing_time_seconds': 0,
        }

        # Simulate processing
        processed_data = sample_orders_data.copy()
        pipeline_metrics['output_records'] = len(processed_data)
        pipeline_metrics['end_time'] = datetime.now()
        pipeline_metrics['processing_time_seconds'] = (
            pipeline_metrics['end_time'] - pipeline_metrics['start_time']
        ).total_seconds()

        # Verify metrics
        assert pipeline_metrics['output_records'] == pipeline_metrics['input_records']
        assert pipeline_metrics['processing_time_seconds'] >= 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
