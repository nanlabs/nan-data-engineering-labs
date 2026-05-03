"""
Data Quality Validation Tests for Enterprise Data Lakehouse
============================================================

End-to-end tests for data quality framework including:
- Completeness checks (null values, required fields)
- Accuracy validation (data types, formats, ranges)
- Consistency checks (referential integrity, duplicates)
- PII detection and masking
- SCD Type 2 implementation
- Delta table optimization
- Data freshness metrics
- Quality score calculation

Usage:
------
    pytest validation/test_data_quality.py -v
    pytest validation/test_data_quality.py::TestCompletenessChecks -v
    pytest validation/test_data_quality.py -k "pii" --tb=short
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
import re


# ============================================================================
# Completeness Tests
# ============================================================================

class TestCompletenessChecks:
    """Test data completeness validations."""

    def test_check_null_values_in_required_columns(self, sample_customers_data, dq_validator):
        """Verify detection of null values in required columns."""
        required_cols = ['customer_id', 'email', 'created_at']

        results = dq_validator.check_completeness(sample_customers_data, required_cols)

        # All required columns should be complete (no nulls)
        for col in required_cols:
            assert results[col]['complete'], \
                f"Column {col} should be complete but has {results[col]['null_count']} nulls"

    def test_detect_missing_data_with_quality_issues(self, sample_data_quality_issues, dq_validator):
        """Verify detection of missing data in problematic dataset."""
        required_cols = ['id', 'name', 'email', 'amount']

        results = dq_validator.check_completeness(sample_data_quality_issues, required_cols)

        # Should detect nulls in id, name, email, amount
        assert not results['id']['complete'], "Should detect null in id column"
        assert not results['name']['complete'], "Should detect null in name column"
        assert not results['email']['complete'], "Should detect null in email column"
        assert not results['amount']['complete'], "Should detect null in amount column"

        # Check percentages
        assert results['id']['null_percentage'] == 20.0, "ID should have 20% nulls (1 out of 5)"
        assert results['name']['null_percentage'] == 20.0, "Name should have 20% nulls (1 out of 5)"

    def test_completeness_report_generation(self, sample_customers_data, dq_validator):
        """Test generation of completeness report."""
        all_cols = sample_customers_data.columns.tolist()

        results = dq_validator.check_completeness(sample_customers_data, all_cols)

        # Report should include all columns
        assert len(results) == len(all_cols), "Report should include all columns"

        # Each column should have required metrics
        for col, metrics in results.items():
            assert 'null_count' in metrics
            assert 'null_percentage' in metrics
            assert 'complete' in metrics

    def test_calculate_overall_completeness_score(self, sample_customers_data, dq_validator):
        """Calculate overall completeness score for dataset."""
        all_cols = sample_customers_data.columns.tolist()
        results = dq_validator.check_completeness(sample_customers_data, all_cols)

        # Calculate score: percentage of columns that are complete
        complete_cols = sum(1 for r in results.values() if r['complete'])
        total_cols = len(results)
        completeness_score = (complete_cols / total_cols) * 100

        # Sample data should be 100% complete
        assert completeness_score == 100.0, \
            f"Completeness score should be 100% but got {completeness_score}%"

    def test_handle_empty_dataframe(self, dq_validator):
        """Test completeness check on empty dataframe."""
        empty_df = pd.DataFrame(columns=['col1', 'col2', 'col3'])

        results = dq_validator.check_completeness(empty_df, ['col1', 'col2'])

        # Empty dataframe should still return results
        assert len(results) == 2
        for col in ['col1', 'col2']:
            assert results[col]['null_count'] == 0
            assert results[col]['complete']


# ============================================================================
# Accuracy Tests
# ============================================================================

class TestAccuracyValidation:
    """Test data accuracy validations."""

    def test_validate_email_format(self, sample_data_quality_issues):
        """Verify email format validation."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        emails = sample_data_quality_issues['email'].dropna()
        valid_emails = emails.apply(lambda x: bool(re.match(email_pattern, str(x))))

        invalid_count = (~valid_emails).sum()

        # Should detect at least 1 invalid email
        assert invalid_count > 0, "Should detect invalid email formats"
        assert invalid_count == 1, "Should detect exactly 1 invalid email (invalid-email)"

    def test_validate_numeric_ranges(self, sample_data_quality_issues, dq_validator):
        """Verify numeric range validation."""
        # Age should be between 0 and 120
        results = dq_validator.check_range(sample_data_quality_issues, 'age', 0, 120)

        assert not results['in_range'], "Should detect out-of-range values"
        assert results['out_of_range_count'] == 2, \
            "Should detect 2 invalid ages (-5 and 150)"

    def test_validate_date_format(self, sample_data_quality_issues):
        """Verify date format validation."""
        dates = sample_data_quality_issues['date'].dropna()

        valid_dates = []
        for date_str in dates:
            try:
                pd.to_datetime(date_str)
                valid_dates.append(True)
            except:
                valid_dates.append(False)

        invalid_count = sum(1 for v in valid_dates if not v)

        # Should detect invalid date (2024-13-32)
        assert invalid_count > 0, "Should detect invalid date formats"

    def test_validate_data_types(self, sample_customers_data):
        """Verify data type validation."""
        expected_types = {
            'customer_id': ['int64', 'int32'],
            'first_name': ['object', 'string'],
            'email': ['object', 'string'],
            'created_at': ['datetime64[ns]', 'object'],  # Could be datetime or string
        }

        for col, expected in expected_types.items():
            actual_type = str(sample_customers_data[col].dtype)
            assert any(exp in actual_type for exp in expected), \
                f"Column {col} has unexpected type {actual_type}"

    def test_validate_amounts_positive(self, sample_orders_data):
        """Verify order amounts are positive."""
        negative_amounts = (sample_orders_data['order_amount'] < 0).sum()

        assert negative_amounts == 0, "Order amounts should all be positive"


