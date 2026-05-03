"""
Stream Event Generator

Generates realistic streaming events for testing and learning.
Supports multiple event types: user events, sensor readings, transactions.
"""

import json
import random
import time
import uuid
from datetime import datetime
from typing import Dict, Any
import argparse

# Event type distributions
USER_EVENTS = ['PAGE_VIEW', 'CLICK', 'PURCHASE', 'ADD_TO_CART', 'SEARCH', 'LOGIN']
DEVICE_TYPES = ['DESKTOP', 'MOBILE', 'TABLET']
SENSOR_TYPES = ['TEMPERATURE', 'HUMIDITY', 'PRESSURE', 'MOTION']
TRANSACTION_TYPES = ['PURCHASE', 'REFUND', 'DEPOSIT', 'WITHDRAWAL']
PAYMENT_METHODS = ['CREDIT_CARD', 'DEBIT_CARD', 'BANK_TRANSFER', 'DIGITAL_WALLET']
COUNTRIES = ['US', 'UK', 'CA', 'DE', 'FR', 'JP', 'AU', 'BR']
CURRENCIES = {'US': 'USD', 'UK': 'GBP', 'DE': 'EUR', 'JP': 'JPY'}

class EventGenerator:
    def __init__(self, seed: int = None):
        if seed:
            random.seed(seed)

        self.user_ids = [f"user_{i:06d}" for i in range(1, 10001)]
        self.sensor_ids = [f"sensor_{i:04d}" for i in range(1, 501)]
        self.product_ids = [f"prod_{i:05d}" for i in range(1, 1001)]

    def generate_user_event(self) -> Dict[str, Any]:
        """Generate a user activity event"""
        event_type = random.choices(
            USER_EVENTS,
            weights=[40, 25, 10, 15, 8, 2],  # PAGE_VIEW most common
            k=1
        )[0]

        user_id = random.choice(self.user_ids)
        country = random.choice(COUNTRIES)

        event = {
            'event_id': str(uuid.uuid4()),
            'event_type': event_type,
            'timestamp': int(datetime.now().timestamp() * 1000),
            'user_id': user_id,
            'session_id': f"session_{random.randint(1, 100000)}",
            'country': country,
            'device_type': random.choice(DEVICE_TYPES),
        }

       # Event-specific fields
        if event_type in ['CLICK', 'PAGE_VIEW']:
            event['page_url'] = f"https://example.com/{random.choice(['home', 'products', 'about', 'contact'])}"

        if event_type in ['PURCHASE', 'ADD_TO_CART']:
            event['product_id'] = random.choice(self.product_ids)
            event['category'] = random.choice(['electronics', 'clothing', 'books', 'home'])

        if event_type == 'PURCHASE':
            event['amount'] = round(random.uniform(10, 500), 2)
            event['currency'] = CURRENCIES.get(country, 'USD')

        if event_type == 'SEARCH':
            event['search_query'] = random.choice(['laptop', 'phone', 'headphones', 'shoes'])

        return event

    def generate_sensor_reading(self) -> Dict[str, Any]:
        """Generate an IoT sensor reading"""
        sensor_type = random.choice(SENSOR_TYPES)

        # Realistic value ranges by sensor type
        value_ranges = {
            'TEMPERATURE': (15.0, 35.0, 'celsius'),
            'HUMIDITY': (20.0, 80.0, 'percent'),
            'PRESSURE': (980.0, 1020.0, 'hPa'),
            'MOTION': (0, 1, 'boolean')
        }

        min_val, max_val, unit = value_ranges[sensor_type]
        value = round(random.uniform(min_val, max_val), 2)

        reading = {
            'sensor_id': random.choice(self.sensor_ids),
            'device_id': f"device_{random.randint(1, 100):03d}",
            'timestamp': int(datetime.now().timestamp() * 1000),
            'sensor_type': sensor_type,
            'value': value,
            'unit': unit,
            'quality': random.choices(
                ['GOOD', 'FAIR', 'POOR'],
                weights=[85, 10, 5],
                k=1
            )[0],
            'battery_level': round(random.uniform(10, 100), 1)
        }

        # Add location for some sensors
        if random.random() < 0.3:
            reading['location'] = {
                'latitude': round(random.uniform(-90, 90), 6),
                'longitude': round(random.uniform(-180, 180), 6)
            }

        return reading

    def generate_transaction(self) -> Dict[str, Any]:
        """Generate a financial transaction"""
        txn_type = random.choice(TRANSACTION_TYPES)
        country = random.choice(COUNTRIES)

        transaction = {
            'transaction_id': f"txn_{uuid.uuid4().hex[:16]}",
            'timestamp': int(datetime.now().timestamp() * 1000),
            'user_id': random.choice(self.user_ids),
            'account_id': f"acc_{random.randint(100000, 999999)}",
            'transaction_type': txn_type,
            'amount': round(random.uniform(10, 1000), 2),
            'currency': CURRENCIES.get(country, 'USD'),
            'payment_method': random.choice(PAYMENT_METHODS),
            'status': random.choices(
                ['COMPLETED', 'PENDING', 'FAILED'],
                weights=[90, 8, 2],
                k=1
            )[0],
            'is_international': random.random() < 0.1
        }

        if txn_type == 'PURCHASE':
            transaction['merchant_id'] = f"merchant_{random.randint(1, 1000):04d}"
            transaction['merchant_name'] = random.choice(['Amazon', 'Walmart', 'Target', 'Best Buy'])
            transaction['merchant_category'] = random.choice(['retail', 'grocery', 'electronics'])

        # Risk score (higher for large international transactions)
        base_risk = 10
        if transaction['is_international']:
            base_risk += 20
        if transaction['amount'] > 500:
            base_risk += 15
        transaction['risk_score'] = min(base_risk + random.uniform(0, 20), 100)
        transaction['flagged_for_review'] = transaction['risk_score'] > 70

        if random.random() < 0.5:
            transaction['location'] = {
                'city': random.choice(['New York', 'London', 'Tokyo', 'Berlin']),
                'country': country
            }

        return transaction

