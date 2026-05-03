"""
Query Projections for CQRS

This module maintains read models (projections) updated from events.
Separates read path from write path for performance optimization.

Key Features:
1. Current state projection (ElastiCache Redis)
2. Historical analytics (Redshift/Athena)
3. Full-text search (OpenSearch - simulated)
4. Eventual consistency handling
5. Projection rebuilds from events

Author: Training Module 18
"""

import os
import sys
import json
import logging
import argparse
import time
from datetime import datetime
from typing import Dict, List, Any

import boto3

# Import event store
sys.path.append(os.path.dirname(__file__))
from event_store import EventStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QueryProjections:
    """
    Manages read models (projections) for CQRS architecture.

    Updates projections based on events from event store.
    """

    def __init__(
        self,
        region: str = "us-east-1",
        use_localstack: bool = False
    ):
        """
        Initialize Query Projections.

        Args:
            region: AWS region
            use_localstack: If True, use LocalStack
        """
        self.region = region
        self.event_store = EventStore(use_localstack=use_localstack)

        # AWS clients
        endpoint_url = "http://localhost:4566" if use_localstack else None

        self.dynamodb = boto3.client('dynamodb', region_name=region, endpoint_url=endpoint_url)

        # Redis simulation (in-memory cache)
        self.cache = {}

        logger.info("QueryProjections initialized")

    def get_current_state(self, aggregate_id: str) -> Dict[str, Any]:
        """
        Get current state from cache (fast).

        Args:
            aggregate_id: Aggregate identifier

        Returns:
            Current state (from ElastiCache projection)
        """
        logger.info(f"🔍 Query current state: {aggregate_id}")

        # Check cache first
        if aggregate_id in self.cache:
            logger.info("✅ Cache hit (ElastiCache)")
            return self.cache[aggregate_id]

        # Cache miss - rebuild from events
        logger.info("⚠️  Cache miss - rebuilding from events...")

        state = self.event_store.get_current_state(aggregate_id)

        # Update cache
        self.cache[aggregate_id] = state

        return state

    def get_state_at_time(
        self,
        aggregate_id: str,
        target_time: datetime
    ) -> Dict[str, Any]:
        """
        Get state at specific time (temporal query).

        Args:
            aggregate_id: Aggregate identifier
            target_time: Query state at this time

        Returns:
            Historical state
        """
        logger.info(f"🕒 Temporal query: {aggregate_id} at {target_time}")

        # Replay events up to target time
        state = self.event_store.get_state_at_time(aggregate_id, target_time)

        return state

    def rebuild_projection(
        self,
        aggregate_id: str,
        projection_type: str = 'current_state'
    ) -> Dict[str, Any]:
        """
        Rebuild projection from events (fix corruption, add new fields).

        Args:
            aggregate_id: Aggregate identifier
            projection_type: Type of projection to rebuild

        Returns:
            Rebuilt state
        """
        logger.info(f"🔧 Rebuilding projection: {aggregate_id} ({projection_type})")

        # Replay all events
        events = self.event_store.get_events(aggregate_id)

        logger.info(f"   Events: {len(events)}")

        if projection_type == 'current_state':
            # Rebuild current state (ElastiCache)
            state = self.event_store._replay_events(events)

            # Update cache
            self.cache[aggregate_id] = state

            logger.info("✅ Current state projection rebuilt")

            return state

        elif projection_type == 'analytics':
            # Rebuild analytics (Redshift)
            # In production: write to Redshift table

            analytics = {
                'aggregate_id': aggregate_id,
                'total_events': len(events),
                'event_types': {},
                'lifecycle_duration': None
            }

            # Count event types
            for event in events:
                event_type = event['event_type']
                analytics['event_types'][event_type] = analytics['event_types'].get(event_type, 0) + 1

            # Calculate lifecycle duration
            if events:
                first_event = datetime.fromisoformat(events[0]['timestamp'])
                last_event = datetime.fromisoformat(events[-1]['timestamp'])
                analytics['lifecycle_duration'] = (last_event - first_event).total_seconds()

            logger.info("✅ Analytics projection rebuilt")

            return analytics

        else:
            raise ValueError(f"Unknown projection type: {projection_type}")

    def get_order_lifecycle(self, aggregate_id: str) -> List[Dict[str, Any]]:
        """
        Get order lifecycle timeline (all events with timestamps).

        Args:
            aggregate_id: Order ID

        Returns:
            List of lifecycle stages
        """
        logger.info(f"📊 Getting lifecycle: {aggregate_id}")

        events = self.event_store.get_events(aggregate_id)

        timeline = []

        for event in events:
            timeline.append({
                'event': event['event_type'],
                'timestamp': event['timestamp'],
                'version': event['version']
            })

        # Calculate durations between stages
        if len(timeline) > 1:
            for i in range(1, len(timeline)):
                prev_time = datetime.fromisoformat(timeline[i-1]['timestamp'])
                curr_time = datetime.fromisoformat(timeline[i]['timestamp'])

                duration_seconds = (curr_time - prev_time).total_seconds()
                timeline[i]['duration_from_previous_sec'] = duration_seconds

        return timeline

    def measure_eventual_consistency_lag(
        self,
        num_samples: int = 100
    ) -> Dict[str, Any]:
        """
        Measure lag between event write and projection update.

        Args:
            num_samples: Number of commands to test

        Returns:
            Dict with latency statistics
        """
        logger.info(f"=== Measuring Eventual Consistency Lag ({num_samples} samples) ===")

        from command_handler import CommandHandler

        handler = CommandHandler(use_localstack=True)

        lags = []

        for i in range(num_samples):
            order_id = f"TEST_ORD_{i:04d}"

            # Execute command (write)
            start_time = time.time()

            handler.execute_command(
                'PlaceOrder',
                order_id,
                {
                    'customer_id': f'CUST_{i}',
                    'items': [{'product_id': 'PROD_TEST', 'quantity': 1}],
                    'amount': 100.00
                }
            )

            # Poll until available in projection (read)
            while True:
                if order_id in self.cache:
                    lag_ms = (time.time() - start_time) * 1000
                    lags.append(lag_ms)
                    break

                time.sleep(0.01)  # 10ms poll interval

                # Simulate projection update (in production: EventBridge → Lambda)
                state = self.event_store.get_current_state(order_id)
                self.cache[order_id] = state

            if (i + 1) % 10 == 0:
                logger.info(f"   Tested: {i + 1} / {num_samples}")

        # Calculate statistics
        lags.sort()
        p50 = lags[int(len(lags) * 0.50)]
        p95 = lags[int(len(lags) * 0.95)]
        p99 = lags[int(len(lags) * 0.99)]

        stats = {
            'samples': num_samples,
            'p50_ms': p50,
            'p95_ms': p95,
            'p99_ms': p99,
            'min_ms': min(lags),
            'max_ms': max(lags),
            'avg_ms': sum(lags) / len(lags)
        }

        logger.info("✅ Lag measurement complete")
        logger.info(f"   P50: {p50:.1f}ms")
        logger.info(f"   P95: {p95:.1f}ms")
        logger.info(f"   P99: {p99:.1f}ms")

        return stats


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='CQRS - Query Projections')

    parser.add_argument(
        '--mode',
        choices=['current', 'temporal', 'rebuild', 'lifecycle', 'measure-lag'],
        default='current',
        help='Query mode'
    )

    parser.add_argument(
        '--env',
        choices=['localstack', 'aws'],
        default='localstack',
        help='Environment'
    )

    parser.add_argument(
        '--aggregate',
        type=str,
        help='Aggregate ID'
    )

    parser.add_argument(
        '--timestamp',
        type=str,
        help='Timestamp for temporal query'
    )

    args = parser.parse_args()

    # Initialize projections
    projections = QueryProjections(use_localstack=(args.env == 'localstack'))

    if args.mode == 'current':
        if not args.aggregate:
            logger.error("❌ --aggregate required")
            sys.exit(1)

        state = projections.get_current_state(args.aggregate)

        print("\n" + "=" * 80)
        print(f"📊 CURRENT STATE: {args.aggregate}")
        print("=" * 80)
        print(json.dumps(state, indent=2, default=str))
        print("=" * 80)

    elif args.mode == 'temporal':
        if not (args.aggregate and args.timestamp):
            logger.error("❌ --aggregate and --timestamp required")
            sys.exit(1)

        target_time = datetime.fromisoformat(args.timestamp)

        state = projections.get_state_at_time(args.aggregate, target_time)

        print("\n" + "=" * 80)
        print(f"🕒 STATE AT {target_time}")
        print("=" * 80)
        print(json.dumps(state, indent=2, default=str))
        print("=" * 80)

    elif args.mode == 'rebuild':
        if not args.aggregate:
            logger.error("❌ --aggregate required")
            sys.exit(1)

        state = projections.rebuild_projection(args.aggregate)
        print(json.dumps(state, indent=2, default=str))

    elif args.mode == 'lifecycle':
        if not args.aggregate:
            logger.error("❌ --aggregate required")
            sys.exit(1)

        timeline = projections.get_order_lifecycle(args.aggregate)

        print("\n" + "=" * 80)
        print(f"📈 ORDER LIFECYCLE: {args.aggregate}")
        print("=" * 80)

        for i, stage in enumerate(timeline, 1):
            duration_str = ""
            if 'duration_from_previous_sec' in stage:
                duration_str = f" (+{stage['duration_from_previous_sec']:.0f}s)"

            print(f"{i}. {stage['event']} at {stage['timestamp']}{duration_str}")

        print("=" * 80)

    elif args.mode == 'measure-lag':
        stats = projections.measure_eventual_consistency_lag(num_samples=100)

        print("\n" + "=" * 80)
        print("📊 EVENTUAL CONSISTENCY LAG")
        print("=" * 80)
        print(f"   Samples: {stats['samples']}")
        print(f"   P50:     {stats['p50_ms']:.1f}ms")
        print(f"   P95:     {stats['p95_ms']:.1f}ms")
        print(f"   P99:     {stats['p99_ms']:.1f}ms")
        print(f"   Average: {stats['avg_ms']:.1f}ms")
        print("=" * 80)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
