"""
Payment Producer for Real-Time Analytics Platform.

Generates payment events after ride completions and sends them to AWS Kinesis.

Events include:
- payment_id: Unique payment identifier
- ride_id: Associated ride
- amount: Payment amount
- payment_method: credit_card, debit_card, wallet, cash
- status: pending, completed, failed
- Includes random failures (2%) for fraud detection testing

Usage:
    python payment_producer.py --stream-name payments_stream --rate 50 --duration 300
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


class PaymentEventGenerator:
    """Generate realistic payment events."""

    PAYMENT_METHODS = [
        ('credit_card', 0.50),  # 50%
        ('debit_card', 0.25),   # 25%
        ('wallet', 0.20),       # 20%
        ('cash', 0.05),         # 5%
    ]

    PAYMENT_STATUSES = [
        ('completed', 0.96),    # 96%
        ('failed', 0.02),       # 2%
        ('pending', 0.02),      # 2%
    ]

    # Card providers for realistic card numbers
    CARD_PROVIDERS = ['Visa', 'Mastercard', 'American Express', 'Discover']

    def __init__(self, seed: int = None):
        """
        Initialize the payment event generator.

        Args:
            seed: Random seed for reproducibility
        """
        self.faker = Faker()
        if seed:
            Faker.seed(seed)
            random.seed(seed)
            np.random.seed(seed)

        # Track payment attempts per customer (for fraud detection testing)
        self.customer_payment_attempts: Dict[str, List[Dict]] = {}

        # Pool of customer IDs
        self.customer_pool = [str(uuid.uuid4()) for _ in range(10000)]

    def _select_weighted(self, options: List[tuple]) -> str:
        """Select from weighted options."""
        choices, weights = zip(*options)
        return np.random.choice(choices, p=weights)

    def _generate_card_number(self, provider: str) -> str:
        """Generate a realistic-looking (but fake) card number."""
        if provider == 'Visa':
            prefix = '4'
            length = 16
        elif provider == 'Mastercard':
            prefix = '5'
            length = 16
        elif provider == 'American Express':
            prefix = '3'
            length = 15
        else:  # Discover
            prefix = '6'
            length = 16

        # Generate random digits
        number = prefix + ''.join([str(random.randint(0, 9)) for _ in range(length - 1)])

        # Mask all but last 4 digits
        return '*' * (length - 4) + number[-4:]

    def _should_simulate_fraud(self, customer_id: str, amount: float,
                              payment_method: str) -> bool:
        """
        Determine if this payment should be flagged as suspicious.

        Fraud indicators:
        - Amount > $500 (large transactions)
        - Multiple failed attempts from same customer
        - Rapid succession of payments
        """
        # Track attempt
        now = datetime.utcnow()
        if customer_id not in self.customer_payment_attempts:
            self.customer_payment_attempts[customer_id] = []

        self.customer_payment_attempts[customer_id].append({
            'timestamp': now,
            'amount': amount,
            'method': payment_method
        })

        # Clean old attempts (keep last hour)
        cutoff = now - timedelta(hours=1)
        self.customer_payment_attempts[customer_id] = [
            a for a in self.customer_payment_attempts[customer_id]
            if a['timestamp'] > cutoff
        ]

        attempts = self.customer_payment_attempts[customer_id]

        # Check fraud indicators
        if amount > 500:
            return random.random() < 0.15  # 15% chance for large amounts

        if len(attempts) > 5:
            # More than 5 attempts in an hour
            return random.random() < 0.25  # 25% chance

        if len(attempts) >= 3:
            # Check if 3+ attempts in last 5 minutes
            recent = [a for a in attempts if (now - a['timestamp']).seconds < 300]
            if len(recent) >= 3:
                return random.random() < 0.30  # 30% chance

        return False

    def generate_payment_event(self) -> Dict[str, Any]:
        """Generate a single payment event."""
        payment_id = str(uuid.uuid4())
        ride_id = str(uuid.uuid4())
        customer_id = random.choice(self.customer_pool)

        # Generate amount (based on typical ride fares)
        # Most rides: $10-50, some longer: $50-200, rare: $200-500
        rand = random.random()
        if rand < 0.80:
            amount = np.random.uniform(10, 50)
        elif rand < 0.95:
            amount = np.random.uniform(50, 200)
        else:
            amount = np.random.uniform(200, 500)

        amount = round(amount, 2)

        # Select payment method
        payment_method = self._select_weighted(self.PAYMENT_METHODS)

        # Determine if should simulate fraud
        is_suspicious = self._should_simulate_fraud(customer_id, amount, payment_method)

        # Select status (more likely to fail if suspicious)
        if is_suspicious:
            status = 'failed' if random.random() < 0.50 else 'completed'
        else:
            status = self._select_weighted(self.PAYMENT_STATUSES)

        # Base event
        event = {
            'payment_id': payment_id,
            'ride_id': ride_id,
            'customer_id': customer_id,
            'amount': amount,
            'payment_method': payment_method,
            'status': status,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'currency': 'USD',
        }

        # Add method-specific details
        if payment_method in ['credit_card', 'debit_card']:
            provider = random.choice(self.CARD_PROVIDERS)
            event['card_provider'] = provider
            event['card_last_4'] = self._generate_card_number(provider)[-4:]
            event['card_type'] = payment_method.replace('_', ' ').title()

        elif payment_method == 'wallet':
            event['wallet_provider'] = random.choice(['PayPal', 'Apple Pay', 'Google Pay', 'Venmo'])

        # Add failure details if failed
        if status == 'failed':
            failure_reasons = [
                'insufficient_funds',
                'card_declined',
                'invalid_card',
                'expired_card',
                'fraud_suspected',
                'network_error',
            ]

            if is_suspicious:
                # More likely to be fraud-related
                event['failure_reason'] = random.choice([
                    'fraud_suspected',
                    'card_declined',
                    'invalid_card'
                ])
            else:
                event['failure_reason'] = random.choice(failure_reasons)

            event['retry_count'] = random.randint(0, 3)

        # Add processing time
        processing_ms = random.randint(100, 3000)
        event['processing_time_ms'] = processing_ms

        # Add transaction fee (2.9% + $0.30 for cards, less for others)
        if payment_method in ['credit_card', 'debit_card']:
            event['transaction_fee'] = round(amount * 0.029 + 0.30, 2)
        elif payment_method == 'wallet':
            event['transaction_fee'] = round(amount * 0.025, 2)
        else:  # cash
            event['transaction_fee'] = 0.0

        # Add fraud score (0-100, higher = more suspicious)
        if is_suspicious or status == 'failed':
            event['fraud_score'] = random.randint(60, 95)
        else:
            event['fraud_score'] = random.randint(0, 40)

        return event


class PaymentProducer:
    """Produce payment events to Kinesis stream."""

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
        self.generator = PaymentEventGenerator()

        # Metrics
        self.total_sent = 0
        self.total_failed = 0
        self.events_by_status = {'completed': 0, 'failed': 0, 'pending': 0}
        self.events_by_method = {
            'credit_card': 0, 'debit_card': 0, 'wallet': 0, 'cash': 0
        }

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
                    event = self.generator.generate_payment_event()
                    batch.append(event)
                    self.events_by_status[event['status']] += 1
                    self.events_by_method[event['payment_method']] += 1

                # Send batch
                if batch:
                    result = batch_put_records(
                        self.kinesis_client,
                        self.stream_name,
                        batch,
                        partition_key_field='payment_id'
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
                    partition_key_field='payment_id'
                )
                self.total_sent += result['success']
                self.total_failed += result['failed']

            self._log_summary()

    def _publish_metrics(self, batch_size: int, result: Dict[str, int]):
        """Publish metrics to CloudWatch."""
        dimensions = [
            {'Name': 'StreamName', 'Value': self.stream_name},
            {'Name': 'Producer', 'Value': 'PaymentProducer'}
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
        if self.total_sent + self.total_failed > 0:
            logger.info(f"Success rate: {(self.total_sent / (self.total_sent + self.total_failed) * 100):.2f}%")
        logger.info("\nEvents by status:")
        for status, count in self.events_by_status.items():
            logger.info(f"  {status}: {count}")
        logger.info("\nEvents by payment method:")
        for method, count in self.events_by_method.items():
            logger.info(f"  {method}: {count}")
        logger.info("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Produce payment events to Kinesis stream'
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
        producer = PaymentProducer(
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