def stream_events(
    event_type: str,
    rate: float,
    duration: int = None,
    output: str = 'stdout'
):
    """
    Stream events at specified rate

    Args:
        event_type: Type of events to generate (user, sensor, transaction)
        rate: Events per second
        duration: Duration in seconds (None for infinite)
        output: Output destination (stdout or filename)
    """
    generator = EventGenerator()

    event_generators = {
        'user': generator.generate_user_event,
        'sensor': generator.generate_sensor_reading,
        'transaction': generator.generate_transaction
    }

    if event_type not in event_generators:
        raise ValueError(f"Invalid event type: {event_type}")

    generate_fn = event_generators[event_type]

    # Output file if specified
    output_file = None
    if output != 'stdout':
        output_file = open(output, 'w')

    interval = 1.0 / rate  # Time between events
    start_time = time.time()
    events_generated = 0

    try:
        while True:
            # Generate event
            event = generate_fn()
            event_json = json.dumps(event)

            if output_file:
                output_file.write(event_json + '\n')
                output_file.flush()
            else:
                print(event_json)

            events_generated += 1

            # Check duration
            if duration and (time.time() - start_time) >= duration:
                break

            # Sleep to maintain rate
            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n Stopped. Generated {events_generated} events.")
    finally:
        if output_file:
            output_file.close()

def batch_generate(
    event_type: str,
    count: int,
    output: str
):
    """Generate batch of events and write to file"""
    generator = EventGenerator()

    event_generators = {
        'user': generator.generate_user_event,
        'sensor': generator.generate_sensor_reading,
        'transaction': generator.generate_transaction
    }

    generate_fn = event_generators[event_type]

    with open(output, 'w') as f:
        for i in range(count):
            event = generate_fn()
            f.write(json.dumps(event) + '\n')

            if (i + 1) % 1000 == 0:
                print(f"Generated {i + 1}/{count} events...")

    print(f"✅ Generated {count} events → {output}")

def main():
    parser = argparse.ArgumentParser(description='Generate streaming events')
    parser.add_argument('--type', choices=['user', 'sensor', 'transaction'],
                       required=True, help='Event type')
    parser.add_argument('--mode', choices=['stream', 'batch'], default='stream',
                       help='Generation mode')
    parser.add_argument('--rate', type=float, default=10.0,
                       help='Events per second (stream mode)')
    parser.add_argument('--duration', type=int, default=None,
                       help='Duration in seconds (stream mode)')
    parser.add_argument('--count', type=int, default=1000,
                       help='Number of events (batch mode)')
    parser.add_argument('--output', default='stdout',
                       help='Output file (default: stdout)')

    args = parser.parse_args()

    if args.mode == 'stream':
        print(f"🚀 Streaming {args.type} events at {args.rate} events/sec...")
        if args.duration:
            print(f"   Duration: {args.duration} seconds")
        stream_events(args.type, args.rate, args.duration, args.output)
    else:
        print(f"📦 Generating {args.count} {args.type} events...")
        batch_generate(args.type, args.count, args.output)

if __name__ == '__main__':
    main()
