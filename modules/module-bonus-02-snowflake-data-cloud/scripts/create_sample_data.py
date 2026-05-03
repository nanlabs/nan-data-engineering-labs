#!/usr/bin/env python3
"""
Sample Data Generator for Snowflake Training Exercises

This script generates realistic sample datasets for Snowflake exercises including:
- Customer data (CSV)
- Order data (CSV)
- Event data (JSON)

Usage:
    python create_sample_data.py --output-dir data/sample --num-customers 10000
    python create_sample_data.py --format json --num-orders 50000
"""

import argparse
import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import random

try:
    from faker import Faker
except ImportError:
    print("ERROR: Faker library not installed. Install with: pip install faker")
    sys.exit(1)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class SampleDataGenerator:
    """Generate realistic sample data for Snowflake training exercises."""

    def __init__(self, seed: int = 42):
        """
        Initialize the data generator.

        Args:
            seed: Random seed for reproducible data generation
        """
        self.fake = Faker()
        Faker.seed(seed)
        random.seed(seed)

        # Product catalog for orders
        self.products = [
            ("Laptop", 899.99, 1299.99),
            ("Smartphone", 499.99, 999.99),
            ("Tablet", 299.99, 799.99),
            ("Headphones", 49.99, 299.99),
            ("Smart Watch", 199.99, 499.99),
            ("Keyboard", 39.99, 149.99),
            ("Mouse", 19.99, 89.99),
            ("Monitor", 199.99, 899.99),
            ("Webcam", 49.99, 199.99),
            ("External Drive", 79.99, 299.99),
            ("USB Cable", 9.99, 29.99),
            ("Phone Case", 14.99, 49.99),
            ("Screen Protector", 9.99, 24.99),
            ("Charger", 19.99, 59.99),
            ("Speaker", 49.99, 399.99),
        ]

        # Event types for event data
        self.event_types = [
            "page_view",
            "button_click",
            "form_submit",
            "video_play",
            "video_pause",
            "item_add_to_cart",
            "item_remove_from_cart",
            "checkout_start",
            "checkout_complete",
            "search",
            "filter_apply",
            "login",
            "logout",
            "signup",
            "profile_update",
        ]

        # Countries for customers
        self.countries = [
            "United States", "Canada", "United Kingdom", "Germany", "France",
            "Spain", "Italy", "Netherlands", "Australia", "Japan",
            "Brazil", "Mexico", "India", "Singapore", "South Korea"
        ]

    def generate_customers(self, n: int = 10000) -> List[Dict]:
        """
        Generate customer data.

        Args:
            n: Number of customers to generate

        Returns:
            List of customer dictionaries
        """
        logger.info(f"Generating {n:,} customers...")
        customers = []

        for i in range(1, n + 1):
            # Generate signup date in the last 3 years
            signup_date = self.fake.date_between(
                start_date='-3y',
                end_date='today'
            )

            # Calculate total spent based on how long they've been a customer
            days_since_signup = (datetime.now().date() - signup_date).days
            avg_monthly_spend = random.uniform(0, 500)
            total_spent = round(avg_monthly_spend * (days_since_signup / 30), 2)

            customer = {
                'customer_id': i,
                'name': self.fake.name(),
                'email': self.fake.email(),
                'country': random.choice(self.countries),
                'signup_date': signup_date.strftime('%Y-%m-%d'),
                'total_spent': total_spent
            }
            customers.append(customer)

            if i % 1000 == 0:
                logger.info(f"  Generated {i:,} customers...")

        logger.info(f"✓ Successfully generated {len(customers):,} customers")
        return customers

    def generate_orders(self, n: int = 50000, num_customers: int = 10000) -> List[Dict]:
        """
        Generate order data.

        Args:
            n: Number of orders to generate
            num_customers: Maximum customer_id to reference

        Returns:
            List of order dictionaries
        """
        logger.info(f"Generating {n:,} orders for {num_customers:,} customers...")
        orders = []

        for i in range(1, n + 1):
            # Generate order date in the last 2 years
            order_date = self.fake.date_time_between(
                start_date='-2y',
                end_date='now'
            )

            # Select random product
            product_name, min_price, max_price = random.choice(self.products)
            price = round(random.uniform(min_price, max_price), 2)
            quantity = random.choices(
                [1, 2, 3, 4, 5],
                weights=[50, 25, 15, 7, 3],
                k=1
            )[0]

            order = {
                'order_id': i,
                'customer_id': random.randint(1, num_customers),
                'product': product_name,
                'quantity': quantity,
                'price': price,
                'order_date': order_date.strftime('%Y-%m-%d %H:%M:%S')
            }
            orders.append(order)

            if i % 5000 == 0:
                logger.info(f"  Generated {i:,} orders...")

        logger.info(f"✓ Successfully generated {len(orders):,} orders")
        return orders

    def generate_events(self, n: int = 100000, num_customers: int = 10000) -> List[Dict]:
        """
        Generate event data (JSON format).

        Args:
            n: Number of events to generate
            num_customers: Maximum user_id to reference

        Returns:
            List of event dictionaries
        """
        logger.info(f"Generating {n:,} events for {num_customers:,} users...")
        events = []

        for i in range(1, n + 1):
            # Generate timestamp in the last 90 days
            timestamp = self.fake.date_time_between(
                start_date='-90d',
                end_date='now'
            )

            event_type = random.choice(self.event_types)

            # Generate event-specific properties
            properties = self._generate_event_properties(event_type)

            event = {
                'event_id': i,
                'user_id': random.randint(1, num_customers),
                'event_type': event_type,
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'properties': properties
            }
            events.append(event)

            if i % 10000 == 0:
                logger.info(f"  Generated {i:,} events...")

        logger.info(f"✓ Successfully generated {len(events):,} events")
        return events

    def _generate_event_properties(self, event_type: str) -> Dict:
        """Generate event-specific properties based on event type."""
        properties = {
            'session_id': self.fake.uuid4(),
            'device': random.choice(['desktop', 'mobile', 'tablet']),
            'browser': random.choice(['Chrome', 'Firefox', 'Safari', 'Edge']),
        }

        if event_type == 'page_view':
            properties['page_url'] = self.fake.uri_path()
            properties['page_title'] = self.fake.sentence(nb_words=4)

        elif event_type in ['button_click', 'form_submit']:
            properties['element_id'] = f"{event_type.split('_')[0]}_{random.randint(1, 100)}"
            properties['element_text'] = self.fake.sentence(nb_words=3)

        elif event_type in ['video_play', 'video_pause']:
            properties['video_id'] = f"video_{random.randint(1, 500)}"
            properties['position'] = random.randint(0, 600)

        elif event_type in ['item_add_to_cart', 'item_remove_from_cart']:
            product_name, _, _ = random.choice(self.products)
            properties['product_name'] = product_name
            properties['product_id'] = f"prod_{random.randint(1, 1000)}"
            properties['quantity'] = random.randint(1, 5)

        elif event_type == 'search':
            properties['search_query'] = self.fake.sentence(nb_words=3)
            properties['results_count'] = random.randint(0, 100)

        elif event_type == 'filter_apply':
            properties['filter_type'] = random.choice(['category', 'price', 'brand', 'rating'])
            properties['filter_value'] = self.fake.word()

        return properties


