"""
Driver Location Producer for Real-Time Analytics Platform.

Generates driver location updates showing realistic movement patterns
and sends them to AWS Kinesis in batches.

Updates include:
- driver_id: Unique driver identifier
- lat/lon: Current coordinates with realistic movement
- available: Whether driver is available for rides
- current_ride_id: If assigned to a ride
- speed_mph: Current speed
- heading: Direction of travel

Usage:
    python driver_location_producer.py --stream-name locations_stream --rate 500 --duration 300
"""

import argparse
import logging
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List
import random
import signal
import math

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


class Driver:
    """Represents a driver with state and movement."""

    def __init__(self, driver_id: str, city: str, start_lat: float, start_lon: float):
        """
        Initialize a driver.

        Args:
            driver_id: Unique driver identifier
            city: City name
            start_lat: Starting latitude
            start_lon: Starting longitude
        """
        self.driver_id = driver_id
        self.city = city
        self.lat = start_lat
        self.lon = start_lon
        self.available = random.choice([True, True, True, False])  # 75% available
        self.current_ride_id = None if self.available else str(uuid.uuid4())

        # Movement parameters
        self.speed_mph = random.uniform(0, 35) if not self.available else random.uniform(0, 15)
        self.heading = random.uniform(0, 360)  # Degrees

        # City boundaries (approximate)
        self.city_center = {'lat': start_lat, 'lon': start_lon}
        self.max_distance = 0.15  # Max distance from center (degrees, ~10 miles)

        # Last update time
        self.last_update = datetime.utcnow()

    def update_position(self, interval_seconds: float = 10.0):
        """
        Update driver position based on movement.

        Args:
            interval_seconds: Time since last update
        """
        if self.speed_mph > 0:
            # Calculate distance traveled
            # speed_mph * (interval_seconds / 3600) = distance in miles
            distance_miles = self.speed_mph * (interval_seconds / 3600.0)

            # Convert to degrees (approximately 69 miles per degree)
            distance_degrees = distance_miles / 69.0

            # Update position based on heading
            heading_rad = math.radians(self.heading)
            dlat = distance_degrees * math.cos(heading_rad)
            dlon = distance_degrees * math.sin(heading_rad)

            self.lat += dlat
            self.lon += dlon

            # Check if out of bounds, adjust heading
            dist_from_center = math.sqrt(
                (self.lat - self.city_center['lat'])**2 +
                (self.lon - self.city_center['lon'])**2
            )

            if dist_from_center > self.max_distance:
                # Turn towards center
                angle_to_center = math.degrees(math.atan2(
                    self.city_center['lon'] - self.lon,
                    self.city_center['lat'] - self.lat
                ))
                self.heading = angle_to_center + random.uniform(-45, 45)

        # Randomly adjust speed and heading
        if random.random() < 0.2:  # 20% chance to change
            if self.available:
                # Available drivers move slower
                self.speed_mph = random.uniform(0, 15)
            else:
                # Busy drivers move at traffic speeds
                self.speed_mph = random.uniform(15, 45)

        if random.random() < 0.3:  # 30% chance to change heading
            self.heading += random.uniform(-45, 45)
            self.heading = self.heading % 360

        # Randomly change availability status (simulate ride assignments)
        if random.random() < 0.05:  # 5% chance
            self.available = not self.available
            if not self.available:
                self.current_ride_id = str(uuid.uuid4())
                self.speed_mph = random.uniform(15, 45)
            else:
                self.current_ride_id = None
                self.speed_mph = random.uniform(0, 15)

        self.last_update = datetime.utcnow()

    def to_event(self) -> Dict[str, Any]:
        """Convert driver state to event dictionary."""
        event = {
            'driver_id': self.driver_id,
            'city': self.city,
            'lat': round(self.lat, 6),
            'lon': round(self.lon, 6),
            'available': self.available,
            'speed_mph': round(self.speed_mph, 1),
            'heading': round(self.heading, 1),
            'timestamp': self.last_update.isoformat() + 'Z',
        }

        if not self.available and self.current_ride_id:
            event['current_ride_id'] = self.current_ride_id

        return event


