"""
Complete validation tests for Module 07: Batch Processing

Tests all key concepts:
- Batch reading and chunking
- Memory optimization
- Data partitioning
- PySpark operations
- Performance optimization
"""

import pytest
import pandas as pd

# Markers
pytestmark = pytest.mark.integration


class TestBatchBasics:
    """Test batch processing fundamentals."""

    def test_chunked_reading(self, sample_csv_file):
        """Test reading large files in chunks."""
        chunk_size = 1000
        total_rows = 0

        for chunk in pd.read_csv(sample_csv_file, chunksize=chunk_size):
            assert len(chunk) <= chunk_size
            assert 'transaction_id' in chunk.columns
            total_rows += len(chunk)

        # Verify all rows read
        df_full = pd.read_csv(sample_csv_file)
        assert total_rows == len(df_full)

    def test_memory_optimization(self, sample_transactions_df):
        """Test memory usage reduction through dtype optimization."""
        df = sample_transactions_df.copy()

        # Calculate initial memory
        initial_memory = df.memory_usage(deep=True).sum() / (1024 ** 2)

        # Optimize dtypes
        df['quantity'] = df['quantity'].astype('uint8')
        df['status'] = df['status'].astype('category')
        df['category'] = df['category'].astype('category')
        df['country'] = df['country'].astype('category')

        # Calculate optimized memory
        optimized_memory = df.memory_usage(deep=True).sum() / (1024 ** 2)

        # Should reduce memory
        assert optimized_memory < initial_memory
        reduction_pct = (initial_memory - optimized_memory) / initial_memory * 100
        assert reduction_pct > 10  # At least 10% reduction

    def test_incremental_aggregation(self, sample_csv_file):
        """Test aggregating data incrementally."""
        chunk_size = 2000

        # Incremental aggregation
        total_count = 0
        total_amount = 0
        category_counts = {}

        for chunk in pd.read_csv(sample_csv_file, chunksize=chunk_size):
            total_count += len(chunk)
            total_amount += chunk['amount'].sum()

            for cat, count in chunk['category'].value_counts().items():
                category_counts[cat] = category_counts.get(cat, 0) + count

        # Compare with full load
        df_full = pd.read_csv(sample_csv_file)

        assert total_count == len(df_full)
        assert abs(total_amount - df_full['amount'].sum()) < 0.01
        assert sum(category_counts.values()) == total_count


class TestDataPartitioning:
    """Test data partitioning strategies."""

    def test_date_partitioning(self, sample_transactions_df, temp_dir):
        """Test date-based partitioning."""
        df = sample_transactions_df.copy()
        df['year'] = df['timestamp'].dt.year
        df['month'] = df['timestamp'].dt.month
        df['day'] = df['timestamp'].dt.day

        # Write partitioned
        output_dir = temp_dir / "date_partitioned"

        for (year, month, day), group in df.groupby(['year', 'month', 'day']):
            partition_dir = output_dir / f"year={year}" / f"month={month:02d}" / f"day={day:02d}"
            partition_dir.mkdir(parents=True, exist_ok=True)
            group.to_parquet(partition_dir / "data.parquet", index=False)

        # Verify partitions exist
        assert output_dir.exists()
        partition_files = list(output_dir.rglob("*.parquet"))
        assert len(partition_files) > 0

        # Read specific partition
        first_partition = partition_files[0]
        df_partition = pd.read_parquet(first_partition)
        assert len(df_partition) > 0

    def test_partition_pruning_benefit(self, partitioned_data):
        """Test that partition pruning reduces data read."""
        # Read all data
        all_files = list(partitioned_data.rglob("*.parquet"))

        # Read specific partition
        specific_partition = all_files[0].parent
        df_subset = pd.read_parquet(specific_partition)

        # Subset should be smaller than full dataset
        df_full = pd.concat([pd.read_parquet(f) for f in all_files])

        assert len(df_subset) < len(df_full)
        assert len(df_subset) > 0


