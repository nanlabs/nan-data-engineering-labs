"""
Rating Producer for Real-Time Analytics Platform.

Generates rating events after ride completions and sends them to AWS Kinesis.

Ratings include:
- rating_id: Unique rating identifier
- ride_id: Associated ride
- customer_id: Customer who gave rating
- driver_id: Driver being rated
- rating: 1-5 stars (weighted distribution, mean ~4.2)
- comment: Optional feedback text
- timestamp: When rating was given

Usage:
    python rating_producer.py --stream-name ratings_stream --rate 30 --duration 300
"""

import argparse
import logging
import sys
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
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


class RatingEventGenerator:
    """Generate realistic rating events with proper distribution."""

    # Realistic rating distribution (weighted towards positive)
    # Average rating: ~4.2 stars
    RATING_WEIGHTS = {
        1: 0.02,   # 2% - terrible experience
        2: 0.03,   # 3% - bad experience
        3: 0.10,   # 10% - okay experience
        4: 0.35,   # 35% - good experience
        5: 0.50,   # 50% - excellent experience
    }

    # Comments by rating level (templates)
    COMMENTS_BY_RATING = {
        5: [
            "Excellent driver! Very professional and friendly.",
            "Perfect ride, on time and clean car.",
            "Great experience, highly recommend!",
            "Fast, safe, and courteous driver.",
            "Amazing service, will request again.",
            "Best ride ever! Super friendly driver.",
            None,  # No comment
            None,
            None,
        ],
        4: [
            "Good ride overall, just minor issues.",
            "Nice driver, arrived on time.",
            "Pleasant experience.",
            "Good service, no complaints.",
            "Driver was friendly and helpful.",
            None,
            None,
            None,
        ],
        3: [
            "Ride was okay, nothing special.",
            "Driver could be more friendly.",
            "Car was not very clean.",
            "Took a longer route than expected.",
            "Average experience.",
            None,
            None,
        ],
        2: [
            "Driver was rude and unprofessional.",
            "Long wait time, poor service.",
            "Car was dirty and uncomfortable.",
            "Unsafe driving, felt concerned.",
            "Not satisfied with the service.",
            None,
        ],
        1: [
            "Terrible experience, driver was very rude.",
            "Unsafe driving, felt scared.",
            "Wrong route taken, much more expensive.",
            "Driver was on phone entire time.",
            "Worst ride ever, very unprofessional.",
            "Car smelled bad, very uncomfortable.",
        ],
    }

    # Rating categories (additional feedback)
    RATING_CATEGORIES = {
        'cleanliness': [1, 2, 3, 4, 5],
        'communication': [1, 2, 3, 4, 5],
        'driving_skill': [1, 2, 3, 4, 5],
        'route_efficiency': [1, 2, 3, 4, 5],
        'professionalism': [1, 2, 3, 4, 5],
    }

    def __init__(self, seed: int = None):
        """
        Initialize the rating event generator.

        Args:
            seed: Random seed for reproducibility
        """
        self.faker = Faker()
        if seed:
            Faker.seed(seed)
            random.seed(seed)
            np.random.seed(seed)

        # Pool of IDs
        self.customer_pool = [str(uuid.uuid4()) for _ in range(10000)]
        self.driver_pool = [str(uuid.uuid4()) for _ in range(5000)]

    def _select_rating(self) -> int:
        """Select a rating based on realistic distribution."""
        ratings = list(self.RATING_WEIGHTS.keys())
        weights = list(self.RATING_WEIGHTS.values())
        return np.random.choice(ratings, p=weights)

    def _generate_comment(self, rating: int) -> Optional[str]:
        """Generate a comment based on rating level."""
        # Lower ratings more likely to have comments (people complain more)
        comment_probability = {
            1: 0.90,  # 90% of 1-star ratings have comments
            2: 0.75,  # 75% of 2-star ratings
            3: 0.50,  # 50% of 3-star ratings
            4: 0.30,  # 30% of 4-star ratings
            5: 0.40,  # 40% of 5-star ratings (positive feedback)
        }

        if random.random() < comment_probability[rating]:
            comments = self.COMMENTS_BY_RATING[rating]
            comment = random.choice(comments)
            if comment:
                return comment

        return None

    def _generate_category_ratings(self, overall_rating: int) -> Dict[str, int]:
        """
        Generate detailed category ratings based on overall rating.

        Category ratings tend to be close to overall rating (±1 star).
        """
        category_ratings = {}

        for category in self.RATING_CATEGORIES.keys():
            # Category rating is usually within ±1 of overall
            variation = random.choice([-1, 0, 0, 0, 1])  # More likely to be same
            category_rating = overall_rating + variation

            # Clamp to 1-5 range
            category_rating = max(1, min(5, category_rating))

            category_ratings[category] = category_rating

        return category_ratings

    def _calculate_time_since_ride(self) -> int:
        """
        Calculate realistic time between ride completion and rating.

        Most ratings happen within minutes, but some take hours or days.
        """
        rand = random.random()

        if rand < 0.60:
            # 60% within 5 minutes
            return random.randint(60, 300)
        elif rand < 0.85:
            # 25% within 1 hour
            return random.randint(300, 3600)
        elif rand < 0.95:
            # 10% within 24 hours
            return random.randint(3600, 86400)
        else:
            # 5% after 1 day (late ratings)
            return random.randint(86400, 604800)  # Up to 1 week

    def generate_rating_event(self) -> Dict[str, Any]:
        """Generate a single rating event."""
        rating_id = str(uuid.uuid4())
        ride_id = str(uuid.uuid4())
        customer_id = random.choice(self.customer_pool)
        driver_id = random.choice(self.driver_pool)

        # Select rating
        rating = self._select_rating()

        # Generate comment
        comment = self._generate_comment(rating)

        # Generate category ratings
        category_ratings = self._generate_category_ratings(rating)

        # Calculate timestamp (rating given some time after ride)
        time_since_ride = self._calculate_time_since_ride()
        rated_at = datetime.utcnow() - timedelta(seconds=time_since_ride)

        # Base event
        event = {
            'rating_id': rating_id,
            'ride_id': ride_id,
            'customer_id': customer_id,
            'driver_id': driver_id,
            'rating': rating,
            'timestamp': rated_at.isoformat() + 'Z',
            'time_since_ride_seconds': time_since_ride,
        }

        # Add comment if exists
        if comment:
            event['comment'] = comment
            event['comment_length'] = len(comment)

        # Add category ratings
        event['category_ratings'] = category_ratings

        # Calculate average category rating
        event['avg_category_rating'] = round(
            sum(category_ratings.values()) / len(category_ratings), 2
        )

        # Add feedback flags
        event['is_positive'] = rating >= 4
        event['needs_review'] = rating <= 2  # Low ratings flagged for review

        # Add tips given (correlates with rating)
        if rating == 5:
            tip_probability = 0.60
        elif rating == 4:
            tip_probability = 0.30
        else:
            tip_probability = 0.05

        event['tip_given'] = random.random() < tip_probability

        if event['tip_given']:
            # Tip amount based on rating
            if rating == 5:
                tip_amount = random.uniform(3.0, 10.0)
            elif rating == 4:
                tip_amount = random.uniform(2.0, 5.0)
            else:
                tip_amount = random.uniform(1.0, 3.0)

            event['tip_amount'] = round(tip_amount, 2)

        return event