# ============================================================================
# Consistency Tests
# ============================================================================

class TestConsistencyValidation:
    """Test data consistency validations."""

    def test_check_primary_key_uniqueness(self, sample_customers_data, dq_validator):
        """Verify primary key uniqueness."""
        results = dq_validator.check_uniqueness(sample_customers_data, ['customer_id'])

        assert results['customer_id']['is_unique'], \
            "Customer ID should be unique"
        assert results['customer_id']['duplicate_count'] == 0, \
            "Should have no duplicate customer IDs"

    def test_detect_duplicate_records(self, dq_validator):
        """Verify detection of duplicate records."""
        # Create data with duplicates
        data = pd.DataFrame({
            'id': [1, 2, 3, 2, 4],  # ID 2 is duplicated
            'name': ['A', 'B', 'C', 'B', 'D'],
        })

        results = dq_validator.check_uniqueness(data, ['id'])

        assert not results['id']['is_unique'], "Should detect duplicates in id"
        assert results['id']['duplicate_count'] == 1, \
            "Should have 1 duplicate (2 occurrences - 1 unique)"

    def test_check_referential_integrity(self, sample_customers_data, sample_orders_data):
        """Verify referential integrity between tables."""
        # All customer_ids in orders should exist in customers
        customer_ids = set(sample_customers_data['customer_id'])
        order_customer_ids = set(sample_orders_data['customer_id'])

        orphan_orders = order_customer_ids - customer_ids

        assert len(orphan_orders) == 0, \
            f"Found {len(orphan_orders)} orphan orders with non-existent customer IDs"

    def test_check_value_consistency(self, sample_orders_data):
        """Verify value consistency across related fields."""
        # Status should be from allowed values
        allowed_statuses = ['pending', 'shipped', 'delivered', 'cancelled']

        invalid_statuses = ~sample_orders_data['status'].isin(allowed_statuses)

        assert invalid_statuses.sum() == 0, \
            "All order statuses should be from allowed values"


# ============================================================================
# PII Detection Tests
# ============================================================================

