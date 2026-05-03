"""
Batch Layer Implementation for Lambda Architecture

This module implements the batch processing component of Lambda Architecture.
It processes ALL historical data to create accurate aggregate views using Apache Spark.

Key Responsibilities:
1. Read raw data from S3 (orders, events, logs)
2. Transform and aggregate using Spark SQL
3. Write batch views to S3 (Parquet, partitioned)
4. Register tables with AWS Glue for Athena queries
5. Schedule daily ETL (recommended: 03:00 AM)

Author: Training Module 18
"""

import json
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

import boto3
import pandas as pd
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BatchLayerProcessor:
    """
    Batch Layer Processor for Lambda Architecture.

    Processes historical data using Spark to create accurate aggregate views.
    Runs daily on schedule (typically 03:00 AM) to incorporate yesterday's data.
    """

    def __init__(
        self,
        raw_bucket: str = "lambda-arch-raw-data",
        batch_views_bucket: str = "lambda-arch-batch-views",
        glue_database: str = "lambda_arch_db",
        region: str = "us-east-1",
        use_localstack: bool = False
    ):
        """
        Initialize Batch Layer Processor.

        Args:
            raw_bucket: S3 bucket containing raw events
            batch_views_bucket: S3 bucket for batch views output
            glue_database: AWS Glue database name
            region: AWS region
            use_localstack: If True, use LocalStack endpoints
        """
        self.raw_bucket = raw_bucket
        self.batch_views_bucket = batch_views_bucket
        self.glue_database = glue_database
        self.region = region

        # AWS clients
        endpoint_url = "http://localhost:4566" if use_localstack else None

        self.s3 = boto3.client('s3', region_name=region, endpoint_url=endpoint_url)
        self.glue = boto3.client('glue', region_name=region, endpoint_url=endpoint_url)
        self.athena = boto3.client('athena', region_name=region, endpoint_url=endpoint_url)

        logger.info(f"BatchLayerProcessor initialized (LocalStack: {use_localstack})")

    def setup_infrastructure(self) -> Dict[str, Any]:
        """
        Create S3 buckets, Glue database, and Athena workgroup.

        Returns:
            Dict with created resource ARNs
        """
        logger.info("=== Setting Up Batch Layer Infrastructure ===")

        results = {}

        # Create S3 buckets
        for bucket in [self.raw_bucket, self.batch_views_bucket]:
            try:
                self.s3.create_bucket(Bucket=bucket)
                logger.info(f"✅ Created S3 bucket: {bucket}")
                results[f's3_{bucket}'] = f"s3://{bucket}"
            except ClientError as e:
                if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                    logger.info(f"✅ S3 bucket already exists: {bucket}")
                    results[f's3_{bucket}'] = f"s3://{bucket}"
                else:
                    logger.error(f"❌ Failed to create bucket {bucket}: {e}")
                    raise

        # Create Glue database
        try:
            self.glue.create_database(
                DatabaseInput={
                    'Name': self.glue_database,
                    'Description': 'Lambda Architecture Batch Views'
                }
            )
            logger.info(f"✅ Created Glue database: {self.glue_database}")
            results['glue_database'] = self.glue_database
        except ClientError as e:
            if e.response['Error']['Code'] == 'AlreadyExistsException':
                logger.info(f"✅ Glue database already exists: {self.glue_database}")
                results['glue_database'] = self.glue_database
            else:
                logger.error(f"❌ Failed to create Glue database: {e}")
                raise

        return results

    def generate_sample_data(self, num_records: int = 10000) -> None:
        """
        Generate sample order data for testing.

        Args:
            num_records: Number of order records to generate
        """
        logger.info(f"=== Generating {num_records:,} Sample Orders ===")

        import random
        from datetime import datetime, timedelta

        # Generate orders for last 90 days
        orders = []
        start_date = datetime.now() - timedelta(days=90)

        user_ids = [f"user_{i:04d}" for i in range(1, 101)]  # 100 users
        product_ids = [f"prod_{i:03d}" for i in range(1, 51)]  # 50 products

        for i in range(num_records):
            order_date = start_date + timedelta(
                seconds=random.randint(0, 90 * 24 * 3600)
            )

            order = {
                'order_id': f"ord_{i:08d}",
                'user_id': random.choice(user_ids),
                'product_id': random.choice(product_ids),
                'amount': round(random.uniform(10.0, 200.0), 2),
                'quantity': random.randint(1, 5),
                'order_date': order_date.strftime('%Y-%m-%d'),
                'order_timestamp': order_date.isoformat(),
                'status': random.choice(['completed', 'completed', 'completed', 'pending', 'cancelled'])
            }
            orders.append(order)

        # Convert to DataFrame
        df = pd.DataFrame(orders)

        # Save as Parquet partitioned by date
        logger.info("Writing partitioned data to S3...")

        for date in df['order_date'].unique():
            date_df = df[df['order_date'] == date]

            # Convert to Parquet bytes
            parquet_buffer = date_df.to_parquet(index=False, compression='snappy')

            # Upload to S3
            year, month, day = date.split('-')
            key = f"orders/year={year}/month={month}/day={day}/data.parquet"

            self.s3.put_object(
                Bucket=self.raw_bucket,
                Key=key,
                Body=parquet_buffer
            )

        logger.info(f"✅ Generated {num_records:,} orders across {len(df['order_date'].unique())} days")
        logger.info(f"   Users: {df['user_id'].nunique()}")
        logger.info(f"   Total Revenue: ${df[df['status']=='completed']['amount'].sum():,.2f}")
        logger.info(f"   Location: s3://{self.raw_bucket}/orders/")

    def read_raw_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Read raw order data from S3.

        Args:
            start_date: Start date (YYYY-MM-DD) or None for all data
            end_date: End date (YYYY-MM-DD) or None for today

        Returns:
            DataFrame with raw orders
        """
        logger.info("=== Reading Raw Data from S3 ===")
        logger.info(f"   Bucket: s3://{self.raw_bucket}/orders/")

        if start_date:
            logger.info(f"   Date Range: {start_date} to {end_date or 'today'}")

        # List all Parquet files
        all_data = []

        try:
            paginator = self.s3.get_paginator('list_objects_v2')

            for page in paginator.paginate(Bucket=self.raw_bucket, Prefix='orders/'):
                if 'Contents' not in page:
                    continue

                for obj in page['Contents']:
                    key = obj['Key']

                    # Filter by date if specified
                    if start_date and not self._key_in_date_range(key, start_date, end_date):
                        continue

                    # Read Parquet file
                    response = self.s3.get_object(Bucket=self.raw_bucket, Key=key)
                    df = pd.read_parquet(response['Body'])
                    all_data.append(df)

            if not all_data:
                logger.warning("⚠️  No data found in S3")
                return pd.DataFrame()

            # Concatenate all partitions
            combined = pd.concat(all_data, ignore_index=True)
            logger.info(f"✅ Loaded {len(combined):,} records")

            return combined

        except ClientError as e:
            logger.error(f"❌ Failed to read S3 data: {e}")
            raise

    def _key_in_date_range(self, key: str, start_date: str, end_date: Optional[str]) -> bool:
        """
        Check if S3 key falls within date range.

        Args:
            key: S3 key (e.g., orders/year=2026/month=03/day=09/data.parquet)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD) or None

        Returns:
            True if key is in range
        """
        try:
            # Extract date from partition key
            parts = key.split('/')
            year = next((p.split('=')[1] for p in parts if p.startswith('year=')), None)
            month = next((p.split('=')[1] for p in parts if p.startswith('month=')), None)
            day = next((p.split('=')[1] for p in parts if p.startswith('day=')), None)

            if not (year and month and day):
                return True  # Non-partitioned, include

            file_date = f"{year}-{month}-{day}"

            if file_date < start_date:
                return False

            if end_date and file_date > end_date:
                return False

            return True

        except Exception:
            return True  # On error, include file

    def calculate_user_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate user-level metrics (lifetime value, order count, etc.).

        Args:
            df: Raw orders DataFrame

        Returns:
            DataFrame with user metrics
        """
        logger.info("=== Calculating User Metrics ===")

        # Filter completed orders only
        completed = df[df['status'] == 'completed'].copy()

        logger.info(f"   Total Orders: {len(df):,}")
        logger.info(f"   Completed Orders: {len(completed):,}")

        # Aggregate by user
        user_metrics = completed.groupby('user_id').agg({
            'order_id': 'count',  # Total orders
            'amount': ['sum', 'mean', 'std'],  # Revenue stats
            'order_date': ['min', 'max']  # First and last order
        }).reset_index()

        # Flatten column names
        user_metrics.columns = [
            'user_id',
            'lifetime_orders',
            'lifetime_revenue',
            'avg_order_value',
            'std_order_value',
            'first_order_date',
            'last_order_date'
        ]

        # Calculate recency (days since last order)
        user_metrics['last_order_date'] = pd.to_datetime(user_metrics['last_order_date'])
        user_metrics['days_since_last_order'] = (
            datetime.now() - user_metrics['last_order_date']
        ).dt.days

        # Calculate frequency (orders per month)
        user_metrics['first_order_date'] = pd.to_datetime(user_metrics['first_order_date'])
        user_metrics['customer_tenure_days'] = (
            user_metrics['last_order_date'] - user_metrics['first_order_date']
        ).dt.days + 1

        user_metrics['orders_per_month'] = (
            user_metrics['lifetime_orders'] /
            (user_metrics['customer_tenure_days'] / 30.0)
        )

        # Calculate customer segment (RFM)
        user_metrics['rfm_score'] = (
            (user_metrics['days_since_last_order'] < 30).astype(int) * 3 +  # Recent
            (user_metrics['orders_per_month'] > 2).astype(int) * 2 +  # Frequent
            (user_metrics['lifetime_revenue'] > 500).astype(int) * 1  # Monetary
        )

        user_metrics['segment'] = user_metrics['rfm_score'].map({
            6: 'Champions',  # Recent + Frequent + High Value
            5: 'Loyal Customers',
            4: 'Potential Loyalists',
            3: 'New Customers',
            2: 'At Risk',
            1: 'Hibernating',
            0: 'Lost'
        })

        logger.info(f"✅ Calculated metrics for {len(user_metrics):,} users")
        logger.info(f"   Total Revenue: ${user_metrics['lifetime_revenue'].sum():,.2f}")

        return user_metrics

    def calculate_cohort_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate cohort retention metrics.

        Args:
            df: Raw orders DataFrame

        Returns:
            DataFrame with cohort metrics
        """
        logger.info("=== Calculating Cohort Metrics ===")

        completed = df[df['status'] == 'completed'].copy()
        completed['order_date'] = pd.to_datetime(completed['order_date'])

        # Determine user cohort (month of first order)
        user_first_order = completed.groupby('user_id')['order_date'].min().reset_index()
        user_first_order.columns = ['user_id', 'cohort_date']
        user_first_order['cohort_month'] = user_first_order['cohort_date'].dt.to_period('M')

        # Merge cohort with orders
        orders_with_cohort = completed.merge(user_first_order, on='user_id')
        orders_with_cohort['order_month'] = orders_with_cohort['order_date'].dt.to_period('M')

        # Calculate months since first order
        orders_with_cohort['months_since_first'] = (
            (orders_with_cohort['order_month'] - orders_with_cohort['cohort_month']).apply(lambda x: x.n)
        )

        # Aggregate: cohort × months_since_first → retention
        cohort_metrics = orders_with_cohort.groupby(
            ['cohort_month', 'months_since_first']
        ).agg({
            'user_id': 'nunique',  # Active users
            'order_id': 'count',  # Total orders
            'amount': 'sum'  # Revenue
        }).reset_index()

        cohort_metrics.columns = [
            'cohort_month',
            'months_since_first',
            'active_users',
            'orders',
            'revenue'
        ]

        # Calculate cohort size (month 0)
        cohort_sizes = cohort_metrics[cohort_metrics['months_since_first'] == 0].set_index('cohort_month')['active_users']

        # Calculate retention rate
        cohort_metrics['cohort_size'] = cohort_metrics['cohort_month'].map(cohort_sizes)
        cohort_metrics['retention_rate'] = (
            cohort_metrics['active_users'] / cohort_metrics['cohort_size']
        )

        cohort_metrics['cohort_month'] = cohort_metrics['cohort_month'].astype(str)

        logger.info(f"✅ Calculated cohort metrics for {cohort_metrics['cohort_month'].nunique()} cohorts")

        return cohort_metrics

    def calculate_product_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate product-level metrics (popularity, revenue, co-purchase).

        Args:
            df: Raw orders DataFrame

        Returns:
            DataFrame with product metrics
        """
        logger.info("=== Calculating Product Metrics ===")

        completed = df[df['status'] == 'completed'].copy()

        # Aggregate by product
        product_metrics = completed.groupby('product_id').agg({
            'order_id': 'count',
            'amount': 'sum',
            'user_id': 'nunique'
        }).reset_index()

        product_metrics.columns = [
            'product_id',
            'total_orders',
            'total_revenue',
            'unique_buyers'
        ]

        product_metrics['avg_revenue_per_order'] = (
            product_metrics['total_revenue'] / product_metrics['total_orders']
        )

        # Rank by revenue
        product_metrics['revenue_rank'] = product_metrics['total_revenue'].rank(
            method='dense',
            ascending=False
        ).astype(int)

        logger.info(f"✅ Calculated metrics for {len(product_metrics)} products")
        logger.info(f"   Top Product: {product_metrics.iloc[0]['product_id']} (${product_metrics.iloc[0]['total_revenue']:,.2f})")

        return product_metrics

    def write_batch_views(
        self,
        user_metrics: pd.DataFrame,
        cohort_metrics: pd.DataFrame,
        product_metrics: pd.DataFrame,
        batch_date: str
    ) -> Dict[str, str]:
        """
        Write batch views to S3 as Parquet files.

        Args:
            user_metrics: User-level metrics
            cohort_metrics: Cohort retention metrics
            product_metrics: Product-level metrics
            batch_date: Batch run date (YYYY-MM-DD)

        Returns:
            Dict with S3 locations
        """
        logger.info(f"=== Writing Batch Views (batch_date={batch_date}) ===")

        results = {}

        # Write user metrics
        user_parquet = user_metrics.to_parquet(index=False, compression='snappy')
        user_key = f"user_metrics/batch_date={batch_date}/data.parquet"
        self.s3.put_object(
            Bucket=self.batch_views_bucket,
            Key=user_key,
            Body=user_parquet
        )
        logger.info(f"✅ Wrote user metrics: s3://{self.batch_views_bucket}/{user_key}")
        results['user_metrics'] = f"s3://{self.batch_views_bucket}/{user_key}"

        # Write cohort metrics
        cohort_parquet = cohort_metrics.to_parquet(index=False, compression='snappy')
        cohort_key = f"cohort_metrics/batch_date={batch_date}/data.parquet"
        self.s3.put_object(
            Bucket=self.batch_views_bucket,
            Key=cohort_key,
            Body=cohort_parquet
        )
        logger.info(f"✅ Wrote cohort metrics: s3://{self.batch_views_bucket}/{cohort_key}")
        results['cohort_metrics'] = f"s3://{self.batch_views_bucket}/{cohort_key}"

        # Write product metrics
        product_parquet = product_metrics.to_parquet(index=False, compression='snappy')
        product_key = f"product_metrics/batch_date={batch_date}/data.parquet"
        self.s3.put_object(
            Bucket=self.batch_views_bucket,
            Key=product_key,
            Body=product_parquet
        )
        logger.info(f"✅ Wrote product metrics: s3://{self.batch_views_bucket}/{product_key}")
        results['product_metrics'] = f"s3://{self.batch_views_bucket}/{product_key}"

        return results

    def create_glue_tables(self) -> None:
        """
        Create Glue tables for Athena queries.
        """
        logger.info("=== Creating Glue Tables ===")

        tables = [
            {
                'name': 'user_metrics',
                'location': f's3://{self.batch_views_bucket}/user_metrics/',
                'columns': [
                    {'Name': 'user_id', 'Type': 'string'},
                    {'Name': 'lifetime_orders', 'Type': 'bigint'},
                    {'Name': 'lifetime_revenue', 'Type': 'double'},
                    {'Name': 'avg_order_value', 'Type': 'double'},
                    {'Name': 'std_order_value', 'Type': 'double'},
                    {'Name': 'first_order_date', 'Type': 'string'},
                    {'Name': 'last_order_date', 'Type': 'string'},
                    {'Name': 'days_since_last_order', 'Type': 'int'},
                    {'Name': 'customer_tenure_days', 'Type': 'int'},
                    {'Name': 'orders_per_month', 'Type': 'double'},
                    {'Name': 'rfm_score', 'Type': 'int'},
                    {'Name': 'segment', 'Type': 'string'}
                ],
                'partition_keys': [{'Name': 'batch_date', 'Type': 'string'}]
            },
            {
                'name': 'cohort_metrics',
                'location': f's3://{self.batch_views_bucket}/cohort_metrics/',
                'columns': [
                    {'Name': 'cohort_month', 'Type': 'string'},
                    {'Name': 'months_since_first', 'Type': 'int'},
                    {'Name': 'active_users', 'Type': 'bigint'},
                    {'Name': 'orders', 'Type': 'bigint'},
                    {'Name': 'revenue', 'Type': 'double'},
                    {'Name': 'cohort_size', 'Type': 'bigint'},
                    {'Name': 'retention_rate', 'Type': 'double'}
                ],
                'partition_keys': [{'Name': 'batch_date', 'Type': 'string'}]
            },
            {
                'name': 'product_metrics',
                'location': f's3://{self.batch_views_bucket}/product_metrics/',
                'columns': [
                    {'Name': 'product_id', 'Type': 'string'},
                    {'Name': 'total_orders', 'Type': 'bigint'},
                    {'Name': 'total_revenue', 'Type': 'double'},
                    {'Name': 'unique_buyers', 'Type': 'bigint'},
                    {'Name': 'avg_revenue_per_order', 'Type': 'double'},
                    {'Name': 'revenue_rank', 'Type': 'int'}
                ],
                'partition_keys': [{'Name': 'batch_date', 'Type': 'string'}]
            }
        ]

        for table_def in tables:
            try:
                self.glue.create_table(
                    DatabaseName=self.glue_database,
                    TableInput={
                        'Name': table_def['name'],
                        'StorageDescriptor': {
                            'Columns': table_def['columns'],
                            'Location': table_def['location'],
                            'InputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat',
                            'OutputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat',
                            'SerdeInfo': {
                                'SerializationLibrary': 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
                            }
                        },
                        'PartitionKeys': table_def['partition_keys']
                    }
                )
                logger.info(f"✅ Created Glue table: {self.glue_database}.{table_def['name']}")

            except ClientError as e:
                if e.response['Error']['Code'] == 'AlreadyExistsException':
                    logger.info(f"✅ Glue table already exists: {table_def['name']}")
                else:
                    logger.error(f"❌ Failed to create table {table_def['name']}: {e}")
                    raise

    def add_partition(self, table_name: str, batch_date: str) -> None:
        """
        Add partition to Glue table.

        Args:
            table_name: Glue table name
            batch_date: Partition value (YYYY-MM-DD)
        """
        try:
            self.glue.create_partition(
                DatabaseName=self.glue_database,
                TableName=table_name,
                PartitionInput={
                    'Values': [batch_date],
                    'StorageDescriptor': {
                        'Location': f's3://{self.batch_views_bucket}/{table_name}/batch_date={batch_date}/',
                        'InputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat',
                        'OutputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat',
                        'SerdeInfo': {
                            'SerializationLibrary': 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
                        }
                    }
                }
            )
            logger.info(f"✅ Added partition to {table_name}: batch_date={batch_date}")

        except ClientError as e:
            if e.response['Error']['Code'] == 'AlreadyExistsException':
                logger.info(f"✅ Partition already exists: {table_name} (batch_date={batch_date})")
            else:
                logger.warning(f"⚠️  Failed to add partition: {e}")

    def run_batch_job(
        self,
        batch_date: Optional[str] = None,
        incremental: bool = True
    ) -> Dict[str, Any]:
        """
        Execute complete batch processing job.

        Args:
            batch_date: Batch run date (YYYY-MM-DD) or None for today
            incremental: If True, only process new data since last batch

        Returns:
            Dict with execution statistics
        """
        if not batch_date:
            batch_date = datetime.now().strftime('%Y-%m-%d')

        logger.info("=" * 60)
        logger.info("=== Batch Layer Execution ===")
        logger.info(f"📅 Batch Date: {batch_date}")
        logger.info(f"🔄 Mode: {'Incremental' if incremental else 'Full Reprocessing'}")
        logger.info("=" * 60)

        start_time = datetime.now()

        # Determine date range
        if incremental:
            # Process data from last batch date to today
            # In production, query Glue to find last batch_date
            end_date = batch_date
            start_date = (datetime.strptime(batch_date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
            logger.info(f"   📊 Processing Range: {start_date} to {end_date}")
        else:
            # Full reprocessing
            start_date = None
            end_date = batch_date
            logger.info(f"   📊 Processing: All data up to {end_date}")

        # Read raw data
        raw_df = self.read_raw_data(start_date, end_date)

        if raw_df.empty:
            logger.warning("⚠️  No data to process")
            return {'status': 'no_data', 'batch_date': batch_date}

        # Calculate metrics
        user_metrics = self.calculate_user_metrics(raw_df)
        cohort_metrics = self.calculate_cohort_metrics(raw_df)
        product_metrics = self.calculate_product_metrics(raw_df)

        # Write to S3
        locations = self.write_batch_views(
            user_metrics,
            cohort_metrics,
            product_metrics,
            batch_date
        )

        # Update Glue partitions
        for table_name in ['user_metrics', 'cohort_metrics', 'product_metrics']:
            self.add_partition(table_name, batch_date)

        # Execution stats
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        stats = {
            'status': 'success',
            'batch_date': batch_date,
            'records_processed': len(raw_df),
            'users': len(user_metrics),
            'cohorts': cohort_metrics['cohort_month'].nunique(),
            'products': len(product_metrics),
            'total_revenue': float(user_metrics['lifetime_revenue'].sum()),
            'duration_seconds': duration,
            'output_locations': locations
        }

        logger.info("=" * 60)
        logger.info("=== Batch Job Complete ===")
        logger.info(f"✅ Status: {stats['status']}")
        logger.info(f"   Records Processed: {stats['records_processed']:,}")
        logger.info(f"   Users: {stats['users']:,}")
        logger.info(f"   Cohorts: {stats['cohorts']}")
        logger.info(f"   Products: {stats['products']}")
        logger.info(f"   Total Revenue: ${stats['total_revenue']:,.2f}")
        logger.info(f"⏱️  Duration: {duration:.1f} seconds")
        logger.info(f"💰 Estimated Cost: ${self._estimate_cost(len(raw_df), duration):.2f}")
        logger.info("=" * 60)

        return stats

    def _estimate_cost(self, records: int, duration_seconds: float) -> float:
        """
        Estimate AWS Glue cost.

        Glue Pricing: $0.44 per DPU-hour
        Default: 2 DPUs minimum (can scale to 100+)

        Args:
            records: Number of records processed
            duration_seconds: Job duration

        Returns:
            Estimated cost in USD
        """
        # Estimate DPUs needed (2 DPUs per million records)
        dpus = max(2, int(records / 500_000))

        # Round up to nearest minute (Glue bills per second, 10-min minimum)
        duration_hours = max(duration_seconds / 3600, 10 / 60)

        cost = dpus * duration_hours * 0.44
        return cost

    def query_athena(self, sql: str, output_location: str = None) -> pd.DataFrame:
        """
        Execute Athena query on batch views.

        Args:
            sql: SQL query
            output_location: S3 location for query results (optional)

        Returns:
            DataFrame with query results
        """
        if not output_location:
            output_location = f"s3://{self.batch_views_bucket}/athena-results/"

        logger.info("=== Executing Athena Query ===")
        logger.info(f"   Query: {sql[:100]}...")

        try:
            # Start query execution
            response = self.athena.start_query_execution(
                QueryString=sql,
                QueryExecutionContext={'Database': self.glue_database},
                ResultConfiguration={'OutputLocation': output_location}
            )

            query_execution_id = response['QueryExecutionId']

            # Wait for completion
            import time
            while True:
                status_response = self.athena.get_query_execution(
                    QueryExecutionId=query_execution_id
                )

                status = status_response['QueryExecution']['Status']['State']

                if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                    break

                time.sleep(1)

            if status != 'SUCCEEDED':
                error = status_response['QueryExecution']['Status'].get('StateChangeReason', 'Unknown')
                logger.error(f"❌ Query failed: {error}")
                raise Exception(f"Athena query failed: {error}")

            # Get results
            results = self.athena.get_query_results(QueryExecutionId=query_execution_id)

            # Parse to DataFrame
            columns = [col['Label'] for col in results['ResultSet']['ResultSetMetadata']['ColumnInfo']]
            rows = results['ResultSet']['Rows'][1:]  # Skip header

            data = []
            for row in rows:
                data.append([field.get('VarCharValue', '') for field in row['Data']])

            df = pd.DataFrame(data, columns=columns)

            # Get statistics
            stats = status_response['QueryExecution']['Statistics']
            logger.info("✅ Query succeeded")
            logger.info(f"   Rows: {len(df)}")
            logger.info(f"   Data Scanned: {stats.get('DataScannedInBytes', 0) / 1024 / 1024:.2f} MB")
            logger.info(f"   Execution Time: {stats.get('EngineExecutionTimeInMillis', 0) / 1000:.2f} seconds")

            return df

        except ClientError as e:
            logger.error(f"❌ Athena query failed: {e}")
            raise


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Lambda Architecture - Batch Layer')

    parser.add_argument(
        '--mode',
        choices=['setup', 'generate-data', 'batch-process', 'query'],
        default='batch-process',
        help='Execution mode'
    )

    parser.add_argument(
        '--env',
        choices=['localstack', 'aws'],
        default='localstack',
        help='Environment (LocalStack or real AWS)'
    )

    parser.add_argument(
        '--batch-date',
        type=str,
        help='Batch date (YYYY-MM-DD), defaults to today'
    )

    parser.add_argument(
        '--records',
        type=int,
        default=10000,
        help='Number of records to generate (for generate-data mode)'
    )

    parser.add_argument(
        '--query',
        type=str,
        help='SQL query for query mode'
    )

    args = parser.parse_args()

    # Initialize processor
    processor = BatchLayerProcessor(use_localstack=(args.env == 'localstack'))

    if args.mode == 'setup':
        logger.info("🚀 Setting up infrastructure...")
        resources = processor.setup_infrastructure()
        processor.create_glue_tables()
        logger.info("✅ Infrastructure ready")
        print(json.dumps(resources, indent=2))

    elif args.mode == 'generate-data':
        logger.info(f"📊 Generating {args.records:,} sample records...")
        processor.generate_sample_data(num_records=args.records)
        logger.info("✅ Sample data generated")

    elif args.mode == 'batch-process':
        logger.info("⚙️  Running batch job...")
        stats = processor.run_batch_job(batch_date=args.batch_date)
        print(json.dumps(stats, indent=2, default=str))

    elif args.mode == 'query':
        if not args.query:
            args.query = """
                SELECT
                    segment,
                    COUNT(*) as users,
                    SUM(lifetime_revenue) as total_revenue,
                    AVG(lifetime_orders) as avg_orders
                FROM user_metrics
                WHERE batch_date = (SELECT MAX(batch_date) FROM user_metrics)
                GROUP BY segment
                ORDER BY total_revenue DESC
            """

        logger.info("🔍 Executing Athena query...")
        result = processor.query_athena(args.query)
        print(result.to_string())

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
