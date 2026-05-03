#!/usr/bin/env python3
"""
Ride Event Producer - Starter Template

This script generates and sends ride events to Kinesis Data Streams.
Complete the TODOs to implement the full functionality.

TODO Count: 8
"""

import json
import time
import argparse
from datetime import datetime
from typing import Dict, Any, List
import boto3
from botocore.exceptions import ClientError

# TODO 1: Import Faker for generating realistic test data
# Hint: from faker import Faker
# You'll need to: pip install faker
from faker import Faker


class RideEventProducer:
    """Generates and sends ride events to Kinesis."""

    def __init__(self, stream_name: str, region: str = 'us-east-1'):
        """
        Initialize the producer.

        Args:
            stream_name: Name of the Kinesis stream
            region: AWS region
        """
        self.stream_name = stream_name
        self.region = region

        # TODO 2: Initialize boto3 Kinesis client
        # Hint: self.kinesis = boto3.client('kinesis', region_name=region)
        self.kinesis = boto3.client('kinesis', region_name=region)

        # TODO 3: Initialize Faker for data generation
        # Hint: self.fake = Faker()
        self.fake = Faker()

        self.cities = ['New York', 'San Francisco', 'Chicago', 'Los Angeles', 'Seattle']
        self.ride_types = ['economy', 'premium', 'shared']

    def generate_ride_request(self) -> Dict[str, Any]:
        """
        Generate a ride request event.

        Returns:
            Dictionary containing ride request data
        """
        # TODO 4: Generate ride request event
        # Hints:
        # - Use self.fake.uuid4() for ride_id
        # - Use self.fake.random_int(1000, 9999) for rider_id
        # - Use self.fake.latitude() and self.fake.longitude() for coordinates
        # - Use datetime.utcnow().isoformat() for timestamp
        # - Use random.choice() to select from cities and ride_types

        import random

        event = {
            "event_type": "ride_requested",
            "ride_id": f"ride-{self.fake.uuid4()}",  # TODO: Generate unique ride ID
            "rider_id": f"rider-{self.fake.random_int(1000, 9999)}",  # TODO: Generate rider ID
            "timestamp": datetime.utcnow().isoformat(),
            "pickup_location": {
                "lat": float(f"{self.fake.latitude():.6f}"),  # TODO: Generate latitude
                "lon": float(f"{self.fake.longitude():.6f}"),  # TODO: Generate longitude
                "address": self.fake.street_address(),
                "city": random.choice(self.cities)  # TODO: Select random city
            },
            "dropoff_location": {
                "lat": float(f"{self.fake.latitude():.6f}"),
                "lon": float(f"{self.fake.longitude():.6f}"),
                "address": self.fake.street_address(),
                "city": random.choice(self.cities)
            },
            "ride_type": random.choice(self.ride_types),  # TODO: Select random ride type
            "requested_at": datetime.utcnow().isoformat()
        }

        return event

    def send_event(self, event: Dict[str, Any]) -> bool:
        """
        Send a single event to Kinesis.

        Args:
            event: Event data to send

        Returns:
            True if successful, False otherwise
        """
        try:
            # TODO 5: Send event to Kinesis using put_record
            # Hints:
            # - Convert event to JSON string: json.dumps(event)
            # - Use event['ride_id'] as PartitionKey
            # - Handle response to check for success

            response = self.kinesis.put_record(
                StreamName=self.stream_name,
                Data=json.dumps(event),  # TODO: Convert event to JSON
                PartitionKey=event['ride_id']  # TODO: Use ride_id as partition key
            )

            # Check if record was successfully sent
            if 'SequenceNumber' in response:
                return True
            else:
                return False

        except ClientError as e:
            print(f"Error sending event: {e}")
            return False

    def send_batch(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Send a batch of events to Kinesis.

        Args:
            events: List of events to send

        Returns:
            Dictionary with success and failure counts
        """
        # TODO 6: Implement batch sending using put_records
        # Hints:
        # - Create records list with Data and PartitionKey for each event
        # - Use kinesis.put_records() with Records parameter
        # - Check response['FailedRecordCount'] for failures
        # - Retry failed records with exponential backoff

        records = []
        for event in events:
            records.append({
                'Data': json.dumps(event),  # TODO: Convert to JSON
                'PartitionKey': event['ride_id']  # TODO: Use ride_id as key
            })

        try:
            # TODO: Send batch to Kinesis
            response = self.kinesis.put_records(
                StreamName=self.stream_name,
                Records=records
            )

            failed_count = response.get('FailedRecordCount', 0)
            success_count = len(records) - failed_count

            return {
                'success': success_count,
                'failed': failed_count
            }

        except ClientError as e:
            print(f"Error sending batch: {e}")
            return {
                'success': 0,
                'failed': len(records)
            }

    def generate_and_send(self, count: int = 1, batch_size: int = 100,
                         rate_limit: float = 0.1) -> Dict[str, int]:
        """
        Generate and send multiple events.

        Args:
            count: Number of events to generate
            batch_size: Size of batches for sending
            rate_limit: Delay between batches (seconds)

        Returns:
            Statistics about sent events
        """
        print(f"Generating and sending {count} events to {self.stream_name}...")

        total_success = 0
        total_failed = 0

        # TODO 7: Implement batch generation and sending
        # Hints:
        # - Generate events in batches
        # - Use send_batch() for efficiency
        # - Add rate limiting with time.sleep()
        # - Track success/failure statistics

        for i in range(0, count, batch_size):
            batch_count = min(batch_size, count - i)

            # Generate batch
            batch_events = []
            for _ in range(batch_count):
                event = self.generate_ride_request()  # TODO: Generate event
                batch_events.append(event)

            # Send batch
            result = self.send_batch(batch_events)  # TODO: Send batch

            total_success += result['success']
            total_failed += result['failed']

            print(f"Sent {i + batch_count}/{count} events "
                  f"(success: {total_success}, failed: {total_failed})")

            # TODO: Add rate limiting
            if i + batch_count < count:
                time.sleep(rate_limit)

        return {
            'total': count,
            'success': total_success,
            'failed': total_failed
        }


def main():
    """Main entry point."""
    # TODO 8: Implement command-line interface
    # Hints:
    # - Use argparse to handle command-line arguments
    # - Arguments: --stream-name, --count, --batch-size, --rate-limit, --region
    # - Create producer instance and call generate_and_send()

    parser = argparse.ArgumentParser(
        description='Generate and send ride events to Kinesis'
    )

    # TODO: Add command-line arguments
    parser.add_argument(
        '--stream-name',
        required=True,
        help='Name of the Kinesis stream'
    )
    parser.add_argument(
        '--count',
        type=int,
        default=100,
        help='Number of events to generate (default: 100)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for sending (default: 100)'
    )
    parser.add_argument(
        '--rate-limit',
        type=float,
        default=0.1,
        help='Delay between batches in seconds (default: 0.1)'
    )
    parser.add_argument(
        '--region',
        default='us-east-1',
        help='AWS region (default: us-east-1)'
    )

    args = parser.parse_args()

    # TODO: Create producer and send events
    try:
        producer = RideEventProducer(
            stream_name=args.stream_name,
            region=args.region
        )

        result = producer.generate_and_send(
            count=args.count,
            batch_size=args.batch_size,
            rate_limit=args.rate_limit
        )

        print("\n" + "="*50)
        print("Summary:")
        print(f"Total events: {result['total']}")
        print(f"Successfully sent: {result['success']}")
        print(f"Failed: {result['failed']}")
        print(f"Success rate: {(result['success']/result['total']*100):.1f}%")
        print("="*50)

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