class TestPIIDetection:
    """Test PII detection and masking."""

    def test_detect_email_pii(self, sample_customers_data, dq_validator):
        """Verify email PII detection."""
        pii_results = dq_validator.detect_pii(sample_customers_data)

        # Should detect email column
        email_pii = [p for p in pii_results if p['column'] == 'email']

        assert len(email_pii) > 0, "Should detect email as PII"
        assert email_pii[0]['pii_type'] == 'email'
        assert email_pii[0]['matches'] == 100, "All 100 emails should match"

    def test_detect_ssn_pii(self, sample_customers_data, dq_validator):
        """Verify SSN PII detection."""
        pii_results = dq_validator.detect_pii(sample_customers_data)

        # Should detect SSN column
        ssn_pii = [p for p in pii_results if p['column'] == 'ssn']

        assert len(ssn_pii) > 0, "Should detect SSN as PII"
        assert ssn_pii[0]['pii_type'] == 'ssn'

    def test_detect_phone_pii(self, sample_customers_data, dq_validator):
        """Verify phone number PII detection."""
        pii_results = dq_validator.detect_pii(sample_customers_data)

        # Should detect phone column
        phone_pii = [p for p in pii_results if p['column'] == 'phone']

        assert len(phone_pii) > 0, "Should detect phone as PII"
        assert phone_pii[0]['pii_type'] == 'phone'

    def test_detect_credit_card_pii(self, sample_customers_data, dq_validator):
        """Verify credit card PII detection."""
        pii_results = dq_validator.detect_pii(sample_customers_data)

        # Should detect credit card column
        cc_pii = [p for p in pii_results if p['column'] == 'credit_card']

        assert len(cc_pii) > 0, "Should detect credit card as PII"
        assert cc_pii[0]['pii_type'] == 'credit_card'

    def test_pii_masking_email(self):
        """Test email masking."""
        def mask_email(email: str) -> str:
            """Mask email keeping first char and domain."""
            parts = email.split('@')
            if len(parts) == 2:
                return f"{parts[0][0]}***@{parts[1]}"
            return "***"

        test_email = "john.doe@example.com"
        masked = mask_email(test_email)

        assert masked == "j***@example.com", \
            f"Email masking incorrect: {masked}"

    def test_pii_masking_ssn(self):
        """Test SSN masking."""
        def mask_ssn(ssn: str) -> str:
            """Mask SSN showing only last 4 digits."""
            return f"***-**-{ssn[-4:]}"

        test_ssn = "123-45-6789"
        masked = mask_ssn(test_ssn)

        assert masked == "***-**-6789", \
            f"SSN masking incorrect: {masked}"

    def test_pii_masking_credit_card(self):
        """Test credit card masking."""
        def mask_credit_card(cc: str) -> str:
            """Mask credit card showing only last 4 digits."""
            parts = cc.split('-')
            if len(parts) == 4:
                return f"****-****-****-{parts[3]}"
            return "****-****-****-****"

        test_cc = "4532-1234-5678-9012"
        masked = mask_credit_card(test_cc)

        assert masked == "****-****-****-9012", \
            f"Credit card masking incorrect: {masked}"


# ============================================================================
# SCD Type 2 Tests
# ============================================================================

