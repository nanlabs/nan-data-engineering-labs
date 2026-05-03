"""
Speed Layer Implementation for Lambda Architecture

This module implements the real-time processing component of Lambda Architecture.
It processes recent events (last 24 hours) using Kinesis + Lambda for sub-second latency.

Key Responsibilities:
1. Receive order events from Kinesis stream
2. Update real-time metrics in DynamoDB (atomic increments)
3. Maintain sliding window of last 24 hours
4. Handle idempotency (deduplicate events)
5. Reset metrics daily (midnight)

Author: Training Module 18
"""

import sys
import json
import logging
import argparse
import time
import base64
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any

import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SpeedLayerProcessor:
    """
    Speed Layer Processor for Lambda Architecture.

    Processes real-time events for immediate insights with <1 second latency.
    Complements batch layer by providing fresh metrics for current day.
    """

    def __init__(
        self,
        stream_name: str = "orders-stream",
        table_name: str = "realtime-user-metrics",
        region: str = "us-east-1",
        use_localstack: bool = False
    ):
        """
        Initialize Speed Layer Processor.

        Args:
            stream_name: Kinesis stream name
            table_name: DynamoDB table for real-time metrics
            region: AWS region
            use_localstack: If True, use LocalStack endpoints
        """
        self.stream_name = stream_name
        self.table_name = table_name
        self.region = region

        # AWS clients
        endpoint_url = "http://localhost:4566" if use_localstack else None

        self.kinesis = boto3.client('kinesis', region_name=region, endpoint_url=endpoint_url)
        self.dynamodb = boto3.client('dynamodb', region_name=region, endpoint_url=endpoint_url)

        # For deduplication (in-memory cache)
        self.processed_event_ids = set()

        logger.info(f"SpeedLayerProcessor initialized (LocalStack: {use_localstack})")

    def setup_infrastructure(self) -> Dict[str, Any]:
        """
        Create Kinesis stream and DynamoDB table.

        Returns:
            Dict with created resource ARNs
        """
        logger.info("=== Setting Up Speed Layer Infrastructure ===")

        results = {}

        # Create Kinesis stream
        try:
            self.kinesis.create_stream(
                StreamName=self.stream_name,
                ShardCount=1  # 1 MB/sec capacity
            )
            logger.info(f"✅ Created Kinesis stream: {self.stream_name}")

            # Wait for stream to become active
            logger.info("   Waiting for stream to be active...")
            waiter = self.kinesis.get_waiter('stream_exists')
            waiter.wait(StreamName=self.stream_name)

            results['kinesis_stream'] = self.stream_name

        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                logger.info(f"✅ Kinesis stream already exists: {self.stream_name}")
                results['kinesis_stream'] = self.stream_name
            else:
                logger.error(f"❌ Failed to create stream: {e}")
                raise

        # Create DynamoDB table
        try:
            self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'user_id', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'  # Auto-scaling
            )
            logger.info(f"✅ Created DynamoDB table: {self.table_name}")

            # Wait for table to be active
            logger.info("   Waiting for table to be active...")
            waiter = self.dynamodb.get_waiter('table_exists')
            waiter.wait(TableName=self.table_name)

            results['dynamodb_table'] = self.table_name

        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                logger.info(f"✅ DynamoDB table already exists: {self.table_name}")
                results['dynamodb_table'] = self.table_name
            else:
                logger.error(f"❌ Failed to create table: {e}")
                raise

        return results

    def send_order_event(
        self,
        order_id: str,
        user_id: str,
        amount: float,
        product_id: str = None,
        timestamp: str = None
    ) -> Dict[str, Any]:
        """
        Send order event to Kinesis stream.

        Args:
            order_id: Unique order ID
            user_id: User ID
            amount: Order amount (USD)
            product_id: Product ID (optional)
            timestamp: ISO timestamp or None for now

        Returns:
            Kinesis response
        """
        if not timestamp:
            timestamp = datetime.now().isoformat()

        event = {
            'event_type': 'OrderPlaced',
            'order_id': order_id,
            'user_id': user_id,
            'amount': amount,
            'product_id': product_id,
            'timestamp': timestamp,
            'event_id': f"{order_id}_{timestamp}"  # For deduplication
        }

        try:
            response = self.kinesis.put_record(
                StreamName=self.stream_name,
                Data=json.dumps(event),
                PartitionKey=user_id  # Same user → same shard (ordering preserved)
            )

            logger.debug(f"📤 Sent event: {order_id} → Shard {response['ShardId']}")

            return response

        except ClientError as e:
            logger.error(f"❌ Failed to send event: {e}")
            raise

    def send_batch_events(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Send multiple events efficiently using put_records (batch API).

        Args:
            events: List of event dicts

        Returns:
            Dict with success/failure counts
        """
        records = []

        for event in events:
            records.append({
                'Data': json.dumps(event),
                'PartitionKey': event['user_id']
            })

        # Kinesis supports up to 500 records per call
        batch_size = 500
        total_success = 0
        total_failed = 0

        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]

            try:
                response = self.kinesis.put_records(
                    StreamName=self.stream_name,
                    Records=batch
                )

                total_success += (len(batch) - response['FailedRecordCount'])
                total_failed += response['FailedRecordCount']

            except ClientError as e:
                logger.error(f"❌ Batch send failed: {e}")
                total_failed += len(batch)

        logger.info(f"📤 Sent {total_success:,} events (failed: {total_failed})")

        return {'success': total_success, 'failed': total_failed}

    def process_order_event(self, event: Dict[str, Any]) -> None:
        """
        Process single order event (update DynamoDB).

        Args:
            event: Order event dict
        """
        event_id = event.get('event_id')

        # Idempotency: Skip if already processed
        if event_id in self.processed_event_ids:
            logger.debug(f"⏭️  Skipping duplicate event: {event_id}")
            return

        user_id = event['user_id']
        amount = Decimal(str(event['amount']))
        timestamp = event['timestamp']

        try:
            # Atomic increment in DynamoDB
            self.dynamodb.update_item(
                TableName=self.table_name,
                Key={'user_id': {'S': user_id}},
                UpdateExpression='''
                    SET orders_today = if_not_exists(orders_today, :zero) + :one,
                        revenue_today = if_not_exists(revenue_today, :zero) + :amount,
                        last_order_time = :timestamp,
                        updated_at = :now
                ''',
                ExpressionAttributeValues={
                    ':zero': {'N': '0'},
                    ':one': {'N': '1'},
                    ':amount': {'N': str(amount)},
                    ':timestamp': {'S': timestamp},
                    ':now': {'S': datetime.now().isoformat()}
                }
            )

            # Mark as processed
            self.processed_event_ids.add(event_id)

            logger.debug(f"✅ Processed: {user_id} → +${amount}")

        except ClientError as e:
            logger.error(f"❌ Failed to update DynamoDB: {e}")
            raise

    def lambda_handler(self, event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
        """
        AWS Lambda handler (invoked by Kinesis trigger).

        Args:
            event: Lambda event with Kinesis records
            context: Lambda context (unused)

        Returns:
            Dict with processing statistics
        """
        logger.info("=== Lambda Handler Invoked ===")
        logger.info(f"   Records: {len(event.get('Records', []))}")

        start_time = time.time()
        processed = 0
        errors = 0

        for record in event.get('Records', []):
            try:
                # Decode Kinesis record
                payload = base64.b64decode(record['kinesis']['data'])
                order_event = json.loads(payload)

                # Process event
                self.process_order_event(order_event)
                processed += 1

            except Exception as e:
                logger.error(f"❌ Failed to process record: {e}")
                errors += 1

        duration_ms = (time.time() - start_time) * 1000

        logger.info(f"✅ Processed {processed} events (errors: {errors}) in {duration_ms:.0f}ms")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'processed': processed,
                'errors': errors,
                'duration_ms': duration_ms
            })
        }

    def consume_stream_continuously(self, batch_size: int = 100) -> None:
        """
        Consume Kinesis stream continuously (simulates Lambda trigger).

        Args:
            batch_size: Number of records to fetch per batch
        """
        logger.info("=== Starting Continuous Stream Consumer ===")
        logger.info(f"   Stream: {self.stream_name}")
        logger.info(f"   Batch Size: {batch_size}")
        logger.info("   Press Ctrl+C to stop")
        logger.info("=" * 60)

        try:
            # Get shard iterator
            response = self.kinesis.describe_stream(StreamName=self.stream_name)
            shard_id = response['StreamDescription']['Shards'][0]['ShardId']

            iterator_response = self.kinesis.get_shard_iterator(
                StreamName=self.stream_name,
                ShardId=shard_id,
                ShardIteratorType='LATEST'  # Start from now
            )

            shard_iterator = iterator_response['ShardIterator']

            # Consume loop
            total_processed = 0

            while True:
                # Get records
                response = self.kinesis.get_records(
                    ShardIterator=shard_iterator,
                    Limit=batch_size
                )

                records = response['Records']

                if records:
                    # Simulate Lambda invocation
                    lambda_event = {'Records': []}

                    for record in records:
                        lambda_event['Records'].append({
                            'kinesis': {
                                'data': base64.b64encode(record['Data']).decode('utf-8'),
                                'sequenceNumber': record['SequenceNumber']
                            }
                        })

                    # Process batch
                    result = self.lambda_handler(lambda_event)
                    total_processed += json.loads(result['body'])['processed']

                    logger.info(f"📊 Total Processed: {total_processed:,} events")

                # Update iterator
                shard_iterator = response['NextShardIterator']

                # Sleep to avoid empty polling
                if not records:
                    time.sleep(1)

        except KeyboardInterrupt:
            logger.info(f"\n⏹️  Stopped consumer (processed {total_processed:,} events)")

        except Exception as e:
            logger.error(f"❌ Consumer error: {e}")
            raise

    def produce_events_continuously(
        self,
        rate_per_second: int = 10,
        duration_seconds: int = None
    ) -> Dict[str, int]:
        """
        Generate and send events continuously.

        Args:
            rate_per_second: Events to send per second
            duration_seconds: Run duration or None for infinite

        Returns:
            Dict with statistics
        """
        logger.info("=== Starting Continuous Event Producer ===")
        logger.info(f"   Rate: {rate_per_second} events/second")
        logger.info(f"   Duration: {duration_seconds or 'infinite'} seconds")
        logger.info("   Press Ctrl+C to stop")
        logger.info("=" * 60)

        import random

        user_ids = [f"user_{i:04d}" for i in range(1, 101)]
        product_ids = [f"prod_{i:03d}" for i in range(1, 51)]

        total_sent = 0
        start_time = time.time()

        try:
            while True:
                # Check duration
                if duration_seconds and (time.time() - start_time) > duration_seconds:
                    break

                # Send batch of events
                events = []

                for _ in range(rate_per_second):
                    event = {
                        'event_type': 'OrderPlaced',
                        'order_id': f"ord_{int(time.time() * 1000)}_{random.randint(1000, 9999)}",
                        'user_id': random.choice(user_ids),
                        'product_id': random.choice(product_ids),
                        'amount': round(random.uniform(10.0, 200.0), 2),
                        'quantity': random.randint(1, 5),
                        'timestamp': datetime.now().isoformat(),
                        'event_id': f"evt_{int(time.time() * 1000000)}"
                    }
                    events.append(event)

                # Send to Kinesis
                result = self.send_batch_events(events)
                total_sent += result['success']

                logger.info(f"📤 Sent {total_sent:,} events (rate: {rate_per_second}/sec)")

                # Sleep to maintain rate
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("\n⏹️  Stopped producer")

        duration = time.time() - start_time

        stats = {
            'total_sent': total_sent,
            'duration_seconds': duration,
            'avg_rate': total_sent / duration if duration > 0 else 0
        }

        logger.info(f"✅ Producer finished: {total_sent:,} events in {duration:.1f}s")

        return stats

    def query_realtime_metrics(self, user_id: str) -> Dict[str, Any]:
        """
        Query real-time metrics for a user from DynamoDB.

        Args:
            user_id: User ID

        Returns:
            Dict with real-time metrics
        """
        try:
            response = self.dynamodb.get_item(
                TableName=self.table_name,
                Key={'user_id': {'S': user_id}}
            )

            if 'Item' not in response:
                return {
                    'user_id': user_id,
                    'orders_today': 0,
                    'revenue_today': 0.0,
                    'last_order_time': None
                }

            item = response['Item']

            return {
                'user_id': user_id,
                'orders_today': int(item.get('orders_today', {}).get('N', 0)),
                'revenue_today': float(item.get('revenue_today', {}).get('N', 0)),
                'last_order_time': item.get('last_order_time', {}).get('S'),
                'updated_at': item.get('updated_at', {}).get('S')
            }

        except ClientError as e:
            logger.error(f"❌ Query failed: {e}")
            raise

    def reset_daily_metrics(self) -> Dict[str, int]:
        """
        Reset real-time metrics (called at midnight).

        Archives current day's data to S3, then resets DynamoDB counters to 0.

        Returns:
            Dict with statistics
        """
        logger.info("=== Resetting Daily Metrics ===")
        logger.info(f"   Time: {datetime.now().isoformat()}")

        # Scan all users
        try:
            response = self.dynamodb.scan(TableName=self.table_name)
            items = response['Items']

            logger.info(f"   Found {len(items)} users with metrics")

            # Archive to S3 (before reset)
            archive_data = []

            for item in items:
                archive_data.append({
                    'user_id': item['user_id']['S'],
                    'orders_today': int(item.get('orders_today', {}).get('N', 0)),
                    'revenue_today': float(item.get('revenue_today', {}).get('N', 0)),
                    'date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                })

            # Write to S3
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            s3_client = boto3.client('s3')

            s3_client.put_object(
                Bucket='lambda-arch-realtime-archive',
                Key=f"daily_snapshots/{yesterday}.json",
                Body=json.dumps(archive_data, indent=2)
            )

            logger.info(f"✅ Archived to s3://lambda-arch-realtime-archive/daily_snapshots/{yesterday}.json")

            # Reset counters
            reset_count = 0

            for item in items:
                user_id = item['user_id']['S']

                self.dynamodb.update_item(
                    TableName=self.table_name,
                    Key={'user_id': {'S': user_id}},
                    UpdateExpression='''
                        SET orders_today = :zero,
                            revenue_today = :zero,
                            reset_at = :now
                    ''',
                    ExpressionAttributeValues={
                        ':zero': {'N': '0'},
                        ':now': {'S': datetime.now().isoformat()}
                    }
                )

                reset_count += 1

            logger.info(f"✅ Reset {reset_count} user metrics")

            return {
                'archived_users': len(archive_data),
                'reset_users': reset_count,
                'archive_location': f"s3://lambda-arch-realtime-archive/daily_snapshots/{yesterday}.json"
            }

        except ClientError as e:
            logger.error(f"❌ Reset failed: {e}")
            raise

    def measure_latency(self, samples: int = 100) -> Dict[str, float]:
        """
        Measure end-to-end latency (send → visible in DynamoDB).

        Args:
            samples: Number of test events to send

        Returns:
            Dict with latency statistics (p50, p95, p99)
        """
        logger.info(f"=== Measuring Latency ({samples} samples) ===")

        latencies = []

        for i in range(samples):
            # Generate test event
            user_id = f"test_user_{i}"
            order_id = f"test_order_{int(time.time() * 1000)}_{i}"

            # Send event
            send_time = time.time()

            self.send_order_event(
                order_id=order_id,
                user_id=user_id,
                amount=99.99
            )

            # Poll DynamoDB until visible
            while True:
                metrics = self.query_realtime_metrics(user_id)

                if metrics['orders_today'] > 0:
                    receive_time = time.time()
                    latency = (receive_time - send_time) * 1000  # ms
                    latencies.append(latency)
                    break

                time.sleep(0.1)  # 100ms poll interval

            if (i + 1) % 10 == 0:
                logger.info(f"   Progress: {i + 1}/{samples} samples")

        # Calculate statistics
        import numpy as np

        latencies_array = np.array(latencies)

        stats = {
            'samples': samples,
            'p50_ms': float(np.percentile(latencies_array, 50)),
            'p95_ms': float(np.percentile(latencies_array, 95)),
            'p99_ms': float(np.percentile(latencies_array, 99)),
            'mean_ms': float(np.mean(latencies_array)),
            'max_ms': float(np.max(latencies_array))
        }

        logger.info("=" * 60)
        logger.info("=== Latency Results ===")
        logger.info(f"   Samples: {stats['samples']}")
        logger.info(f"   P50: {stats['p50_ms']:.0f}ms")
        logger.info(f"   P95: {stats['p95_ms']:.0f}ms")
        logger.info(f"   P99: {stats['p99_ms']:.0f}ms")
        logger.info(f"   Mean: {stats['mean_ms']:.0f}ms")
        logger.info(f"   Max: {stats['max_ms']:.0f}ms")
        logger.info("=" * 60)

        return stats

    def get_stream_metrics(self) -> Dict[str, Any]:
        """
        Get Kinesis stream metrics.

        Returns:
            Dict with stream statistics
        """
        try:
            response = self.kinesis.describe_stream(StreamName=self.stream_name)
            stream_desc = response['StreamDescription']

            # Get CloudWatch metrics
            cloudwatch = boto3.client('cloudwatch', region_name=self.region)

            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)

            # Get IncomingRecords metric
            metrics = cloudwatch.get_metric_statistics(
                Namespace='AWS/Kinesis',
                MetricName='IncomingRecords',
                Dimensions=[{'Name': 'StreamName', 'Value': self.stream_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,  # 5 minutes
                Statistics=['Sum', 'Average']
            )

            total_records = sum([point['Sum'] for point in metrics['Datapoints']])

            stats = {
                'stream_name': self.stream_name,
                'status': stream_desc['StreamStatus'],
                'shards': len(stream_desc['Shards']),
                'retention_hours': stream_desc['RetentionPeriodHours'],
                'records_last_hour': int(total_records),
                'estimated_cost_per_hour': self._estimate_stream_cost(
                    len(stream_desc['Shards']),
                    total_records
                )
            }

            logger.info("=== Kinesis Stream Metrics ===")
            logger.info(f"   Stream: {stats['stream_name']}")
            logger.info(f"   Status: {stats['status']}")
            logger.info(f"   Shards: {stats['shards']}")
            logger.info(f"   Retention: {stats['retention_hours']} hours")
            logger.info(f"   Records (last hour): {stats['records_last_hour']:,}")
            logger.info(f"   Estimated Cost: ${stats['estimated_cost_per_hour']:.4f}/hour")

            return stats

        except ClientError as e:
            logger.error(f"❌ Failed to get stream metrics: {e}")
            raise

    def _estimate_stream_cost(self, shards: int, records_per_hour: int) -> float:
        """
        Estimate Kinesis stream cost.

        Pricing (US-East-1):
        - Shard hour: $0.015
        - PUT payload unit (25 KB): $0.000014

        Args:
            shards: Number of shards
            records_per_hour: Events per hour

        Returns:
            Estimated cost per hour (USD)
        """
        # Shard cost
        shard_cost = shards * 0.015

        # PUT cost (assume 1 KB per event)
        payload_units = records_per_hour / 25  # 25 KB per unit
        put_cost = payload_units * 0.014 / 1000  # $0.014 per 1,000 units

        return shard_cost + put_cost


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Lambda Architecture - Speed Layer')

    parser.add_argument(
        '--mode',
        choices=['setup', 'producer', 'consumer', 'query', 'reset', 'latency-test', 'metrics'],
        default='consumer',
        help='Execution mode'
    )

    parser.add_argument(
        '--env',
        choices=['localstack', 'aws'],
        default='localstack',
        help='Environment (LocalStack or real AWS)'
    )

    parser.add_argument(
        '--user-id',
        type=str,
        help='User ID to query (for query mode)'
    )

    parser.add_argument(
        '--rate',
        type=int,
        default=10,
        help='Events per second (for producer mode)'
    )

    parser.add_argument(
        '--duration',
        type=int,
        help='Duration in seconds (for producer mode)'
    )

    parser.add_argument(
        '--samples',
        type=int,
        default=100,
        help='Number of samples (for latency-test mode)'
    )

    args = parser.parse_args()

    # Initialize processor
    processor = SpeedLayerProcessor(use_localstack=(args.env == 'localstack'))

    if args.mode == 'setup':
        logger.info("🚀 Setting up infrastructure...")
        resources = processor.setup_infrastructure()
        logger.info("✅ Infrastructure ready")
        print(json.dumps(resources, indent=2))

    elif args.mode == 'producer':
        logger.info(f"📤 Starting producer (rate: {args.rate}/sec)...")
        stats = processor.produce_events_continuously(
            rate_per_second=args.rate,
            duration_seconds=args.duration
        )
        print(json.dumps(stats, indent=2))

    elif args.mode == 'consumer':
        logger.info("📥 Starting consumer...")
        processor.consume_stream_continuously()

    elif args.mode == 'query':
        if not args.user_id:
            logger.error("❌ --user-id required for query mode")
            sys.exit(1)

        logger.info(f"🔍 Querying metrics for {args.user_id}...")
        metrics = processor.query_realtime_metrics(args.user_id)

        print("=" * 60)
        print(f"👤 User: {metrics['user_id']}")
        print(f"   Orders Today: {metrics['orders_today']}")
        print(f"   Revenue Today: ${metrics['revenue_today']:,.2f}")
        print(f"   Last Order: {metrics['last_order_time']}")
        print("=" * 60)

    elif args.mode == 'reset':
        logger.info("🔄 Resetting daily metrics...")
        result = processor.reset_daily_metrics()
        print(json.dumps(result, indent=2))

    elif args.mode == 'latency-test':
        logger.info(f"⏱️  Measuring latency ({args.samples} samples)...")
        stats = processor.measure_latency(samples=args.samples)
        print(json.dumps(stats, indent=2))

    elif args.mode == 'metrics':
        logger.info("📊 Getting stream metrics...")
        stats = processor.get_stream_metrics()
        print(json.dumps(stats, indent=2, default=str))

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
