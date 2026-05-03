"""
Ride Event Producer for Real-Time Analytics Platform.

Generates realistic ride events (ride_requested, ride_started, ride_completed)
and sends them to AWS Kinesis in batches.

Events include:
- ride_requested: New ride request with pickup location
- ride_started: Driver assigned and ride started
- ride_completed: Ride finished with dropoff location and fare

Usage:
    python ride_event_producer.py --stream-name rides_stream --rate 100 --duration 300
"""

import argparse
import logging
import sys
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List
import random
import signal

from faker import Faker
import numpy as np

# Import common utilities
from common.kinesis_utils import (
    get_kinesis_client,
    get_cloudwatch_client,
    batch_put_records,
    publish_cloudwatch_metric,
    validate_stream_exists,
    KinesisProducerError
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_flag = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_flag
    logger.info("Shutdown signal received, finishing current batch...")
    shutdown_flag = True


class RideEventGenerator:
    """Generate realistic ride events with proper state transitions."""

    # Major cities with approximate coordinates
    CITIES = {
        'New York': {'lat': 40.7128, 'lon': -74.0060, 'spread': 0.2},
        'Los Angeles': {'lat': 34.0522, 'lon': -118.2437, 'spread': 0.3},
        'Chicago': {'lat': 41.8781, 'lon': -87.6298, 'spread': 0.15},
        'Houston': {'lat': 29.7604, 'lon': -95.3698, 'spread': 0.2},
        'San Francisco': {'lat': 37.7749, 'lon': -122.4194, 'spread': 0.1},
        'Seattle': {'lat': 47.6062, 'lon': -122.3321, 'spread': 0.12},
        'Boston': {'lat': 42.3601, 'lon': -71.0589, 'spread': 0.1},
        'Miami': {'lat': 25.7617, 'lon': -80.1918, 'spread': 0.15},
    }

    RIDE_STATUSES = ['requested', 'started', 'completed']

    def __init__(self, seed: int = None):
        """
        Initialize the ride event generator.

        Args:
            seed: Random seed for reproducibility
        """
        self.faker = Faker()
        if seed:
            Faker.seed(seed)
            random.seed(seed)
            np.random.seed(seed)

        # Track active rides for state transitions
        self.active_rides: Dict[str, Dict[str, Any]] = {}
        self.pending_rides: List[str] = []  # Rides waiting to be started
        self.in_progress_rides: List[str] = []  # Rides waiting to be completed

        # Pools of IDs
        self.customer_pool = [str(uuid.uuid4()) for _ in range(10000)]
        self.driver_pool = [str(uuid.uuid4()) for _ in range(5000)]

    def _generate_coordinates(self, city_name: str) -> Dict[str, float]:
        """Generate coordinates within a city."""
        city = self.CITIES[city_name]
        lat = city['lat'] + np.random.uniform(-city['spread'], city['spread'])
        lon = city['lon'] + np.random.uniform(-city['spread'], city['spread'])
        return {'lat': round(lat, 6), 'lon': round(lon, 6)}

    def _calculate_distance(self, coord1: Dict, coord2: Dict) -> float:
        """Calculate approximate distance in miles using Haversine formula."""
        from math import radians, cos, sin, asin, sqrt

        lat1, lon1 = radians(coord1['lat']), radians(coord1['lon'])
        lat2, lon2 = radians(coord2['lat']), radians(coord2['lon'])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        miles = 3956 * c  # Earth radius in miles

        return round(miles, 2)

    def _calculate_fare(self, distance_miles: float) -> float:
        """Calculate estimated fare based on distance and surge."""
        base_fare = 2.50
        per_mile = 1.75
        per_minute = 0.35

        # Estimate duration (assuming 30 mph average)
        duration_minutes = (distance_miles / 30) * 60

        fare = base_fare + (distance_miles * per_mile) + (duration_minutes * per_minute)

        # Add random surge (10% of rides have 1.2-2.0x surge)
        if random.random() < 0.1:
            surge = random.uniform(1.2, 2.0)
            fare *= surge

        return round(fare, 2)

    def generate_ride_requested(self) -> Dict[str, Any]:
        """Generate a ride_requested event."""
        ride_id = str(uuid.uuid4())
        city_name = random.choice(list(self.CITIES.keys()))
        pickup = self._generate_coordinates(city_name)

        # Generate dropoff 1-20 miles away
        distance_miles = random.uniform(1.0, 20.0)
        angle = random.uniform(0, 2 * np.pi)
        # Approximate: 1 degree ≈ 69 miles
        dlat = (distance_miles / 69) * np.cos(angle)
        dlon = (distance_miles / 69) * np.sin(angle)

        dropoff = {
            'lat': round(pickup['lat'] + dlat, 6),
            'lon': round(pickup['lon'] + dlon, 6)
        }

        actual_distance = self._calculate_distance(pickup, dropoff)
        estimated_fare = self._calculate_fare(actual_distance)

        event = {
            'ride_id': ride_id,
            'event_type': 'ride_requested',
            'customer_id': random.choice(self.customer_pool),
            'city': city_name,
            'pickup_lat': pickup['lat'],
            'pickup_lon': pickup['lon'],
            'dropoff_lat': dropoff['lat'],
            'dropoff_lon': dropoff['lon'],
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'status': 'requested',
            'estimated_fare': estimated_fare,
            'estimated_distance_miles': actual_distance,
            'estimated_duration_minutes': round((actual_distance / 30) * 60, 1),
        }

        # Track ride for state transitions
        self.active_rides[ride_id] = {
            'city': city_name,
            'pickup': pickup,
            'dropoff': dropoff,
            'customer_id': event['customer_id'],
            'estimated_fare': estimated_fare,
            'distance_miles': actual_distance,
            'requested_at': datetime.utcnow()
        }
        self.pending_rides.append(ride_id)

        return event

    def generate_ride_started(self) -> Dict[str, Any]:
        """Generate a ride_started event for a pending ride."""
        if not self.pending_rides:
            return None

        ride_id = self.pending_rides.pop(0)
        ride_data = self.active_rides[ride_id]

        # Assign driver (1-5 minute wait time)
        wait_minutes = random.uniform(1, 5)
        started_at = ride_data['requested_at'] + timedelta(minutes=wait_minutes)

        event = {
            'ride_id': ride_id,
            'event_type': 'ride_started',
            'customer_id': ride_data['customer_id'],
            'driver_id': random.choice(self.driver_pool),
            'city': ride_data['city'],
            'pickup_lat': ride_data['pickup']['lat'],
            'pickup_lon': ride_data['pickup']['lon'],
            'timestamp': started_at.isoformat() + 'Z',
            'status': 'started',
            'wait_time_minutes': round(wait_minutes, 1),
        }

        # Update ride tracking
        ride_data['driver_id'] = event['driver_id']
        ride_data['started_at'] = started_at
        self.in_progress_rides.append(ride_id)

        return event

    def generate_ride_completed(self) -> Dict[str, Any]:
        """Generate a ride_completed event for an in-progress ride."""
        if not self.in_progress_rides:
            return None

        ride_id = self.in_progress_rides.pop(0)
        ride_data = self.active_rides[ride_id]

        # Calculate actual duration (80-120% of estimated)
        estimated_duration = (ride_data['distance_miles'] / 30) * 60
        actual_duration = estimated_duration * random.uniform(0.8, 1.2)

        completed_at = ride_data['started_at'] + timedelta(minutes=actual_duration)

        # Calculate actual fare (usually close to estimate, ±20%)
        actual_fare = ride_data['estimated_fare'] * random.uniform(0.85, 1.15)

        event = {
            'ride_id': ride_id,
            'event_type': 'ride_completed',
            'customer_id': ride_data['customer_id'],
            'driver_id': ride_data['driver_id'],
            'city': ride_data['city'],
            'pickup_lat': ride_data['pickup']['lat'],
            'pickup_lon': ride_data['pickup']['lon'],
            'dropoff_lat': ride_data['dropoff']['lat'],
            'dropoff_lon': ride_data['dropoff']['lon'],
            'timestamp': completed_at.isoformat() + 'Z',
            'status': 'completed',
            'actual_fare': round(actual_fare, 2),
            'actual_distance_miles': ride_data['distance_miles'],
            'actual_duration_minutes': round(actual_duration, 1),
            'tip_amount': round(actual_fare * random.choice([0, 0, 0.10, 0.15, 0.20]), 2),
        }

        # Remove from active rides
        del self.active_rides[ride_id]

        return event

    def generate_event(self) -> Dict[str, Any]:
        """
        Generate the next ride event with realistic state transitions.

        Priority:
        1. Complete some in-progress rides (30% chance if available)
        2. Start some pending rides (40% chance if available)
        3. Create new ride requests (always)
        """
        # Decide which event type to generate
        rand = random.random()

        # 30% chance to complete a ride if available
        if self.in_progress_rides and rand < 0.3:
            event = self.generate_ride_completed()
            if event:
                return event

        # 40% chance to start a ride if available
        if self.pending_rides and rand < 0.7:
            event = self.generate_ride_started()
            if event:
                return event

        # Otherwise create new request
        return self.generate_ride_requested()


class RideEventProducer:
    """Produce ride events to Kinesis stream."""

    def __init__(
        self,
        stream_name: str,
        region: str,
        rate: int,
        namespace: str = 'RideShare/Producers'
    ):
        """
        Initialize the producer.

        Args:
            stream_name: Kinesis stream name
            region: AWS region
            rate: Target events per second
            namespace: CloudWatch namespace for metrics
        """
        self.stream_name = stream_name
        self.region = region
        self.rate = rate
        self.namespace = namespace

        # Initialize clients
        self.kinesis_client = get_kinesis_client(region)
        self.cloudwatch_client = get_cloudwatch_client(region)

        # Validate stream exists
        if not validate_stream_exists(self.kinesis_client, stream_name):
            raise KinesisProducerError(f"Stream {stream_name} is not available")

        # Initialize generator
        self.generator = RideEventGenerator()

        # Metrics
        self.total_sent = 0
        self.total_failed = 0
        self.events_by_type = {'ride_requested': 0, 'ride_started': 0, 'ride_completed': 0}

    def produce(self, duration_seconds: int = None):
        """
        Produce events to Kinesis.

        Args:
            duration_seconds: How long to produce events (None = indefinite)
        """
        logger.info(f"Starting producer: stream={self.stream_name}, "
                   f"rate={self.rate} events/sec, duration={duration_seconds}s")

        start_time = time.time()
        batch = []
        batch_size = 500  # Kinesis limit

        # Calculate delay between batches
        events_per_batch = min(batch_size, self.rate)
        batch_delay = events_per_batch / self.rate if self.rate > 0 else 1

        try:
            while not shutdown_flag:
                # Check duration
                if duration_seconds and (time.time() - start_time) >= duration_seconds:
                    logger.info("Duration reached, stopping producer")
                    break

                batch_start = time.time()

                # Generate batch of events
                for _ in range(events_per_batch):
                    event = self.generator.generate_event()
                    if event:
                        batch.append(event)
                        self.events_by_type[event['event_type']] += 1

                # Send batch
                if batch:
                    result = batch_put_records(
                        self.kinesis_client,
                        self.stream_name,
                        batch,
                        partition_key_field='ride_id'
                    )

                    self.total_sent += result['success']
                    self.total_failed += result['failed']

                    # Publish metrics
                    self._publish_metrics(len(batch), result)

                    logger.info(f"Sent batch: {result['success']} succeeded, "
                              f"{result['failed']} failed. "
                              f"Total: {self.total_sent} sent, {self.total_failed} failed")

                    batch = []

                # Rate limiting
                batch_duration = time.time() - batch_start
                sleep_time = max(0, batch_delay - batch_duration)
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        except Exception as e:
            logger.error(f"Producer error: {e}", exc_info=True)
            raise
        finally:
            # Send remaining events
            if batch:
                logger.info(f"Sending final batch of {len(batch)} events")
                result = batch_put_records(
                    self.kinesis_client,
                    self.stream_name,
                    batch,
                    partition_key_field='ride_id'
                )
                self.total_sent += result['success']
                self.total_failed += result['failed']

            self._log_summary()

    def _publish_metrics(self, batch_size: int, result: Dict[str, int]):
        """Publish metrics to CloudWatch."""
        dimensions = [
            {'Name': 'StreamName', 'Value': self.stream_name},
            {'Name': 'Producer', 'Value': 'RideEventProducer'}
        ]

        publish_cloudwatch_metric(
            self.cloudwatch_client,
            self.namespace,
            'RecordsSent',
            result['success'],
            'Count',
            dimensions
        )

        if result['failed'] > 0:
            publish_cloudwatch_metric(
                self.cloudwatch_client,
                self.namespace,
                'RecordsFailed',
                result['failed'],
                'Count',
                dimensions
            )

    def _log_summary(self):
        """Log final summary."""
        logger.info("=" * 60)
        logger.info("PRODUCER SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total events sent: {self.total_sent}")
        logger.info(f"Total events failed: {self.total_failed}")
        logger.info(f"Success rate: {(self.total_sent / (self.total_sent + self.total_failed) * 100):.2f}%")
        logger.info("Events by type:")
        for event_type, count in self.events_by_type.items():
            logger.info(f"  {event_type}: {count}")
        logger.info("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Produce ride events to Kinesis stream'
    )
    parser.add_argument(
        '--stream-name',
        required=True,
        help='Kinesis stream name'
    )
    parser.add_argument(
        '--rate',
        type=int,
        default=10,
        help='Target events per second (default: 10)'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=None,
        help='Duration in seconds (default: run indefinitely)'
    )
    parser.add_argument(
        '--region',
        default='us-east-1',
        help='AWS region (default: us-east-1)'
    )
    parser.add_argument(
        '--namespace',
        default='RideShare/Producers',
        help='CloudWatch namespace (default: RideShare/Producers)'
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )

    args = parser.parse_args()

    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        producer = RideEventProducer(
            stream_name=args.stream_name,
            region=args.region,
            rate=args.rate,
            namespace=args.namespace
        )

        producer.produce(duration_seconds=args.duration)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
