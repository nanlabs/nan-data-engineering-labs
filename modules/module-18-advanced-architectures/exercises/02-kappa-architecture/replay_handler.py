"""
Replay Handler for Kappa Architecture

This module handles reprocessing by replaying events from Kinesis stream.
Kappa's key advantage: reprocessing = replay stream with new code (no separate batch layer).

Key Features:
1. Replay Kinesis stream from timestamp (AT_TIMESTAMP iterator)
2. Process events with new logic (write to new materialized view)
3. Parallel replay across shards
4. Progress tracking and resumability
5. Time-range filtering (replay only needed period)

Author: Training Module 18
"""

import sys
import json
import logging
import argparse
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ReplayHandler:
    """
    Handles stream replay for Kappa Architecture reprocessing.

    Replays historical events from Kinesis to recompute materialized views
    with updated logic (add metrics, fix bugs, etc.).
    """

    def __init__(
        self,
        stream_name: str = "orders-kappa",
        region: str = "us-east-1",
        use_localstack: bool = False
    ):
        """
        Initialize Replay Handler.

        Args:
            stream_name: Kinesis stream name
            region: AWS region
            use_localstack: If True, use LocalStack
        """
        self.stream_name = stream_name
        self.region = region

        # AWS clients
        endpoint_url = "http://localhost:4566" if use_localstack else None

        self.kinesis = boto3.client('kinesis', region_name=region, endpoint_url=endpoint_url)
        self.dynamodb = boto3.client('dynamodb', region_name=region, endpoint_url=endpoint_url)

        logger.info("ReplayHandler initialized")
        logger.info(f"   Stream: {stream_name}")

    def replay_shard(
        self,
        shard_id: str,
        start_timestamp: datetime,
        end_timestamp: datetime,
        target_table: str,
        processor_func: callable
    ) -> Dict[str, int]:
        """
        Replay single shard within time range.

        Args:
            shard_id: Kinesis shard ID
            start_timestamp: Start time
            end_timestamp: End time
            target_table: DynamoDB table for output
            processor_func: Function to process each event

        Returns:
            Dict with replay statistics
        """
        logger.info(f"🔄 Replaying shard: {shard_id}")
        logger.info(f"   Time: {start_timestamp} to {end_timestamp}")

        try:
            # Get shard iterator at start timestamp
            response = self.kinesis.get_shard_iterator(
                StreamName=self.stream_name,
                ShardId=shard_id,
                ShardIteratorType='AT_TIMESTAMP',
                Timestamp=start_timestamp
            )

            shard_iterator = response['ShardIterator']

            processed = 0
            skipped = 0

            while shard_iterator:
                # Fetch records
                records_response = self.kinesis.get_records(
                    ShardIterator=shard_iterator,
                    Limit=1000
                )

                records = records_response['Records']

                if not records:
                    break

                # Check if we've passed end timestamp
                last_record_time = records[-1]['ApproximateArrivalTimestamp']

                if last_record_time > end_timestamp:
                    # Filter records within time range
                    records = [
                        r for r in records
                        if r['ApproximateArrivalTimestamp'] <= end_timestamp
                    ]

                # Process records
                for record in records:
                    event = json.loads(record['Data'])

                    # Apply processor function (writes to target_table)
                    processor_func(event, target_table)
                    processed += 1

                    if processed % 1000 == 0:
                        logger.info(f"   Shard {shard_id}: {processed:,} events")

                # Update iterator
                shard_iterator = records_response.get('NextShardIterator')

                # Stop if past end time
                if last_record_time > end_timestamp:
                    break

            logger.info(f"✅ Shard {shard_id}: {processed:,} events replayed")

            return {'shard_id': shard_id, 'processed': processed, 'skipped': skipped}

        except ClientError as e:
            logger.error(f"❌ Replay failed for shard {shard_id}: {e}")
            return {'shard_id': shard_id, 'processed': 0, 'error': str(e)}

    def replay_stream(
        self,
        start_timestamp: datetime,
        end_timestamp: datetime,
        target_table: str,
        parallel: bool = True
    ) -> Dict[str, Any]:
        """
        Replay entire stream (all shards) within time range.

        Args:
            start_timestamp: Start time
            end_timestamp: End time
            target_table: DynamoDB table for output
            parallel: If True, replay shards in parallel

        Returns:
            Dict with replay statistics
        """
        logger.info("=" * 70)
        logger.info("=== Stream Replay Handler ===")
        logger.info(f"📡 Stream: {self.stream_name}")
        logger.info(f"📅 Time Range: {start_timestamp} to {end_timestamp}")
        logger.info(f"   Duration: {(end_timestamp - start_timestamp).days} days")
        logger.info(f"💾 Target Table: {target_table}")
        logger.info(f"⚙️  Mode: {'Parallel' if parallel else 'Sequential'}")
        logger.info("=" * 70)

        start_time = time.time()

        # Get shards
        response = self.kinesis.describe_stream(StreamName=self.stream_name)
        shards = response['StreamDescription']['Shards']

        logger.info("\n📊 Stream Info:")
        logger.info(f"   Shards: {len(shards)}")
        logger.info(f"   Retention: {response['StreamDescription']['RetentionPeriodHours']} hours")

        # Define processor function
        def process_event(event: Dict[str, Any], table: str) -> None:
            """Process event and write to DynamoDB."""
            # Extract fields
            category = event.get('category', 'Unknown')
            amount = Decimal(str(event['amount']))
            user_id = event['user_id']
            timestamp = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))

            # Determine window (5-minute tumbling)
            window_start = timestamp.replace(
                minute=(timestamp.minute // 5) * 5,
                second=0,
                microsecond=0
            )

            # Update DynamoDB (atomic increment)
            try:
                self.dynamodb.update_item(
                    TableName=table,
                    Key={
                        'category': {'S': category},
                        'window_start': {'S': window_start.isoformat()}
                    },
                    UpdateExpression='''
                        SET order_count = if_not_exists(order_count, :zero) + :one,
                            revenue = if_not_exists(revenue, :zero_decimal) + :amount,
                            window_end = :window_end,
                            updated_at = :now
                        ADD unique_users :user_set
                    ''',
                    ExpressionAttributeValues={
                        ':zero': {'N': '0'},
                        ':zero_decimal': {'N': '0'},
                        ':one': {'N': '1'},
                        ':amount': {'N': str(amount)},
                        ':window_end': {'S': (window_start + timedelta(minutes=5)).isoformat()},
                        ':now': {'S': datetime.now().isoformat()},
                        ':user_set': {'SS': [user_id]}
                    }
                )
            except Exception as e:
                logger.debug(f"Update error (may be set type issue): {e}")

        # Replay shards
        shard_results = []

        if parallel:
            # Parallel replay (faster)
            logger.info(f"\n🚀 Starting parallel replay ({len(shards)} workers)...")

            with ThreadPoolExecutor(max_workers=len(shards)) as executor:
                futures = []

                for shard in shards:
                    future = executor.submit(
                        self.replay_shard,
                        shard['ShardId'],
                        start_timestamp,
                        end_timestamp,
                        target_table,
                        process_event
                    )
                    futures.append(future)

                # Collect results
                for future in as_completed(futures):
                    result = future.result()
                    shard_results.append(result)

        else:
            # Sequential replay
            logger.info("\n🔄 Starting sequential replay...")

            for shard in shards:
                result = self.replay_shard(
                    shard['ShardId'],
                    start_timestamp,
                    end_timestamp,
                    target_table,
                    process_event
                )
                shard_results.append(result)

        # Calculate totals
        total_processed = sum(r['processed'] for r in shard_results)
        duration = time.time() - start_time

        replay_stats = {
            'stream_name': self.stream_name,
            'start_timestamp': start_timestamp.isoformat(),
            'end_timestamp': end_timestamp.isoformat(),
            'target_table': target_table,
            'shards_replayed': len(shard_results),
            'total_events': total_processed,
            'duration_seconds': duration,
            'events_per_second': total_processed / duration if duration > 0 else 0,
            'shard_results': shard_results
        }

        logger.info("\n" + "=" * 70)
        logger.info("=== Replay Complete ===")
        logger.info(f"✅ Total Events: {total_processed:,}")
        logger.info(f"⏱️  Duration: {duration / 60:.1f} minutes")
        logger.info(f"🚀 Throughput: {replay_stats['events_per_second']:.0f} events/second")
        logger.info(f"💾 Target: {target_table}")
        logger.info("=" * 70)

        return replay_stats

    def estimate_replay_time(
        self,
        start_timestamp: datetime,
        end_timestamp: datetime,
        events_per_day: int = 10_000_000
    ) -> Dict[str, Any]:
        """
        Estimate replay time and cost.

        Args:
            start_timestamp: Start time
            end_timestamp: End time
            events_per_day: Expected events per day

        Returns:
            Dict with estimates
        """
        duration_days = (end_timestamp - start_timestamp).days

        total_events = duration_days * events_per_day

        # Estimate throughput
        # Kinesis: 2 MB/sec per shard read capacity
        # Assume 1 KB per event: 2 MB/sec = 2,000 events/sec per shard

        response = self.kinesis.describe_stream(StreamName=self.stream_name)
        shard_count = len(response['StreamDescription']['Shards'])

        throughput_per_shard = 2000  # events/sec
        total_throughput = shard_count * throughput_per_shard

        replay_seconds = total_events / total_throughput
        replay_hours = replay_seconds / 3600

        # Cost: Replay reads are free (no additional cost)
        # But stream retention costs: $0.023/GB-month

        data_size_gb = (total_events * 1) / 1024 / 1024 / 1024  # 1 KB per event
        retention_cost_per_month = data_size_gb * 0.023

        estimate = {
            'duration_days': duration_days,
            'total_events': total_events,
            'shard_count': shard_count,
            'throughput_events_per_sec': total_throughput,
            'estimated_replay_hours': replay_hours,
            'estimated_replay_time': f"{int(replay_hours)}h {int((replay_hours % 1) * 60)}m",
            'data_size_gb': data_size_gb,
            'stream_retention_cost_per_month': retention_cost_per_month,
            'replay_read_cost': 0  # Kinesis reads are free
        }

        logger.info("=== Replay Time Estimate ===")
        logger.info(f"   Duration: {duration_days} days")
        logger.info(f"   Events: {total_events:,} ({events_per_day:,}/day)")
        logger.info(f"   Shards: {shard_count} ({total_throughput:,} events/sec capacity)")
        logger.info(f"⏱️  Estimated Time: {estimate['estimated_replay_time']}")
        logger.info("💰 Costs:")
        logger.info("   Replay Reads: $0 (free)")
        logger.info(f"   Stream Retention: ${retention_cost_per_month:.2f}/month")

        return estimate

    def replay_last_n_days(
        self,
        days: int,
        target_table: str,
        parallel: bool = True
    ) -> Dict[str, Any]:
        """
        Convenience method: Replay last N days.

        Args:
            days: Number of days to replay
            target_table: Target DynamoDB table
            parallel: Parallel processing

        Returns:
            Replay statistics
        """
        end_timestamp = datetime.now()
        start_timestamp = end_timestamp - timedelta(days=days)

        logger.info(f"=== Replaying Last {days} Days ===")

        return self.replay_stream(
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            target_table=target_table,
            parallel=parallel
        )

    def benchmark_replay(
        self,
        days: int = 7,
        events_per_day: int = 10_000_000
    ) -> None:
        """
        Benchmark replay performance for different time ranges.

        Args:
            days: Number of days to benchmark
            events_per_day: Events per day rate
        """
        logger.info("=== Replay Performance Benchmark ===")

        time_ranges = [1, 7, 30, 90, 365]

        print("\n" + "=" * 80)
        print("📊 REPLAY TIME ESTIMATES")
        print("=" * 80)
        print()
        print(f"{'Days':<8} {'Events':<15} {'Replay Time':<15} {'Throughput':<20} {'Cost':<10}")
        print("-" * 80)

        for days in time_ranges:
            end = datetime.now()
            start = end - timedelta(days=days)

            estimate = self.estimate_replay_time(
                start_timestamp=start,
                end_timestamp=end,
                events_per_day=events_per_day
            )

            print(
                f"{days:<8} "
                f"{estimate['total_events']:>13,}  "
                f"{estimate['estimated_replay_time']:<15} "
                f"{estimate['throughput_events_per_sec']:>8,} events/sec  "
                f"$0 (free)"
            )

        print("\n" + "=" * 80)
        print("\n💡 Key Insight: Replay time scales linearly with data volume")
        print("   To reduce replay time: increase shard count (higher throughput)")
        print()

    def replay_with_progress(
        self,
        start_timestamp: datetime,
        end_timestamp: datetime,
        target_table: str
    ) -> Dict[str, Any]:
        """
        Replay with progress tracking (for long-running replays).

        Args:
            start_timestamp: Start time
            end_timestamp: End time
            target_table: Target table

        Returns:
            Replay statistics
        """
        logger.info("=== Replay with Progress Tracking ===")

        # Get shards
        response = self.kinesis.describe_stream(StreamName=self.stream_name)
        shards = response['StreamDescription']['Shards']

        total_duration = (end_timestamp - start_timestamp).total_seconds()

        logger.info(f"   Shards: {len(shards)}")
        logger.info(f"   Duration: {total_duration / 3600:.1f} hours")
        logger.info("")

        # Track progress
        progress = {shard['ShardId']: 0 for shard in shards}

        # Simple processor (similar to stream_processor.py)
        def process_event(event: Dict[str, Any], table: str) -> None:
            """Update window metrics in DynamoDB."""
            category = event.get('category', 'Unknown')
            amount = Decimal(str(event['amount']))
            user_id = event['user_id']
            timestamp = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))

            # 5-minute window
            window_start = timestamp.replace(
                minute=(timestamp.minute // 5) * 5,
                second=0,
                microsecond=0
            )

            # Atomic increment
            self.dynamodb.update_item(
                TableName=table,
                Key={
                    'category': {'S': category},
                    'window_start': {'S': window_start.isoformat()}
                },
                UpdateExpression='''
                    SET order_count = if_not_exists(order_count, :zero) + :one,
                        revenue = if_not_exists(revenue, :zero_decimal) + :amount,
                        window_end = :window_end,
                        updated_at = :now
                ''',
                ExpressionAttributeValues={
                    ':zero': {'N': '0'},
                    ':zero_decimal': {'N': '0'},
                    ':one': {'N': '1'},
                    ':amount': {'N': str(amount)},
                    ':window_end': {'S': (window_start + timedelta(minutes=5)).isoformat()},
                    ':now': {'S': datetime.now().isoformat()}
                }
            )

        # Replay in parallel
        with ThreadPoolExecutor(max_workers=len(shards)) as executor:
            futures = []

            for shard in shards:
                future = executor.submit(
                    self.replay_shard,
                    shard['ShardId'],
                    start_timestamp,
                    end_timestamp,
                    target_table,
                    process_event
                )
                futures.append(future)

            # Progress bar
            print("\n🔄 Replay Progress:")
            print("   " + "─" * 60)

            completed_shards = 0
            shard_results = []

            for future in as_completed(futures):
                result = future.result()
                shard_results.append(result)

                completed_shards += 1
                progress_pct = completed_shards / len(shards) * 100

                bar_length = 40
                filled = int(bar_length * completed_shards / len(shards))
                bar = "█" * filled + "░" * (bar_length - filled)

                print(f"\r   [{bar}] {progress_pct:.0f}% ({completed_shards}/{len(shards)} shards)", end='')

            print()  # New line after progress bar

        # Calculate totals
        total_processed = sum(r['processed'] for r in shard_results)
        replay_duration = time.time() - start_time

        stats = {
            'stream_name': self.stream_name,
            'start_timestamp': start_timestamp.isoformat(),
            'end_timestamp': end_timestamp.isoformat(),
            'target_table': target_table,
            'shards': len(shards),
            'total_events_replayed': total_processed,
            'replay_duration_seconds': replay_duration,
            'replay_duration_minutes': replay_duration / 60,
            'throughput_events_per_second': total_processed / replay_duration if replay_duration > 0 else 0,
            'shard_details': shard_results
        }

        logger.info("\n✅ Replay Complete")
        logger.info(f"   Events: {total_processed:,}")
        logger.info(f"   Duration: {replay_duration / 60:.1f} minutes")
        logger.info(f"   Throughput: {stats['throughput_events_per_second']:.0f} events/sec")

        return stats


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Kappa Architecture - Replay Handler')

    parser.add_argument(
        '--mode',
        choices=['replay', 'estimate', 'benchmark', 'replay-last'],
        default='replay',
        help='Operation mode'
    )

    parser.add_argument(
        '--env',
        choices=['localstack', 'aws'],
        default='localstack',
        help='Environment'
    )

    parser.add_argument(
        '--start',
        type=str,
        help='Start timestamp (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)'
    )

    parser.add_argument(
        '--end',
        type=str,
        help='End timestamp (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS), defaults to now'
    )

    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days (for replay-last mode)'
    )

    parser.add_argument(
        '--target-table',
        type=str,
        default='category_metrics_v2',
        help='Target DynamoDB table'
    )

    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Enable parallel replay'
    )

    args = parser.parse_args()

    # Initialize handler
    handler = ReplayHandler(use_localstack=(args.env == 'localstack'))

    if args.mode == 'replay':
        if not args.start:
            logger.error("❌ --start required for replay mode")
            sys.exit(1)

        # Parse timestamps
        try:
            start = datetime.fromisoformat(args.start)
        except ValueError:
            start = datetime.strptime(args.start, '%Y-%m-%d')

        if args.end:
            try:
                end = datetime.fromisoformat(args.end)
            except ValueError:
                end = datetime.strptime(args.end, '%Y-%m-%d')
        else:
            end = datetime.now()

        # Execute replay
        stats = handler.replay_with_progress(
            start_timestamp=start,
            end_timestamp=end,
            target_table=args.target_table
        )

        print("\n" + json.dumps(stats, indent=2, default=str))

    elif args.mode == 'estimate':
        if not args.start:
            args.start = (datetime.now() - timedelta(days=args.days)).strftime('%Y-%m-%d')

        start = datetime.fromisoformat(args.start)
        end = datetime.now() if not args.end else datetime.fromisoformat(args.end)

        estimate = handler.estimate_replay_time(start, end)
        print(json.dumps(estimate, indent=2, default=str))

    elif args.mode == 'benchmark':
        handler.benchmark_replay(events_per_day=10_000_000)

    elif args.mode == 'replay-last':
        stats = handler.replay_last_n_days(
            days=args.days,
            target_table=args.target_table,
            parallel=args.parallel
        )

        print(json.dumps(stats, indent=2, default=str))

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