class TestSCDType2Implementation:
    """Test Slowly Changing Dimension Type 2 implementation."""

    def test_initial_load_scd2(self):
        """Test initial load creates SCD2 records."""
        # Initial data
        initial_data = pd.DataFrame({
            'customer_id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie'],
            'email': ['alice@test.com', 'bob@test.com', 'charlie@test.com'],
        })

        # Add SCD2 columns
        scd2_data = initial_data.copy()
        scd2_data['effective_start_date'] = datetime.now()
        scd2_data['effective_end_date'] = pd.NaT
        scd2_data['is_current'] = True
        scd2_data['version'] = 1

        # All records should be current
        assert (scd2_data['is_current'] == True).all(), \
            "All initial records should be current"
        assert (scd2_data['version'] == 1).all(), \
            "All initial records should be version 1"

    def test_update_scd2_record(self):
        """Test updating an SCD2 record creates new version."""
        # Existing record
        existing = pd.DataFrame({
            'customer_id': [1],
            'name': ['Alice'],
            'email': ['alice@test.com'],
            'effective_start_date': [datetime.now() - timedelta(days=30)],
            'effective_end_date': [pd.NaT],
            'is_current': [True],
            'version': [1],
        })

        # Update: email changed
        updated_data = pd.DataFrame({
            'customer_id': [1],
            'name': ['Alice'],
            'email': ['alice.new@test.com'],
        })

        # Simulate SCD2 logic
        now = datetime.now()

        # Expire old record
        existing_updated = existing.copy()
        existing_updated['effective_end_date'] = now
        existing_updated['is_current'] = False

        # Create new record
        new_record = updated_data.copy()
        new_record['effective_start_date'] = now
        new_record['effective_end_date'] = pd.NaT
        new_record['is_current'] = True
        new_record['version'] = 2

        # Combine
        final_data = pd.concat([existing_updated, new_record], ignore_index=True)

        # Verify SCD2 logic
        assert len(final_data) == 2, "Should have 2 versions of the record"
        assert final_data[final_data['version'] == 1]['is_current'].iloc[0] == False, \
            "Old version should not be current"
        assert final_data[final_data['version'] == 2]['is_current'].iloc[0] == True, \
            "New version should be current"

    def test_query_current_records(self):
        """Test querying only current records."""
        # Data with multiple versions
        scd2_data = pd.DataFrame({
            'customer_id': [1, 1, 2, 3],
            'name': ['Alice', 'Alice Updated', 'Bob', 'Charlie'],
            'email': ['alice@test.com', 'alice.new@test.com', 'bob@test.com', 'charlie@test.com'],
            'effective_start_date': [
                datetime.now() - timedelta(days=30),
                datetime.now(),
                datetime.now() - timedelta(days=20),
                datetime.now() - timedelta(days=10),
            ],
            'is_current': [False, True, True, True],
            'version': [1, 2, 1, 1],
        })

        # Query current records
        current_records = scd2_data[scd2_data['is_current'] == True]

        assert len(current_records) == 3, "Should have 3 current records"
        assert set(current_records['customer_id']) == {1, 2, 3}, \
            "Should have one current record per customer"

    def test_query_historical_records(self):
        """Test querying historical records as of a date."""
        # Data with multiple versions
        base_date = datetime.now()

        scd2_data = pd.DataFrame({
            'customer_id': [1, 1, 2],
            'name': ['Alice', 'Alice Updated', 'Bob'],
            'effective_start_date': [
                base_date - timedelta(days=30),
                base_date - timedelta(days=5),
                base_date - timedelta(days=20),
            ],
            'effective_end_date': [
                base_date - timedelta(days=5),
                pd.NaT,
                pd.NaT,
            ],
            'is_current': [False, True, True],
            'version': [1, 2, 1],
        })

        # Query as of 10 days ago
        as_of_date = base_date - timedelta(days=10)

        historical = scd2_data[
            (scd2_data['effective_start_date'] <= as_of_date) &
            ((scd2_data['effective_end_date'].isna()) |
             (scd2_data['effective_end_date'] > as_of_date))
        ]

        # Should get Alice v1 and Bob v1
        assert len(historical) == 2, "Should have 2 records as of 10 days ago"
        assert historical[historical['customer_id'] == 1]['version'].iloc[0] == 1, \
            "Should get version 1 of Alice's record"


# ============================================================================
# Delta Table Optimization Tests
# ============================================================================

class TestDeltaTableOptimization:
    """Test Delta Lake table optimization."""

    def test_small_files_detection(self):
        """Test detection of small files that need compaction."""
        # Simulate file size metadata
        files = [
            {'path': 'file1.parquet', 'size_mb': 5},
            {'path': 'file2.parquet', 'size_mb': 3},
            {'path': 'file3.parquet', 'size_mb': 128},
            {'path': 'file4.parquet', 'size_mb': 2},
            {'path': 'file5.parquet', 'size_mb': 150},
        ]

        # Files smaller than 10MB should be flagged
        threshold_mb = 10
        small_files = [f for f in files if f['size_mb'] < threshold_mb]

        assert len(small_files) == 3, "Should detect 3 small files"
        total_small_size = sum(f['size_mb'] for f in small_files)
        assert total_small_size == 10, "Total size of small files should be 10MB"

    def test_optimize_recommendations(self):
        """Test optimization recommendations based on table stats."""
        # Table statistics
        table_stats = {
            'total_files': 1000,
            'avg_file_size_mb': 8,
            'total_size_gb': 7.8,
            'total_rows': 10_000_000,
            'partitions': 365,
        }

        recommendations = []

        # Check file count
        if table_stats['total_files'] > 100:
            recommendations.append('Run OPTIMIZE to reduce file count')

        # Check average file size
        if table_stats['avg_file_size_mb'] < 64:
            recommendations.append('Files are small, compaction recommended')

        # Check partition count
        if table_stats['partitions'] > 100:
            recommendations.append('Consider reducing partition granularity')

        assert len(recommendations) == 3, "Should have 3 optimization recommendations"

    def test_calculate_z_order_columns(self, sample_orders_data):
        """Test identification of columns for Z-ORDER optimization."""
        # Columns frequently used in filters should be Z-ORDER candidates
        high_cardinality_cols = []

        for col in ['customer_id', 'product_category', 'status']:
            if col in sample_orders_data.columns:
                cardinality = sample_orders_data[col].nunique()
                total_rows = len(sample_orders_data)

                # If cardinality is between 10% and 90% of total rows, good for Z-ORDER
                if 0.1 <= (cardinality / total_rows) <= 0.9:
                    high_cardinality_cols.append(col)

        # Should identify some columns
        assert len(high_cardinality_cols) > 0, \
            "Should identify columns suitable for Z-ORDER"

    def test_vacuum_dry_run(self):
        """Test VACUUM dry run to identify deletable files."""
        # Simulate file versions with timestamps
        current_time = datetime.now()
        retention_days = 7

        files = [
            {'path': 'file1.parquet', 'modified': current_time - timedelta(days=10)},
            {'path': 'file2.parquet', 'modified': current_time - timedelta(days=5)},
            {'path': 'file3.parquet', 'modified': current_time - timedelta(days=30)},
            {'path': 'file4.parquet', 'modified': current_time - timedelta(days=2)},
        ]

        # Files older than retention period can be vacuumed
        vacuum_threshold = current_time - timedelta(days=retention_days)
        deletable_files = [f for f in files if f['modified'] < vacuum_threshold]

        assert len(deletable_files) == 2, \
            "Should identify 2 files older than retention period"