class DriverLocationGenerator:
    """Generate realistic driver location updates."""

    # Major cities with approximate coordinates
    CITIES = {
        'New York': {'lat': 40.7128, 'lon': -74.0060, 'drivers': 2000},
        'Los Angeles': {'lat': 34.0522, 'lon': -118.2437, 'drivers': 1800},
        'Chicago': {'lat': 41.8781, 'lon': -87.6298, 'drivers': 1200},
        'Houston': {'lat': 29.7604, 'lon': -95.3698, 'drivers': 800},
        'San Francisco': {'lat': 37.7749, 'lon': -122.4194, 'drivers': 1000},
        'Seattle': {'lat': 47.6062, 'lon': -122.3321, 'drivers': 600},
        'Boston': {'lat': 42.3601, 'lon': -71.0589, 'drivers': 500},
        'Miami': {'lat': 25.7617, 'lon': -80.1918, 'drivers': 600},
    }

    def __init__(self, num_drivers: int = None, seed: int = None):
        """
        Initialize the driver location generator.

        Args:
            num_drivers: Total number of drivers to simulate
            seed: Random seed for reproducibility
        """
        self.faker = Faker()
        if seed:
            Faker.seed(seed)
            random.seed(seed)
            np.random.seed(seed)

        # Determine number of drivers
        if num_drivers is None:
            num_drivers = sum(city['drivers'] for city in self.CITIES.values())

        # Initialize drivers across cities
        self.drivers: List[Driver] = []
        self._initialize_drivers(num_drivers)

        logger.info(f"Initialized {len(self.drivers)} drivers across {len(self.CITIES)} cities")

    def _initialize_drivers(self, num_drivers: int):
        """Initialize driver pool distributed across cities."""
        # Distribute drivers proportionally
        total_capacity = sum(city['drivers'] for city in self.CITIES.values())

        for city_name, city_data in self.CITIES.items():
            city_drivers = int((city_data['drivers'] / total_capacity) * num_drivers)

            for _ in range(city_drivers):
                # Random starting position within city
                start_lat = city_data['lat'] + random.uniform(-0.1, 0.1)
                start_lon = city_data['lon'] + random.uniform(-0.1, 0.1)

                driver = Driver(
                    driver_id=str(uuid.uuid4()),
                    city=city_name,
                    start_lat=start_lat,
                    start_lon=start_lon
                )
                self.drivers.append(driver)

    def generate_updates(self, interval_seconds: float = 10.0) -> List[Dict[str, Any]]:
        """
        Generate location updates for all drivers.

        Args:
            interval_seconds: Time since last update

        Returns:
            List of location update events
        """
        events = []

        for driver in self.drivers:
            driver.update_position(interval_seconds)
            events.append(driver.to_event())

        return events

    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics about driver fleet."""
        total = len(self.drivers)
        available = sum(1 for d in self.drivers if d.available)
        busy = total - available

        by_city = {}
        for city_name in self.CITIES:
            city_drivers = [d for d in self.drivers if d.city == city_name]
            by_city[city_name] = {
                'total': len(city_drivers),
                'available': sum(1 for d in city_drivers if d.available),
                'busy': sum(1 for d in city_drivers if not d.available),
            }

        return {
            'total_drivers': total,
            'available_drivers': available,
            'busy_drivers': busy,
            'availability_rate': round((available / total * 100), 2) if total > 0 else 0,
            'by_city': by_city,
        }


class DriverLocationProducer:
    """Produce driver location updates to Kinesis stream."""

    def __init__(
        self,
        stream_name: str,
        region: str,
        rate: int,
        update_interval: float = 10.0,
        namespace: str = 'RideShare/Producers'
    ):
        """
        Initialize the producer.

        Args:
            stream_name: Kinesis stream name
            region: AWS region
            rate: Target events per second
            update_interval: Driver update interval in seconds
            namespace: CloudWatch namespace for metrics
        """
        self.stream_name = stream_name
        self.region = region
        self.rate = rate
        self.update_interval = update_interval
        self.namespace = namespace

        # Initialize clients
        self.kinesis_client = get_kinesis_client(region)
        self.cloudwatch_client = get_cloudwatch_client(region)

        # Validate stream exists
        if not validate_stream_exists(self.kinesis_client, stream_name):
            raise KinesisProducerError(f"Stream {stream_name} is not available")

        # Calculate number of drivers needed to achieve target rate
        # If we want 'rate' events/sec and update every 'update_interval' seconds,
        # we need: rate * update_interval drivers
        num_drivers = int(rate * update_interval)

        # Initialize generator
        self.generator = DriverLocationGenerator(num_drivers=num_drivers)

        # Metrics
        self.total_sent = 0
        self.total_failed = 0
        self.update_count = 0

    def produce(self, duration_seconds: int = None):
        """
        Produce location updates to Kinesis.

        Args:
            duration_seconds: How long to produce events (None = indefinite)
        """
        logger.info(f"Starting producer: stream={self.stream_name}, "
                   f"rate={self.rate} events/sec, update_interval={self.update_interval}s")

        # Log initial stats
        stats = self.generator.get_stats()
        logger.info(f"Driver fleet: {stats['total_drivers']} total, "
                   f"{stats['available_drivers']} available, "
                   f"{stats['busy_drivers']} busy")

        start_time = time.time()

        try:
            while not shutdown_flag:
                # Check duration
                if duration_seconds and (time.time() - start_time) >= duration_seconds:
                    logger.info("Duration reached, stopping producer")
                    break

                update_start = time.time()

                # Generate updates for all drivers
                events = self.generator.generate_updates(self.update_interval)
                self.update_count += 1

                # Send in batches
                batch_size = 500
                for i in range(0, len(events), batch_size):
                    batch = events[i:i + batch_size]

                    result = batch_put_records(
                        self.kinesis_client,
                        self.stream_name,
                        batch,
                        partition_key_field='driver_id'
                    )

                    self.total_sent += result['success']
                    self.total_failed += result['failed']

                    # Publish metrics
                    self._publish_metrics(len(batch), result)

                # Log progress every 10 updates
                if self.update_count % 10 == 0:
                    stats = self.generator.get_stats()
                    logger.info(f"Update #{self.update_count}: Sent {len(events)} events. "
                              f"Total: {self.total_sent} sent, {self.total_failed} failed. "
                              f"Availability: {stats['availability_rate']}%")

                # Wait for next update interval
                update_duration = time.time() - update_start
                sleep_time = max(0, self.update_interval - update_duration)
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        except Exception as e:
            logger.error(f"Producer error: {e}", exc_info=True)
            raise
        finally:
            self._log_summary()

    def _publish_metrics(self, batch_size: int, result: Dict[str, int]):
        """Publish metrics to CloudWatch."""
        dimensions = [
            {'Name': 'StreamName', 'Value': self.stream_name},
            {'Name': 'Producer', 'Value': 'DriverLocationProducer'}
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

        # Publish availability metrics
        stats = self.generator.get_stats()
        publish_cloudwatch_metric(
            self.cloudwatch_client,
            self.namespace,
            'DriverAvailability',
            stats['availability_rate'],
            'Percent',
            dimensions
        )

    def _log_summary(self):
        """Log final summary."""
        stats = self.generator.get_stats()

        logger.info("=" * 60)
        logger.info("PRODUCER SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total events sent: {self.total_sent}")
        logger.info(f"Total events failed: {self.total_failed}")
        logger.info(f"Total updates: {self.update_count}")
        if self.total_sent + self.total_failed > 0:
            logger.info(f"Success rate: {(self.total_sent / (self.total_sent + self.total_failed) * 100):.2f}%")
        logger.info("\nDriver Fleet Stats:")
        logger.info(f"  Total drivers: {stats['total_drivers']}")
        logger.info(f"  Available: {stats['available_drivers']} ({stats['availability_rate']}%)")
        logger.info(f"  Busy: {stats['busy_drivers']}")
        logger.info("\nBy City:")
        for city, city_stats in stats['by_city'].items():
            logger.info(f"  {city}: {city_stats['total']} total, "
                       f"{city_stats['available']} available, {city_stats['busy']} busy")
        logger.info("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Produce driver location updates to Kinesis stream'
    )
    parser.add_argument(
        '--stream-name',
        required=True,
        help='Kinesis stream name'
    )
    parser.add_argument(
        '--rate',
        type=int,
        default=100,
        help='Target events per second (default: 100)'
    )
    parser.add_argument(
        '--update-interval',
        type=float,
        default=10.0,
        help='Driver update interval in seconds (default: 10.0)'
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
        producer = DriverLocationProducer(
            stream_name=args.stream_name,
            region=args.region,
            rate=args.rate,
            update_interval=args.update_interval,
            namespace=args.namespace
        )

        producer.produce(duration_seconds=args.duration)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