def save_to_csv(data: List[Dict], filepath: Path) -> Tuple[int, int]:
    """
    Save data to CSV file.

    Args:
        data: List of dictionaries to save
        filepath: Path to output file

    Returns:
        Tuple of (record_count, file_size_bytes)
    """
    logger.info(f"Saving {len(data):,} records to {filepath}...")

    # Ensure directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Write CSV
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        if data:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

    file_size = filepath.stat().st_size
    logger.info(f"✓ Saved {len(data):,} records ({file_size:,} bytes)")

    return len(data), file_size


def save_to_json(data: List[Dict], filepath: Path) -> Tuple[int, int]:
    """
    Save data to JSON file (newline-delimited).

    Args:
        data: List of dictionaries to save
        filepath: Path to output file

    Returns:
        Tuple of (record_count, file_size_bytes)
    """
    logger.info(f"Saving {len(data):,} records to {filepath}...")

    # Ensure directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON (newline-delimited)
    with open(filepath, 'w', encoding='utf-8') as f:
        for record in data:
            f.write(json.dumps(record) + '\n')

    file_size = filepath.stat().st_size
    logger.info(f"✓ Saved {len(data):,} records ({file_size:,} bytes)")

    return len(data), file_size


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Generate sample data for Snowflake training exercises',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate default datasets
  python create_sample_data.py

  # Generate custom number of records
  python create_sample_data.py --num-customers 5000 --num-orders 25000

  # Generate JSON format only
  python create_sample_data.py --format json --output-dir /tmp/data

  # Specify custom output directory
  python create_sample_data.py --output-dir ../data/custom
        """
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/sample',
        help='Output directory for generated files (default: data/sample)'
    )
    parser.add_argument(
        '--num-customers',
        type=int,
        default=10000,
        help='Number of customers to generate (default: 10000)'
    )
    parser.add_argument(
        '--num-orders',
        type=int,
        default=50000,
        help='Number of orders to generate (default: 50000)'
    )
    parser.add_argument(
        '--num-events',
        type=int,
        default=100000,
        help='Number of events to generate (default: 100000)'
    )
    parser.add_argument(
        '--format',
        type=str,
        choices=['csv', 'json', 'both'],
        default='both',
        help='Output format (default: both)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducible data (default: 42)'
    )

    args = parser.parse_args()

    # Validate inputs
    if args.num_customers <= 0 or args.num_orders <= 0 or args.num_events <= 0:
        logger.error("Number of records must be positive integers")
        sys.exit(1)

    # Initialize generator
    generator = SampleDataGenerator(seed=args.seed)
    output_dir = Path(args.output_dir)

    logger.info("=" * 60)
    logger.info("Sample Data Generator for Snowflake Training")
    logger.info("=" * 60)
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Format: {args.format}")
    logger.info(f"Random seed: {args.seed}")
    logger.info("=" * 60)

    statistics = {
        'total_records': 0,
        'total_size': 0,
        'files': []
    }

    try:
        # Generate customers
        customers = generator.generate_customers(args.num_customers)

        if args.format in ['csv', 'both']:
            count, size = save_to_csv(
                customers,
                output_dir / 'customers.csv'
            )
            statistics['total_records'] += count
            statistics['total_size'] += size
            statistics['files'].append(('customers.csv', count, size))

        if args.format in ['json', 'both']:
            count, size = save_to_json(
                customers,
                output_dir / 'customers.json'
            )
            statistics['total_records'] += count
            statistics['total_size'] += size
            statistics['files'].append(('customers.json', count, size))

        # Generate orders
        orders = generator.generate_orders(args.num_orders, args.num_customers)

        if args.format in ['csv', 'both']:
            count, size = save_to_csv(
                orders,
                output_dir / 'orders.csv'
            )
            statistics['total_records'] += count
            statistics['total_size'] += size
            statistics['files'].append(('orders.csv', count, size))

        if args.format in ['json', 'both']:
            count, size = save_to_json(
                orders,
                output_dir / 'orders.json'
            )
            statistics['total_records'] += count
            statistics['total_size'] += size
            statistics['files'].append(('orders.json', count, size))

        # Generate events (always JSON)
        events = generator.generate_events(args.num_events, args.num_customers)
        count, size = save_to_json(
            events,
            output_dir / 'events.json'
        )
        statistics['total_records'] += count
        statistics['total_size'] += size
        statistics['files'].append(('events.json', count, size))

        # Print summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("GENERATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total records generated: {statistics['total_records']:,}")
        logger.info(f"Total size: {format_file_size(statistics['total_size'])}")
        logger.info("")
        logger.info("Files created:")
        for filename, count, size in statistics['files']:
            logger.info(f"  • {filename}: {count:,} records ({format_file_size(size)})")
        logger.info("=" * 60)
        logger.info("✓ Data generation completed successfully!")
        logger.info(f"✓ Files saved to: {output_dir.absolute()}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error during data generation: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