class RatingProducer:
    """Produce rating events to Kinesis stream."""

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
        self.generator = RatingEventGenerator()

        # Metrics
        self.total_sent = 0
        self.total_failed = 0
        self.ratings_by_star = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        self.total_rating_sum = 0
        self.ratings_with_comments = 0
        self.ratings_with_tips = 0

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
                    event = self.generator.generate_rating_event()
                    batch.append(event)

                    # Update metrics
                    self.ratings_by_star[event['rating']] += 1
                    self.total_rating_sum += event['rating']
                    if 'comment' in event:
                        self.ratings_with_comments += 1
                    if event.get('tip_given', False):
                        self.ratings_with_tips += 1

                # Send batch
                if batch:
                    result = batch_put_records(
                        self.kinesis_client,
                        self.stream_name,
                        batch,
                        partition_key_field='rating_id'
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
                    partition_key_field='rating_id'
                )
                self.total_sent += result['success']
                self.total_failed += result['failed']

            self._log_summary()

    def _publish_metrics(self, batch_size: int, result: Dict[str, int]):
        """Publish metrics to CloudWatch."""
        dimensions = [
            {'Name': 'StreamName', 'Value': self.stream_name},
            {'Name': 'Producer', 'Value': 'RatingProducer'}
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
        total_ratings = sum(self.ratings_by_star.values())
        avg_rating = self.total_rating_sum / total_ratings if total_ratings > 0 else 0

        logger.info("=" * 60)
        logger.info("PRODUCER SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total events sent: {self.total_sent}")
        logger.info(f"Total events failed: {self.total_failed}")
        if self.total_sent + self.total_failed > 0:
            logger.info(f"Success rate: {(self.total_sent / (self.total_sent + self.total_failed) * 100):.2f}%")
        logger.info(f"\nAverage rating: {avg_rating:.2f} stars")
        logger.info(f"Ratings with comments: {self.ratings_with_comments} "
                   f"({(self.ratings_with_comments / total_ratings * 100):.1f}%)")
        logger.info(f"Ratings with tips: {self.ratings_with_tips} "
                   f"({(self.ratings_with_tips / total_ratings * 100):.1f}%)")
        logger.info("\nRatings by star:")
        for star in sorted(self.ratings_by_star.keys()):
            count = self.ratings_by_star[star]
            percentage = (count / total_ratings * 100) if total_ratings > 0 else 0
            logger.info(f"  {star} stars: {count} ({percentage:.1f}%)")
        logger.info("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Produce rating events to Kinesis stream'
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
        producer = RatingProducer(
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