# ============================================================================
# Data Freshness Tests
# ============================================================================

class TestDataFreshness:
    """Test data freshness and timeliness metrics."""

    def test_calculate_data_freshness(self, sample_orders_data):
        """Calculate data freshness metric."""
        current_time = datetime.now()

        # Get latest order date
        latest_order = sample_orders_data['order_date'].max()

        # Calculate freshness (hours since last update)
        if isinstance(latest_order, pd.Timestamp):
            freshness_hours = (current_time - latest_order).total_seconds() / 3600
        else:
            freshness_hours = 0

        # Data should be relatively fresh (depends on ingestion schedule)
        assert freshness_hours >= 0, "Freshness should be non-negative"

    def test_detect_stale_partitions(self):
        """Detect stale partitions that haven't been updated."""
        # Simulate partition metadata
        current_time = datetime.now()

        partitions = [
            {'partition': '2024-01-01', 'last_modified': current_time - timedelta(days=1)},
            {'partition': '2024-01-02', 'last_modified': current_time - timedelta(hours=2)},
            {'partition': '2024-01-03', 'last_modified': current_time - timedelta(days=10)},
            {'partition': '2024-01-04', 'last_modified': current_time - timedelta(hours=1)},
        ]

        # Partitions not updated in last 7 days are stale
        stale_threshold = current_time - timedelta(days=7)
        stale_partitions = [p for p in partitions if p['last_modified'] < stale_threshold]

        assert len(stale_partitions) == 1, "Should detect 1 stale partition"

    def test_sla_compliance(self):
        """Test SLA compliance for data availability."""
        # SLA: Data should be available within 2 hours of source update
        sla_hours = 2

        # Simulate ingestion times
        ingestion_records = [
            {'source_timestamp': datetime.now() - timedelta(hours=3),
             'target_timestamp': datetime.now() - timedelta(hours=2.5)},  # 0.5 hours latency - OK
            {'source_timestamp': datetime.now() - timedelta(hours=5),
             'target_timestamp': datetime.now() - timedelta(hours=2)},  # 3 hours latency - VIOLATED
            {'source_timestamp': datetime.now() - timedelta(hours=2),
             'target_timestamp': datetime.now() - timedelta(hours=1)},  # 1 hour latency - OK
        ]

        violations = []
        for record in ingestion_records:
            latency_hours = (record['target_timestamp'] - record['source_timestamp']).total_seconds() / 3600
            if latency_hours > sla_hours:
                violations.append(record)

        assert len(violations) == 1, "Should detect 1 SLA violation"


# ============================================================================
# Quality Score Tests
# ============================================================================