@pytest.mark.spark
class TestPySparkOperations:
    """Test PySpark DataFrame operations."""

    def test_spark_read_write(self, spark_session, sample_transactions_df, temp_dir):
        """Test basic Spark read/write."""
        # Write with pandas
        input_path = temp_dir / "input.parquet"
        sample_transactions_df.to_parquet(input_path, index=False)

        # Read with Spark
        df_spark = spark_session.read.parquet(str(input_path))

        assert df_spark.count() == len(sample_transactions_df)
        assert 'transaction_id' in df_spark.columns

        # Write with Spark
        output_path = temp_dir / "output.parquet"
        df_spark.write.parquet(str(output_path))

        # Verify
        assert output_path.exists()

    def test_spark_filtering(self, spark_df_transactions):
        """Test Spark filtering operations."""
        df = spark_df_transactions

        # Filter
        df_filtered = df.filter(df.amount > 500)

        count = df_filtered.count()
        assert count > 0
        assert count < df.count()

        # Verify all amounts > 500
        amounts = [row.amount for row in df_filtered.collect()]
        assert all(amt > 500 for amt in amounts)

    def test_spark_aggregation(self, spark_df_transactions):
        """Test Spark aggregation operations."""
        from pyspark.sql.functions import sum, count, avg

        df = spark_df_transactions

        # Aggregate by category
        df_agg = df.groupBy("category").agg(
            sum("amount").alias("total"),
            count("*").alias("count"),
            avg("amount").alias("avg")
        )

        results = df_agg.collect()

        # Verify results
        assert len(results) > 0
        for row in results:
            assert row.total > 0
            assert row.count > 0
            assert row.avg > 0

    def test_spark_join(self, spark_df_transactions, spark_df_users):
        """Test Spark join operations."""
        transactions = spark_df_transactions
        users = spark_df_users

        # Join
        df_joined = transactions.join(users, "user_id", "inner")

        # Verify
        assert df_joined.count() > 0

        # Should have columns from both DataFrames
        assert 'transaction_id' in df_joined.columns
        assert 'email' in df_joined.columns
        assert 'amount' in df_joined.columns
        assert 'tier' in df_joined.columns


@pytest.mark.performance
class TestPerformanceOptimization:
    """Test performance optimization techniques."""

    @pytest.mark.spark
    def test_caching_benefits(self, spark_df_transactions):
        """Test that caching improves performance on repeated access."""
        import time

        df = spark_df_transactions

        # First count (no cache)
        start = time.time()
        count1 = df.count()
        time1 = time.time() - start

        # Cache
        df.cache()

        # Second count (cached)
        start = time.time()
        count2 = df.count()
        time2 = time.time() - start

        # Third count (should use cache)
        start = time.time()
        count3 = df.count()
        time3 = time.time() - start

        # Verify counts match
        assert count1 == count2 == count3

        # Cached access should be faster (usually 2-10x)
        # Note: Small datasets may not show significant difference
        assert time3 <= time2

        # Cleanup
        df.unpersist()

    @pytest.mark.spark
    def test_repartitioning(self, spark_df_transactions):
        """Test repartitioning for better parallelism."""
        df = spark_df_transactions

        # Check initial partitions
        initial_partitions = df.rdd.getNumPartitions()

        # Repartition
        df_repart = df.repartition(8)
        new_partitions = df_repart.rdd.getNumPartitions()

        assert new_partitions == 8
        assert new_partitions != initial_partitions

        # Verify data integrity
        assert df.count() == df_repart.count()


class TestDataQuality:
    """Test data quality checks."""

    def test_null_detection(self, sample_transactions_df):
        """Test detecting null values."""
        df = sample_transactions_df.copy()

        # Check initial nulls
        null_counts = df.isnull().sum()

        # Should have no nulls in critical columns
        assert null_counts['transaction_id'] == 0
        assert null_counts['amount'] == 0

        # Introduce nulls
        df.loc[0, 'amount'] = None

        # Detect
        null_counts = df.isnull().sum()
        assert null_counts['amount'] == 1

    def test_duplicate_detection(self, sample_transactions_df):
        """Test detecting duplicate records."""
        df = sample_transactions_df.copy()

        # Check initial duplicates
        initial_dupes = df.duplicated(subset=['transaction_id']).sum()
        assert initial_dupes == 0

        # Introduce duplicate
        df = pd.concat([df, df.iloc[[0]]], ignore_index=True)

        # Detect
        dupes = df.duplicated(subset=['transaction_id']).sum()
        assert dupes == 1

    def test_value_range_validation(self, sample_transactions_df):
        """Test validating value ranges."""
        df = sample_transactions_df

        # Check amount range
        assert df['amount'].min() >= 0
        assert df['amount'].max() <= 10000

        # Check quantity range
        assert df['quantity'].min() >= 1
        assert df['quantity'].max() <= 100


class TestETLPipeline:
    """Test complete ETL pipeline."""

    @pytest.mark.spark
    def test_end_to_end_pipeline(
        self,
        spark_session,
        spark_df_transactions,
        spark_df_users,
        temp_dir
    ):
        """Test complete ETL pipeline."""
        from pyspark.sql.functions import col

        # Extract
        transactions = spark_df_transactions
        users = spark_df_users

        # Transform
        # 1. Filter completed transactions
        df_completed = transactions.filter(col("status") == "completed")

        # 2. Join with users
        df_enriched = df_completed.join(users, "user_id", "inner")

        # 3. Aggregate by country
        df_agg = df_enriched.groupBy("country").agg({
            "amount": "sum",
            "transaction_id": "count"
        })

        # Load
        output_path = temp_dir / "output"
        df_agg.write.parquet(str(output_path))

        # Validate
        assert output_path.exists()

        # Read back and verify
        df_result = spark_session.read.parquet(str(output_path))
        assert df_result.count() > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
