"""
Event Store for Event Sourcing

This module implements an immutable event log using DynamoDB.
All state changes stored as events (never updated, only appended).

Key Features:
1. Append-only event log (DynamoDB)
2. Optimistic locking (version numbers)
3. Replay events to reconstruct state
4. Snapshots for performance (every 100 events)
5. Temporal queries (state at specific time)

Author: Training Module 18
"""

import sys
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Any

import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EventStore:
    """
    Immutable event store for Event Sourcing.

    Stores all domain events in DynamoDB (append-only).
    """

    def __init__(
        self,
        table_name: str = "event_store",
        snapshot_table: str = "event_snapshots",
        region: str = "us-east-1",
        use_localstack: bool = False
    ):
        """
        Initialize Event Store.

        Args:
            table_name: DynamoDB table for events
            snapshot_table: DynamoDB table for snapshots
            region: AWS region
            use_localstack: If True, use LocalStack
        """
        self.table_name = table_name
        self.snapshot_table = snapshot_table
        self.region = region

        # AWS clients
        endpoint_url = "http://localhost:4566" if use_localstack else None

        self.dynamodb = boto3.client('dynamodb', region_name=region, endpoint_url=endpoint_url)
        self.eventbridge = boto3.client('events', region_name=region, endpoint_url=endpoint_url)

        logger.info("EventStore initialized")
        logger.info(f"   Event Table: {table_name}")
        logger.info(f"   Snapshot Table: {snapshot_table}")

    def setup_infrastructure(self) -> Dict[str, Any]:
        """
        Create DynamoDB tables for events and snapshots.

        Returns:
            Dict with created resources
        """
        logger.info("=== Setting Up Event Store ===")

        results = {}

        # Create event store table
        try:
            self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {'AttributeName': 'aggregate_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'aggregate_id', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST',
                StreamSpecification={
                    'StreamEnabled': True,
                    'StreamViewType': 'NEW_IMAGE'
                }
            )
            logger.info(f"✅ Created event table: {self.table_name}")
            results['event_table'] = self.table_name

        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                logger.info(f"✅ Event table exists: {self.table_name}")
                results['event_table'] = self.table_name
            else:
                raise

        # Create snapshot table
        try:
            self.dynamodb.create_table(
                TableName=self.snapshot_table,
                KeySchema=[
                    {'AttributeName': 'aggregate_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'aggregate_id', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            logger.info(f"✅ Created snapshot table: {self.snapshot_table}")
            results['snapshot_table'] = self.snapshot_table

        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                logger.info(f"✅ Snapshot table exists: {self.snapshot_table}")
                results['snapshot_table'] = self.snapshot_table
            else:
                raise

        # Create EventBridge event bus
        try:
            self.eventbridge.create_event_bus(Name='data-mesh-events')
            logger.info("✅ Created EventBridge bus: data-mesh-events")
            results['event_bus'] = 'data-mesh-events'

        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceAlreadyExistsException':
                logger.info("✅ EventBridge bus exists: data-mesh-events")
                results['event_bus'] = 'data-mesh-events'
            else:
                raise

        return results

    def append_event(
        self,
        aggregate_id: str,
        event_type: str,
        data: Dict[str, Any],
        expected_version: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Append event to store (IMMUTABLE - no updates allowed).

        Args:
            aggregate_id: Aggregate identifier (e.g., order_id)
            event_type: Event type (OrderPlaced, PaymentProcessed, etc.)
            data: Event payload
            expected_version: For optimistic locking

        Returns:
            Dict with event metadata
        """
        timestamp = datetime.now().isoformat()

        # Get current version
        current_version = self._get_latest_version(aggregate_id)
        new_version = current_version + 1

        # Optimistic locking check
        if expected_version is not None and expected_version != current_version:
            raise Exception(
                f"Concurrency conflict: Expected v{expected_version}, found v{current_version}"
            )

        logger.info(f"📝 Appending event: {aggregate_id}.{event_type} (v{new_version})")

        try:
            # Append to event store
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item={
                    'aggregate_id': {'S': aggregate_id},
                    'timestamp': {'S': timestamp},
                    'event_type': {'S': event_type},
                    'version': {'N': str(new_version)},
                    'data': {'S': json.dumps(data, default=str)},
                    'created_at': {'S': timestamp}
                },
                ConditionExpression='attribute_not_exists(aggregate_id) OR attribute_not_exists(#ts)',
                ExpressionAttributeNames={'#ts': 'timestamp'}
            )

            logger.info(f"✅ Event stored: v{new_version}")

            # Publish to EventBridge
            self._publish_event(aggregate_id, event_type, data, new_version)

            # Check if snapshot needed
            if new_version % 100 == 0:
                self._create_snapshot(aggregate_id, new_version)

            return {
                'aggregate_id': aggregate_id,
                'event_type': event_type,
                'version': new_version,
                'timestamp': timestamp
            }

        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                logger.error("❌ Event already exists (duplicate)")
                raise Exception("Event already exists")
            else:
                logger.error(f"❌ Failed to append event: {e}")
                raise

    def get_events(
        self,
        aggregate_id: str,
        from_version: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get all events for aggregate.

        Args:
            aggregate_id: Aggregate identifier
            from_version: Start from version (for incremental replay)

        Returns:
            List of events
        """
        logger.info(f"🔍 Getting events: {aggregate_id} (from v{from_version})")

        try:
            response = self.dynamodb.query(
                TableName=self.table_name,
                KeyConditionExpression='aggregate_id = :id',
                ExpressionAttributeValues={':id': {'S': aggregate_id}}
            )

            events = []

            for item in response['Items']:
                version = int(item['version']['N'])

                if version >= from_version:
                    events.append({
                        'aggregate_id': item['aggregate_id']['S'],
                        'timestamp': item['timestamp']['S'],
                        'event_type': item['event_type']['S'],
                        'version': version,
                        'data': json.loads(item['data']['S'])
                    })

            logger.info(f"✅ Found {len(events)} events (v{events[0]['version'] if events else 0} - v{events[-1]['version'] if events else 0})")

            return events

        except ClientError as e:
            logger.error(f"❌ Failed to get events: {e}")
            return []

    def get_events_at_time(
        self,
        aggregate_id: str,
        target_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get events up to specific time (temporal query).

        Args:
            aggregate_id: Aggregate identifier
            target_time: Query events up to this time

        Returns:
            List of events before target_time
        """
        logger.info(f"🕒 Temporal query: {aggregate_id} at {target_time}")

        all_events = self.get_events(aggregate_id)

        # Filter by timestamp
        filtered_events = [
            e for e in all_events
            if datetime.fromisoformat(e['timestamp']) <= target_time
        ]

        logger.info(f"✅ Found {len(filtered_events)} events before {target_time}")

        return filtered_events

    def _get_latest_version(self, aggregate_id: str) -> int:
        """Get latest version number for aggregate."""
        try:
            response = self.dynamodb.query(
                TableName=self.table_name,
                KeyConditionExpression='aggregate_id = :id',
                ExpressionAttributeValues={':id': {'S': aggregate_id}},
                ScanIndexForward=False,  # Descending order
                Limit=1
            )

            if response['Items']:
                return int(response['Items'][0]['version']['N'])
            else:
                return 0  # No events yet

        except ClientError:
            return 0

    def _publish_event(
        self,
        aggregate_id: str,
        event_type: str,
        data: Dict[str, Any],
        version: int
    ) -> None:
        """Publish event to EventBridge."""
        try:
            self.eventbridge.put_events(
                Entries=[{
                    'Source': 'event-store',
                    'DetailType': event_type,
                    'Detail': json.dumps({
                        'aggregate_id': aggregate_id,
                        'event_type': event_type,
                        'version': version,
                        'data': data
                    }, default=str),
                    'EventBusName': 'data-mesh-events'
                }]
            )

            logger.debug(f"📤 Published to EventBridge: {event_type}")

        except ClientError as e:
            logger.warning(f"⚠️  Failed to publish event: {e}")

    def _create_snapshot(self, aggregate_id: str, version: int) -> None:
        """Create snapshot of current state."""
        logger.info(f"📸 Creating snapshot: {aggregate_id} at v{version}")

        # Replay all events to get current state
        events = self.get_events(aggregate_id)
        state = self._replay_events(events)

        try:
            self.dynamodb.put_item(
                TableName=self.snapshot_table,
                Item={
                    'aggregate_id': {'S': aggregate_id},
                    'version': {'N': str(version)},
                    'state': {'S': json.dumps(state, default=str)},
                    'created_at': {'S': datetime.now().isoformat()}
                }
            )

            logger.info(f"✅ Snapshot created at v{version}")

        except ClientError as e:
            logger.warning(f"⚠️  Failed to create snapshot: {e}")

    def _replay_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Replay events to reconstruct state.

        Args:
            events: List of events

        Returns:
            Current state
        """
        state = {
            'status': 'unknown',
            'items': [],
            'amount': 0.0,
            'payment_status': 'unpaid',
            'shipping_status': 'not_shipped'
        }

        for event in events:
            event_type = event['event_type']
            data = event['data']

            # Apply event to state
            if event_type == 'OrderPlaced':
                state['status'] = 'pending'
                state['customer_id'] = data.get('customer_id')
                state['items'] = data.get('items', [])
                state['amount'] = data.get('amount', 0.0)

            elif event_type == 'PaymentProcessed':
                state['payment_status'] = 'paid'
                state['payment_method'] = data.get('payment_method')

            elif event_type == 'OrderShipped':
                state['status'] = 'shipped'
                state['shipping_status'] = 'shipped'
                state['tracking_number'] = data.get('tracking_number')

            elif event_type == 'OrderDelivered':
                state['status'] = 'delivered'
                state['shipping_status'] = 'delivered'

            elif event_type == 'OrderCancelled':
                state['status'] = 'cancelled'
                state['cancellation_reason'] = data.get('reason')

        return state

    def get_current_state(self, aggregate_id: str) -> Dict[str, Any]:
        """
        Get current state by replaying events.

        Args:
            aggregate_id: Aggregate identifier

        Returns:
            Current state
        """
        logger.info(f"🔄 Reconstructing state: {aggregate_id}")

        # Check for snapshot first
        snapshot = self._get_latest_snapshot(aggregate_id)

        if snapshot:
            logger.info(f"   Using snapshot at v{snapshot['version']}")

            # Replay only events after snapshot
            events = self.get_events(aggregate_id, from_version=snapshot['version'] + 1)
            state = snapshot['state']

            # Apply incremental events
            for event in events:
                state = self._apply_event(state, event)

        else:
            # Full replay
            events = self.get_events(aggregate_id)
            state = self._replay_events(events)

        logger.info(f"✅ State reconstructed (from {len(events)} events)")

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
            target_time: Target time

        Returns:
            State at target_time
        """
        logger.info(f"🕒 Temporal query: {aggregate_id} at {target_time}")

        # Get events before target time
        events = self.get_events_at_time(aggregate_id, target_time)

        # Replay events
        state = self._replay_events(events)

        logger.info(f"✅ State at {target_time}: {state.get('status', 'unknown')}")

        return state

    def _get_latest_snapshot(self, aggregate_id: str) -> Optional[Dict[str, Any]]:
        """Get latest snapshot for aggregate."""
        try:
            response = self.dynamodb.get_item(
                TableName=self.snapshot_table,
                Key={'aggregate_id': {'S': aggregate_id}}
            )

            if 'Item' in response:
                return {
                    'aggregate_id': response['Item']['aggregate_id']['S'],
                    'version': int(response['Item']['version']['N']),
                    'state': json.loads(response['Item']['state']['S'])
                }
            else:
                return None

        except ClientError:
            return None

    def _apply_event(self, state: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
        """Apply single event to state."""
        event_type = event['event_type']
        data = event['data']

        if event_type == 'OrderPlaced':
            state.update({
                'status': 'pending',
                'customer_id': data.get('customer_id'),
                'items': data.get('items', []),
                'amount': data.get('amount', 0.0)
            })

        elif event_type == 'PaymentProcessed':
            state['payment_status'] = 'paid'

        elif event_type == 'OrderShipped':
            state['status'] = 'shipped'
            state['tracking_number'] = data.get('tracking_number')

        elif event_type == 'OrderCancelled':
            state['status'] = 'cancelled'

        return state

    def get_event_statistics(self) -> Dict[str, Any]:
        """
        Get event store statistics.

        Returns:
            Dict with statistics
        """
        logger.info("=== Event Store Statistics ===")

        try:
            # Get table info
            response = self.dynamodb.describe_table(TableName=self.table_name)
            table_info = response['Table']

            item_count = table_info.get('ItemCount', 0)
            table_size_mb = table_info.get('TableSizeBytes', 0) / 1024 / 1024

            # Count event types (sample scan)
            scan_response = self.dynamodb.scan(
                TableName=self.table_name,
                Limit=1000
            )

            event_types = {}
            for item in scan_response['Items']:
                event_type = item['event_type']['S']
                event_types[event_type] = event_types.get(event_type, 0) + 1

            stats = {
                'total_events': item_count,
                'table_size_mb': table_size_mb,
                'event_types': event_types,
                'events_per_type': len(event_types)
            }

            logger.info(f"   Total Events: {stats['total_events']:,}")
            logger.info(f"   Table Size: {stats['table_size_mb']:.2f} MB")
            logger.info(f"   Event Types: {stats['events_per_type']}")

            for event_type, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"      {event_type}: {count:,}")

            return stats

        except ClientError as e:
            logger.error(f"❌ Failed to get statistics: {e}")
            return {}


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Event Sourcing - Event Store')

    parser.add_argument(
        '--mode',
        choices=['setup', 'append', 'get', 'replay', 'temporal', 'stats'],
        default='get',
        help='Operation mode'
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
        help='Aggregate ID (e.g., order_id)'
    )

    parser.add_argument(
        '--event-type',
        type=str,
        help='Event type (OrderPlaced, PaymentProcessed, etc.)'
    )

    parser.add_argument(
        '--data',
        type=str,
        help='Event data (JSON string)'
    )

    parser.add_argument(
        '--timestamp',
        type=str,
        help='Timestamp for temporal query'
    )

    args = parser.parse_args()

    # Initialize event store
    store = EventStore(use_localstack=(args.env == 'localstack'))

    if args.mode == 'setup':
        resources = store.setup_infrastructure()
        print(json.dumps(resources, indent=2))

    elif args.mode == 'append':
        if not (args.aggregate and args.event_type and args.data):
            logger.error("❌ --aggregate, --event-type, and --data required")
            sys.exit(1)

        data = json.loads(args.data)

        result = store.append_event(
            aggregate_id=args.aggregate,
            event_type=args.event_type,
            data=data
        )

        print(json.dumps(result, indent=2))

    elif args.mode == 'get':
        if not args.aggregate:
            logger.error("❌ --aggregate required")
            sys.exit(1)

        events = store.get_events(args.aggregate)

        print("\n" + "=" * 80)
        print(f"📜 EVENT HISTORY: {args.aggregate}")
        print("=" * 80)

        for i, event in enumerate(events, 1):
            print(f"\n{i}. {event['event_type']} (v{event['version']})")
            print(f"   Time: {event['timestamp']}")
            print(f"   Data: {json.dumps(event['data'], indent=6)}")

        print("\n" + "=" * 80)

    elif args.mode == 'replay':
        if not args.aggregate:
            logger.error("❌ --aggregate required")
            sys.exit(1)

        state = store.get_current_state(args.aggregate)

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

        state = store.get_state_at_time(args.aggregate, target_time)

        print("\n" + "=" * 80)
        print(f"🕒 STATE AT {target_time}")
        print("=" * 80)
        print(json.dumps(state, indent=2, default=str))
        print("=" * 80)

    elif args.mode == 'stats':
        store.get_event_statistics()

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