class TestQualityScoreCalculation:
    """Test overall data quality score calculation."""

    def test_calculate_weighted_quality_score(self):
        """Calculate weighted quality score across dimensions."""
        # Quality scores by dimension (0-100)
        dimension_scores = {
            'completeness': 95.0,
            'accuracy': 88.0,
            'consistency': 92.0,
            'timeliness': 85.0,
            'validity': 90.0,
        }

        # Weights for each dimension
        weights = {
            'completeness': 0.25,
            'accuracy': 0.25,
            'consistency': 0.20,
            'timeliness': 0.15,
            'validity': 0.15,
        }

        # Calculate weighted score
        total_score = sum(dimension_scores[dim] * weights[dim]
                         for dim in dimension_scores.keys())

        assert 80 <= total_score <= 100, \
            f"Quality score {total_score} should be between 80 and 100"
        assert abs(total_score - 90.45) < 0.1, \
            f"Quality score should be approximately 90.45 but got {total_score}"

    def test_quality_threshold_enforcement(self):
        """Test enforcement of quality thresholds."""
        quality_scores = [
            {'table': 'customers', 'score': 95.0},
            {'table': 'orders', 'score': 88.0},
            {'table': 'products', 'score': 72.0},  # Below threshold
            {'table': 'inventory', 'score': 91.0},
        ]

        threshold = 80.0

        failing_tables = [q for q in quality_scores if q['score'] < threshold]

        assert len(failing_tables) == 1, "Should detect 1 table below threshold"
        assert failing_tables[0]['table'] == 'products', \
            "Products table should be flagged"

    def test_quality_trend_analysis(self):
        """Test quality score trend analysis."""
        # Historical quality scores
        historical_scores = [
            {'date': '2024-01-01', 'score': 85.0},
            {'date': '2024-01-02', 'score': 87.0},
            {'date': '2024-01-03', 'score': 84.0},
            {'date': '2024-01-04', 'score': 90.0},
            {'date': '2024-01-05', 'score': 89.0},
        ]

        scores = [h['score'] for h in historical_scores]

        # Calculate trend (simple moving average)
        window_size = 3
        moving_avg = []
        for i in range(len(scores) - window_size + 1):
            avg = sum(scores[i:i+window_size]) / window_size
            moving_avg.append(avg)

        # Latest moving average should be around 87.7
        assert len(moving_avg) == 3
        assert 87.0 <= moving_avg[-1] <= 90.0, \
            f"Latest moving average {moving_avg[-1]} out of expected range"


# ============================================================================
# Integration Tests
# ============================================================================

class TestDataQualityIntegration:
    """End-to-end data quality integration tests."""

    def test_full_data_quality_pipeline(self, sample_customers_data, dq_validator):
        """Run full data quality pipeline on sample data."""
        results = {
            'dataset': 'customers',
            'row_count': len(sample_customers_data),
            'timestamp': datetime.now().isoformat(),
        }

        # Completeness
        required_cols = ['customer_id', 'email', 'first_name', 'last_name']
        completeness = dq_validator.check_completeness(sample_customers_data, required_cols)
        results['completeness'] = completeness

        # Uniqueness
        uniqueness = dq_validator.check_uniqueness(sample_customers_data, ['customer_id', 'email'])
        results['uniqueness'] = uniqueness

        # PII Detection
        pii = dq_validator.detect_pii(sample_customers_data)
        results['pii_detected'] = pii

        # Verify results structure
        assert 'completeness' in results
        assert 'uniqueness' in results
        assert 'pii_detected' in results
        assert results['row_count'] == 100

        # All required columns should be complete
        for col in required_cols:
            assert results['completeness'][col]['complete']

    def test_quality_report_generation(self, sample_customers_data, dq_validator):
        """Generate comprehensive quality report."""
        report = {
            'table_name': 'customers',
            'execution_time': datetime.now().isoformat(),
            'metrics': {}
        }

        # Add various metrics
        all_cols = sample_customers_data.columns.tolist()

        completeness = dq_validator.check_completeness(sample_customers_data, all_cols)
        complete_cols = sum(1 for r in completeness.values() if r['complete'])
        report['metrics']['completeness_score'] = (complete_cols / len(all_cols)) * 100

        uniqueness = dq_validator.check_uniqueness(sample_customers_data, ['customer_id'])
        report['metrics']['uniqueness_score'] = 100 if uniqueness['customer_id']['is_unique'] else 0

        pii = dq_validator.detect_pii(sample_customers_data)
        report['metrics']['pii_columns'] = [p['column'] for p in pii]

        # Verify report
        assert report['metrics']['completeness_score'] == 100.0
        assert report['metrics']['uniqueness_score'] == 100.0
        assert len(report['metrics']['pii_columns']) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
