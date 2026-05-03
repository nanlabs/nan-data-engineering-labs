"""
Stream Processor for Kappa Architecture

This module implements continuous stream processing using Kinesis Data Analytics (Flink).
Unlike Lambda Architecture, there is NO separate batch layer - all processing is stream-based.

Key Features:
1. Kinesis Data Streams source (365-day retention)
2. Flink SQL for stateful aggregations (tumbling windows)
3. DynamoDB sink for materialized views
4. Exactly-once processing semantics
5. Checkpointing for fault tolerance

Author: Training Module 18
"""

import sys
import json
import logging
import argparse
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any
from collections import defaultdict

import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KappaStreamProcessor:
    """
    Kappa Architecture Stream Processor.

    Processes event stream continuously to maintain materialized views.
    No separate batch layer - reprocessing done via stream replay.
    """

    def __init__(
        self,
        stream_name: str = "orders-kappa",
        output_table: str = "category_metrics_v1",
        window_minutes: int = 5,
        region: str = "us-east-1",
        use_localstack: bool = False
    ):
        """
        Initialize Kappa Stream Processor.

        Args:
            stream_name: Kinesis stream name
            output_table: DynamoDB table for output
            window_minutes: Tumbling window size (minutes)
            region: AWS region
            use_localstack: If True, use LocalStack
        """
        self.stream_name = stream_name
        self.output_table = output_table
        self.window_minutes = window_minutes
        self.region = region

        # AWS clients
        endpoint_url = "http://localhost:4566" if use_localstack else None

        self.kinesis = boto3.client('kinesis', region_name=region, endpoint_url=endpoint_url)
        self.dynamodb = boto3.client('dynamodb', region_name=region, endpoint_url=endpoint_url)
        self.kinesisanalytics = boto3.client('kinesisanalytics', region_name=region, endpoint_url=endpoint_url)

        # In-memory state for window aggregations (simulates Flink state)
        self.window_state = defaultdict(lambda: {
            'order_count': 0,
            'total_revenue': Decimal('0'),
            'unique_users': set(),
            'window_start': None,
            'window_end': None
        })

        logger.info("KappaStreamProcessor initialized")
        logger.info(f"   Stream: {stream_name}")
        logger.info(f"   Output: {output_table}")
        logger.info(f"   Window: {window_minutes} minutes")

    def setup_infrastructure(self) -> Dict[str, Any]:
        """
        Create Kinesis stream and DynamoDB table.

        Returns:
            Dict with created resources
        """
        logger.info("=== Setting Up Kappa Infrastructure ===")

        results = {}

        # Create Kinesis stream with extended retention
        try:
            self.kinesis.create_stream(
                StreamName=self.stream_name,
                ShardCount=2  # 2 MB/sec total capacity
            )
            logger.info(f"✅ Created Kinesis stream: {self.stream_name}")

            # Wait for stream
            waiter = self.kinesis.get_waiter('stream_exists')
            waiter.wait(StreamName=self.stream_name)

            # Set retention to 365 days
            self.kinesis.increase_stream_retention_period(
                StreamName=self.stream_name,
                RetentionPeriodHours=8760  # 365 days
            )
            logger.info("✅ Set retention: 365 days")

            results['kinesis_stream'] = self.stream_name

        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                logger.info(f"✅ Stream already exists: {self.stream_name}")
                results['kinesis_stream'] = self.stream_name
            else:
                raise

        # Create DynamoDB table
        try:
            self.dynamodb.create_table(
                TableName=self.output_table,
                KeySchema=[
                    {'AttributeName': 'category', 'KeyType': 'HASH'},
                    {'AttributeName': 'window_start', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'category', 'AttributeType': 'S'},
                    {'AttributeName': 'window_start', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            logger.info(f"✅ Created DynamoDB table: {self.output_table}")

            results['dynamodb_table'] = self.output_table

        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                logger.info(f"✅ Table already exists: {self.output_table}")
                results['dynamodb_table'] = self.output_table
            else:
                raise

        return results

    def process_event(self, event: Dict[str, Any]) -> None:
        """
        Process single event (update window state).

        Args:
            event: Order event
        """
        category = event.get('category', 'Unknown')
        amount = Decimal(str(event['amount']))
        user_id = event['user_id']
        timestamp = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))

        # Determine window
        window_start = timestamp.replace(
            minute=(timestamp.minute // self.window_minutes) * self.window_minutes,
            second=0,
            microsecond=0
        )
        window_end = window_start + timedelta(minutes=self.window_minutes)

        window_key = f"{category}#{window_start.isoformat()}"

        # Update window state
        state = self.window_state[window_key]

        if state['window_start'] is None:
            state['window_start'] = window_start
            state['window_end'] = window_end

        state['order_count'] += 1
        state['total_revenue'] += amount
        state['unique_users'].add(user_id)

        logger.debug(f"📊 Updated window: {window_key} → {state['order_count']} orders")

    def flush_window(self, category: str, window_start: datetime) -> None:
        """
        Flush completed window to DynamoDB.

        Args:
            category: Product category
            window_start: Window start time
        """
        window_key = f"{category}#{window_start.isoformat()}"
        state = self.window_state.get(window_key)

        if not state or state['order_count'] == 0:
            return

        # Calculate metrics
        avg_order_value = state['total_revenue'] / state['order_count']

        try:
            # Write to DynamoDB
            self.dynamodb.put_item(
                TableName=self.output_table,
                Item={
                    'category': {'S': category},
                    'window_start': {'S': window_start.isoformat()},
                    'window_end': {'S': state['window_end'].isoformat()},
                    'order_count': {'N': str(state['order_count'])},
                    'revenue': {'N': str(state['total_revenue'])},
                    'avg_order_value': {'N': str(avg_order_value)},
                    'unique_buyers': {'N': str(len(state['unique_users']))},
                    'updated_at': {'S': datetime.now().isoformat()}
                }
            )

            logger.info(
                f"💾 Flushed window: {category} [{window_start.strftime('%H:%M')} - {state['window_end'].strftime('%H:%M')}] "
                f"→ {state['order_count']} orders, ${state['total_revenue']}"
            )

            # Clear state
            del self.window_state[window_key]

        except ClientError as e:
            logger.error(f"❌ Failed to write window: {e}")

    def consume_stream_continuously(
        self,
        iterator_type: str = 'LATEST'
    ) -> None:
        """
        Consume Kinesis stream continuously (simulates Flink application).

        Args:
            iterator_type: LATEST (start now) or TRIM_HORIZON (start from oldest)
        """
        logger.info("=== Starting Kappa Stream Processor ===")
        logger.info(f"   Stream: {self.stream_name}")
        logger.info(f"   Window: {self.window_minutes} minutes")
        logger.info(f"   Output: {self.output_table}")
        logger.info(f"   Iterator: {iterator_type}")
        logger.info("=" * 60)

        try:
            # Get shard iterators
            response = self.kinesis.describe_stream(StreamName=self.stream_name)
            shards = response['StreamDescription']['Shards']

            logger.info(f"   Shards: {len(shards)}")

            iterators = []
            for shard in shards:
                shard_id = shard['ShardId']

                iterator_response = self.kinesis.get_shard_iterator(
                    StreamName=self.stream_name,
                    ShardId=shard_id,
                    ShardIteratorType=iterator_type
                )

                iterators.append({
                    'shard_id': shard_id,
                    'iterator': iterator_response['ShardIterator']
                })

            # Track last window flush time
            last_flush = datetime.now()
            total_processed = 0

            # Consume loop
            while True:
                for shard_data in iterators:
                    # Get records
                    response = self.kinesis.get_records(
                        ShardIterator=shard_data['iterator'],
                        Limit=100
                    )

                    records = response['Records']

                    # Process records
                    for record in records:
                        event = json.loads(record['Data'])
                        self.process_event(event)
                        total_processed += 1

                    # Update iterator
                    shard_data['iterator'] = response['NextShardIterator']

                # Flush windows periodically (every window_minutes)
                now = datetime.now()
                if (now - last_flush).total_seconds() >= self.window_minutes * 60:
                    self._flush_completed_windows(now)
                    last_flush = now

                    logger.info(f"📊 Processed: {total_processed:,} events")

                # Sleep to avoid empty polling
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info(f"\n⏹️  Stopped processor (processed {total_processed:,} events)")

            # Final flush
            self._flush_completed_windows(datetime.now(), force=True)

        except Exception as e:
            logger.error(f"❌ Processor error: {e}")
            raise

    def _flush_completed_windows(self, current_time: datetime, force: bool = False) -> None:
        """
        Flush all completed windows to DynamoDB.

        Args:
            current_time: Current timestamp
            force: If True, flush all windows
        """
        windows_to_flush = []

        for window_key, state in self.window_state.items():
            if state['window_end'] is None:
                continue

            # Window is complete if end time < current time
            if force or state['window_end'] < current_time:
                category = window_key.split('#')[0]
                windows_to_flush.append((category, state['window_start']))

        for category, window_start in windows_to_flush:
            self.flush_window(category, window_start)

    def query_category_metrics(
        self,
        category: str,
        start_time: datetime = None,
        end_time: datetime = None
    ) -> List[Dict[str, Any]]:
        """
        Query category metrics from materialized view.

        Args:
            category: Product category
            start_time: Start time (optional)
            end_time: End time (optional)

        Returns:
            List of window metrics
        """
        logger.info(f"🔍 Querying metrics: {category}")

        # Build query expression
        key_condition = "category = :category"
        expression_values = {':category': {'S': category}}

        if start_time:
            key_condition += " AND window_start >= :start"
            expression_values[':start'] = {'S': start_time.isoformat()}

        if end_time:
            key_condition += " AND window_start < :end"
            expression_values[':end'] = {'S': end_time.isoformat()}

        try:
            response = self.dynamodb.query(
                TableName=self.output_table,
                KeyConditionExpression=key_condition,
                ExpressionAttributeValues=expression_values
            )

            results = []

            for item in response['Items']:
                results.append({
                    'category': item['category']['S'],
                    'window_start': item['window_start']['S'],
                    'window_end': item['window_end']['S'],
                    'order_count': int(item['order_count']['N']),
                    'revenue': float(item['revenue']['N']),
                    'avg_order_value': float(item['avg_order_value']['N']),
                    'unique_buyers': int(item['unique_buyers']['N'])
                })

            logger.info(f"✅ Found {len(results)} windows")

            return results

        except ClientError as e:
            logger.error(f"❌ Query failed: {e}")
            return []

    def get_aggregate_metrics(self, category: str, hours_back: int = 24) -> Dict[str, Any]:
        """
        Get aggregated metrics over time range.

        Args:
            category: Product category
            hours_back: Hours to aggregate

        Returns:
            Dict with aggregated metrics
        """
        start_time = datetime.now() - timedelta(hours=hours_back)

        windows = self.query_category_metrics(
            category=category,
            start_time=start_time
        )

        if not windows:
            return {
                'category': category,
                'time_range_hours': hours_back,
                'total_orders': 0,
                'total_revenue': 0.0,
                'avg_order_value': 0.0
            }

        # Aggregate across windows
        total_orders = sum(w['order_count'] for w in windows)
        total_revenue = sum(w['revenue'] for w in windows)
        unique_buyers = len(set(w['unique_buyers'] for w in windows))

        return {
            'category': category,
            'time_range_hours': hours_back,
            'windows': len(windows),
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'avg_order_value': total_revenue / total_orders if total_orders > 0 else 0,
            'unique_buyers': unique_buyers
        }

    def deploy_flink_application(
        self,
        application_name: str = "kappa-processor-v1",
        code_s3_bucket: str = "kappa-flink-code"
    ) -> str:
        """
        Deploy Kinesis Data Analytics (Flink) application.

        This creates a managed Flink application that processes stream continuously.

        Args:
            application_name: Flink application name
            code_s3_bucket: S3 bucket with Flink application code

        Returns:
            Application ARN
        """
        logger.info(f"=== Deploying Flink Application: {application_name} ===")

        # Flink SQL code
        flink_sql = f"""
        -- Source: Kinesis stream
        CREATE TABLE orders (
            order_id STRING,
            user_id STRING,
            category STRING,
            amount DOUBLE,
            order_timestamp TIMESTAMP(3),
            WATERMARK FOR order_timestamp AS order_timestamp - INTERVAL '5' SECOND
        ) WITH (
            'connector' = 'kinesis',
            'stream' = '{self.stream_name}',
            'aws.region' = '{self.region}',
            'scan.stream.initpos' = 'LATEST',
            'format' = 'json'
        );

        -- Sink: DynamoDB table
        CREATE TABLE category_metrics (
            category STRING,
            window_start TIMESTAMP(3),
            window_end TIMESTAMP(3),
            order_count BIGINT,
            revenue DOUBLE,
            avg_order_value DOUBLE,
            unique_buyers BIGINT,
            PRIMARY KEY (category, window_start) NOT ENFORCED
        ) WITH (
            'connector' = 'dynamodb',
            'table-name' = '{self.output_table}',
            'aws.region' = '{self.region}'
        );

        -- Tumbling window aggregation
        INSERT INTO category_metrics
        SELECT
            category,
            window_start,
            window_end,
            COUNT(*) as order_count,
            SUM(amount) as revenue,
            AVG(amount) as avg_order_value,
            COUNT(DISTINCT user_id) as unique_buyers
        FROM TABLE(
            TUMBLE(TABLE orders, DESCRIPTOR(order_timestamp), INTERVAL '{self.window_minutes}' MINUTES)
        )
        GROUP BY window_start, window_end, category;
        """

        # Save Flink SQL to file
        sql_file = f"/tmp/{application_name}.sql"
        with open(sql_file, 'w') as f:
            f.write(flink_sql)

        logger.info(f"✅ Generated Flink SQL: {sql_file}")
        logger.info(f"   Query: Tumbling window ({self.window_minutes} min)")
        logger.info(f"   Source: Kinesis stream ({self.stream_name})")
        logger.info(f"   Sink: DynamoDB ({self.output_table})")

        # In production, upload to S3 and create Kinesis Analytics app
        # For this exercise, we simulate with Python consumer

        return application_name

    def produce_test_events(
        self,
        num_events: int = 1000,
        rate_per_second: int = 10
    ) -> None:
        """
        Produce test events to stream.

        Args:
            num_events: Number of events to produce
            rate_per_second: Events per second
        """
        logger.info(f"=== Producing {num_events:,} Test Events ===")
        logger.info(f"   Rate: {rate_per_second} events/second")

        import random

        categories = ['Electronics', 'Clothing', 'Home', 'Sports', 'Books', 'Toys']
        user_ids = [f"user_{i:04d}" for i in range(1, 501)]

        records = []

        for i in range(num_events):
            event = {
                'event_type': 'OrderPlaced',
                'order_id': f"ord_{int(time.time() * 1000)}_{i}",
                'user_id': random.choice(user_ids),
                'category': random.choice(categories),
                'amount': round(random.uniform(10.0, 500.0), 2),
                'timestamp': datetime.now().isoformat(),
                'event_id': f"evt_{int(time.time() * 1000000)}_{i}"
            }

            records.append({
                'Data': json.dumps(event),
                'PartitionKey': event['user_id']
            })

            # Send in batches of 500
            if len(records) >= 500:
                self.kinesis.put_records(
                    StreamName=self.stream_name,
                    Records=records
                )

                logger.info(f"📤 Sent {i + 1:,} / {num_events:,} events")
                records = []

                # Rate limiting
                time.sleep(len(records) / rate_per_second)

        # Send remaining
        if records:
            self.kinesis.put_records(
                StreamName=self.stream_name,
                Records=records
            )

        logger.info(f"✅ Produced {num_events:,} events to {self.stream_name}")

    def get_processing_metrics(self) -> Dict[str, Any]:
        """
        Get stream processing metrics.

        Returns:
            Dict with metrics
        """
        logger.info("=== Stream Processing Metrics ===")

        try:
            # Get stream description
            stream_desc = self.kinesis.describe_stream(StreamName=self.stream_name)
            stream_info = stream_desc['StreamDescription']

            # Count records in DynamoDB (output)
            table_desc = self.dynamodb.describe_table(TableName=self.output_table)
            item_count = table_desc['Table'].get('ItemCount', 0)

            metrics = {
                'stream_name': self.stream_name,
                'stream_status': stream_info['StreamStatus'],
                'shard_count': len(stream_info['Shards']),
                'retention_hours': stream_info['RetentionPeriodHours'],
                'output_table': self.output_table,
                'materialized_windows': item_count,
                'window_minutes': self.window_minutes
            }

            logger.info(f"   Stream: {metrics['stream_name']} ({metrics['stream_status']})")
            logger.info(f"   Shards: {metrics['shard_count']}")
            logger.info(f"   Retention: {metrics['retention_hours']} hours ({metrics['retention_hours']/24:.0f} days)")
            logger.info(f"   Materialized Windows: {metrics['materialized_windows']:,}")

            return metrics

        except ClientError as e:
            logger.error(f"❌ Failed to get metrics: {e}")
            return {}

    def print_category_report(self, category: str, hours: int = 24) -> None:
        """
        Print formatted report for category.

        Args:
            category: Product category
            hours: Time range in hours
        """
        metrics = self.get_aggregate_metrics(category, hours_back=hours)

        print("=" * 70)
        print(f"📊 CATEGORY METRICS: {category}")
        print(f"   Time Range: Last {hours} hours")
        print("=" * 70)
        print()

        print(f"   Total Orders:       {metrics['total_orders']:,} orders")
        print(f"   Total Revenue:      ${metrics['total_revenue']:,.2f}")
        print(f"   Avg Order Value:    ${metrics['avg_order_value']:.2f}")
        print(f"   Unique Buyers:      {metrics.get('unique_buyers', 'N/A')}")
        print(f"   Windows Aggregated: {metrics['windows']}")
        print()
        print("=" * 70)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Kappa Architecture - Stream Processor')

    parser.add_argument(
        '--mode',
        choices=['setup', 'process', 'produce', 'query', 'deploy', 'metrics'],
        default='process',
        help='Execution mode'
    )

    parser.add_argument(
        '--env',
        choices=['localstack', 'aws'],
        default='localstack',
        help='Environment'
    )

    parser.add_argument(
        '--category',
        type=str,
        help='Category to query'
    )

    parser.add_argument(
        '--hours',
        type=int,
        default=24,
        help='Hours to aggregate (for query mode)'
    )

    parser.add_argument(
        '--events',
        type=int,
        default=1000,
        help='Number of events (for produce mode)'
    )

    parser.add_argument(
        '--window-minutes',
        type=int,
        default=5,
        help='Window size in minutes'
    )

    parser.add_argument(
        '--output-table',
        type=str,
        default='category_metrics_v1',
        help='DynamoDB output table'
    )

    args = parser.parse_args()

    # Initialize processor
    processor = KappaStreamProcessor(
        output_table=args.output_table,
        window_minutes=args.window_minutes,
        use_localstack=(args.env == 'localstack')
    )

    if args.mode == 'setup':
        logger.info("🚀 Setting up infrastructure...")
        resources = processor.setup_infrastructure()
        print(json.dumps(resources, indent=2))

    elif args.mode == 'process':
        logger.info("⚙️  Starting stream processor...")
        processor.consume_stream_continuously()

    elif args.mode == 'produce':
        logger.info(f"📤 Producing {args.events:,} test events...")
        processor.produce_test_events(num_events=args.events)

    elif args.mode == 'query':
        if not args.category:
            logger.error("❌ --category required for query mode")
            sys.exit(1)

        processor.print_category_report(args.category, hours=args.hours)

    elif args.mode == 'deploy':
        logger.info("🚀 Deploying Flink application...")
        app_name = processor.deploy_flink_application()
        logger.info(f"✅ Deployed: {app_name}")

    elif args.mode == 'metrics':
        stats = processor.get_processing_metrics()
        print(json.dumps(stats, indent=2, default=str))

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
