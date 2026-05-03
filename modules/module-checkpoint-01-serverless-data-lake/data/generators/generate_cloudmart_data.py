#!/usr/bin/env python3
"""
CloudMart Data Generator
========================
Generates realistic e-commerce data for the CloudMart Data Lake project.

This script generates:
- Customer data with demographic information
- Product catalog with categories and pricing
- Order transactions with seasonality patterns
- User behavior events (clickstream data)

Output formats: CSV, JSON, Parquet
"""

import argparse
import json
import random
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from faker import Faker

# Initialize Faker for realistic data generation
fake = Faker()
Faker.seed(42)
random.seed(42)


class CloudMartDataGenerator:
    """Main data generator for CloudMart e-commerce platform."""

    def __init__(self, seed: int = 42):
        """Initialize the data generator with a random seed."""
        self.seed = seed
        Faker.seed(seed)
        random.seed(seed)
        self.fake = Faker()

        # Configuration
        self.countries = ['US', 'UK', 'DE', 'FR', 'CA', 'AU']
        self.categories = ['Electronics', 'Clothing', 'Books', 'Home', 'Food']
        self.segments = ['Premium', 'Standard', 'Basic']
        self.statuses = ['completed', 'pending', 'cancelled']
        self.event_types = ['page_view', 'add_to_cart', 'purchase', 'logout']

        # Segment weights for customer distribution
        self.segment_weights = {
            'Premium': 0.15,
            'Standard': 0.50,
            'Basic': 0.35
        }

        # Status weights for orders
        self.status_weights = {
            'completed': 0.85,
            'pending': 0.10,
            'cancelled': 0.05
        }

    def generate_customers(self, n: int = 50000) -> pd.DataFrame:
        """
        Generate customer data.

        Args:
            n: Number of customers to generate

        Returns:
            DataFrame with customer data
        """
        print(f"Generating {n:,} customers...")

        customers = []
        for i in range(n):
            # Assign segment based on weights
            segment = random.choices(
                list(self.segment_weights.keys()),
                weights=list(self.segment_weights.values())
            )[0]

            # Generate signup date (last 2 years)
            signup_date = self.fake.date_between(
                start_date='-2y',
                end_date='today'
            )

            customer = {
                'customer_id': f'CUST{str(i+1).zfill(8)}',
                'name': self.fake.name(),
                'email': self.fake.email(),
                'country': random.choice(self.countries),
                'city': self.fake.city(),
                'signup_date': signup_date.isoformat(),
                'segment': segment
            }
            customers.append(customer)

            if (i + 1) % 10000 == 0:
                print(f"  Generated {i+1:,} customers...")

        df = pd.DataFrame(customers)
        print(f"✓ Generated {len(df):,} customers")
        return df

    def generate_products(self, n: int = 5000) -> pd.DataFrame:
        """
        Generate product catalog data.

        Args:
            n: Number of products to generate

        Returns:
            DataFrame with product data
        """
        print(f"Generating {n:,} products...")

        products = []
        for i in range(n):
            category = random.choice(self.categories)

            # Category-specific price ranges
            price_ranges = {
                'Electronics': (50, 1000),
                'Clothing': (10, 200),
                'Books': (10, 50),
                'Home': (20, 500),
                'Food': (5, 100)
            }

            min_price, max_price = price_ranges[category]
            price = round(random.uniform(min_price, max_price), 2)

            product = {
                'product_id': f'PROD{str(i+1).zfill(6)}',
                'name': self._generate_product_name(category),
                'category': category,
                'price': price,
                'stock_quantity': random.randint(0, 500)
            }
            products.append(product)

            if (i + 1) % 1000 == 0:
                print(f"  Generated {i+1:,} products...")

        df = pd.DataFrame(products)
        print(f"✓ Generated {len(df):,} products")
        return df

    def generate_orders(
        self,
        customers_df: pd.DataFrame,
        products_df: pd.DataFrame,
        n: int = 200000
    ) -> pd.DataFrame:
        """
        Generate order transaction data.

        Args:
            customers_df: DataFrame with customer data
            products_df: DataFrame with product data
            n: Number of orders to generate

        Returns:
            DataFrame with order data
        """
        print(f"Generating {n:,} orders...")

        orders = []
        customer_ids = customers_df['customer_id'].tolist()
        customer_segments = dict(zip(
            customers_df['customer_id'],
            customers_df['segment']
        ))

        # Date range: last year
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        for i in range(n):
            # Select customer with segment-based order frequency
            customer_id = self._select_customer_weighted(
                customer_ids,
                customer_segments
            )

            # Generate order date with seasonality
            order_date = self._generate_order_date_with_seasonality(
                start_date,
                end_date
            )

            # Select 1-5 products
            num_products = random.choices(
                [1, 2, 3, 4, 5],
                weights=[0.4, 0.3, 0.15, 0.10, 0.05]
            )[0]

            selected_products = random.sample(
                products_df.to_dict('records'),
                num_products
            )

            # Calculate total amount
            total_amount = sum(p['price'] for p in selected_products)

            # Segment-based discount
            segment = customer_segments[customer_id]
            if segment == 'Premium':
                total_amount *= 0.90  # 10% discount
            elif segment == 'Standard':
                total_amount *= 0.95  # 5% discount

            # Assign status
            status = random.choices(
                list(self.status_weights.keys()),
                weights=list(self.status_weights.values())
            )[0]

            order = {
                'order_id': str(uuid.uuid4()),
                'customer_id': customer_id,
                'order_date': order_date.date().isoformat(),
                'order_timestamp': order_date.isoformat(),
                'total_amount': round(total_amount, 2),
                'status': status,
                'products': json.dumps([p['product_id'] for p in selected_products]),
                'product_count': num_products
            }
            orders.append(order)

            if (i + 1) % 20000 == 0:
                print(f"  Generated {i+1:,} orders...")

        df = pd.DataFrame(orders)
        print(f"✓ Generated {len(df):,} orders")
        return df

    def generate_events(
        self,
        customers_df: pd.DataFrame,
        n: int = 1000000
    ) -> pd.DataFrame:
        """
        Generate clickstream event data.

        Args:
            customers_df: DataFrame with customer data
            n: Number of events to generate

        Returns:
            DataFrame with event data
        """
        print(f"Generating {n:,} events...")

        events = []
        customer_ids = customers_df['customer_id'].tolist()

        # Date range: last 30 days
        end_datetime = datetime.now()
        start_datetime = end_datetime - timedelta(days=30)

        for i in range(n):
            user_id = random.choice(customer_ids)
            event_type = random.choices(
                self.event_types,
                weights=[0.60, 0.20, 0.15, 0.05]
            )[0]

            # Generate timestamp
            event_timestamp = self._random_datetime(start_datetime, end_datetime)

            # Generate event properties based on type
            properties = self._generate_event_properties(event_type)

            event = {
                'event_id': str(uuid.uuid4()),
                'user_id': user_id,
                'event_type': event_type,
                'event_timestamp': event_timestamp.isoformat(),
                'properties': json.dumps(properties)
            }
            events.append(event)

            if (i + 1) % 100000 == 0:
                print(f"  Generated {i+1:,} events...")

        df = pd.DataFrame(events)
        print(f"✓ Generated {len(df):,} events")
        return df

    def _generate_product_name(self, category: str) -> str:
        """Generate realistic product names based on category."""
        prefixes = {
            'Electronics': ['Smart', 'Wireless', 'Digital', 'HD', 'Premium'],
            'Clothing': ['Classic', 'Modern', 'Vintage', 'Designer', 'Casual'],
            'Books': ['The', 'Complete', 'Essential', 'Ultimate', 'Comprehensive'],
            'Home': ['Deluxe', 'Comfort', 'Modern', 'Elegant', 'Classic'],
            'Food': ['Organic', 'Fresh', 'Premium', 'Gourmet', 'Natural']
        }

        items = {
            'Electronics': ['Headphones', 'Speaker', 'Camera', 'Tablet', 'Watch'],
            'Clothing': ['Shirt', 'Jeans', 'Jacket', 'Dress', 'Shoes'],
            'Books': ['Guide', 'Novel', 'Cookbook', 'Biography', 'Collection'],
            'Home': ['Chair', 'Lamp', 'Table', 'Cushion', 'Rug'],
            'Food': ['Coffee', 'Tea', 'Snacks', 'Nuts', 'Chocolate']
        }

        prefix = random.choice(prefixes[category])
        item = random.choice(items[category])

        return f"{prefix} {item}"

    def _select_customer_weighted(
        self,
        customer_ids: List[str],
        customer_segments: Dict[str, str]
    ) -> str:
        """Select a customer with segment-based weighting (Premium customers order more)."""
        # Premium customers are 3x more likely to order
        # Standard customers are 2x more likely
        # Basic customers have base probability
        while True:
            customer_id = random.choice(customer_ids)
            segment = customer_segments[customer_id]

            weight = {'Premium': 3, 'Standard': 2, 'Basic': 1}[segment]
            if random.random() < weight / 3:
                return customer_id

    def _generate_order_date_with_seasonality(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> datetime:
        """Generate order date with seasonal patterns (higher in Nov-Dec)."""
        # Generate random date
        time_between = end_date - start_date
        days_between = time_between.days
        random_days = random.randint(0, days_between)
        order_date = start_date + timedelta(days=random_days)

        # Apply seasonality boost for Nov-Dec
        month = order_date.month
        if month in [11, 12]:
            # Higher probability of orders in holiday season
            if random.random() < 0.3:  # 30% chance to regenerate
                return self._generate_order_date_with_seasonality(
                    start_date,
                    end_date
                )

        # Add time component
        hour = random.choices(
            range(24),
            weights=[2 if h < 6 else 8 if 9 <= h <= 21 else 4 for h in range(24)]
        )[0]
        minute = random.randint(0, 59)
        second = random.randint(0, 59)

        return order_date.replace(hour=hour, minute=minute, second=second)

    def _random_datetime(
        self,
        start: datetime,
        end: datetime
    ) -> datetime:
        """Generate random datetime between start and end."""
        delta = end - start
        random_seconds = random.randint(0, int(delta.total_seconds()))
        return start + timedelta(seconds=random_seconds)

    def _generate_event_properties(self, event_type: str) -> Dict[str, Any]:
        """Generate event-specific properties."""
        if event_type == 'page_view':
            return {
                'page': random.choice([
                    'home', 'products', 'category', 'product_detail', 'cart'
                ]),
                'referrer': random.choice(['google', 'direct', 'facebook', 'email']),
                'device': random.choice(['desktop', 'mobile', 'tablet'])
            }
        elif event_type == 'add_to_cart':
            return {
                'product_id': f'PROD{random.randint(1, 5000):06d}',
                'quantity': random.randint(1, 3),
                'price': round(random.uniform(10, 500), 2)
            }
        elif event_type == 'purchase':
            return {
                'order_id': str(uuid.uuid4()),
                'total': round(random.uniform(20, 1000), 2),
                'items': random.randint(1, 5)
            }
        else:  # logout
            return {
                'session_duration': random.randint(60, 3600),
                'pages_viewed': random.randint(1, 20)
            }


def save_dataframes(
    dataframes: Dict[str, pd.DataFrame],
    output_dir: Path,
    output_format: str = 'csv'
):
    """
    Save generated dataframes to files.

    Args:
        dataframes: Dictionary mapping names to DataFrames
        output_dir: Output directory path
        output_format: Output format (csv, json, or parquet)
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nSaving data to {output_dir} in {output_format.upper()} format...")

    for name, df in dataframes.items():
        file_path = output_dir / f"{name}.{output_format}"

        if output_format == 'csv':
            df.to_csv(file_path, index=False)
        elif output_format == 'json':
            df.to_json(file_path, orient='records', lines=True)
        elif output_format == 'parquet':
            df.to_parquet(file_path, index=False, compression='snappy')
        else:
            raise ValueError(f"Unsupported format: {output_format}")

        file_size = file_path.stat().st_size / (1024 * 1024)  # MB
        print(f"  ✓ Saved {name}.{output_format} ({file_size:.2f} MB)")


def add_ingestion_timestamps(
    dataframes: Dict[str, pd.DataFrame]
) -> Dict[str, pd.DataFrame]:
    """Add ingestion timestamp to all dataframes."""
    ingestion_time = datetime.now().isoformat()

    for name, df in dataframes.items():
        df['ingestion_timestamp'] = ingestion_time

    return dataframes


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Generate CloudMart e-commerce data for data lake',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate default dataset
  python generate_cloudmart_data.py

  # Generate larger dataset in Parquet format
  python generate_cloudmart_data.py --num-customers 100000 --num-orders 500000 --format parquet

  # Generate with specific seed for reproducibility
  python generate_cloudmart_data.py --seed 12345 --output-dir ./my-data

  # Generate minimal dataset for testing
  python generate_cloudmart_data.py --num-customers 1000 --num-orders 5000 --num-events 10000
        """
    )

    parser.add_argument(
        '--num-customers',
        type=int,
        default=50000,
        help='Number of customers to generate (default: 50000)'
    )
    parser.add_argument(
        '--num-products',
        type=int,
        default=5000,
        help='Number of products to generate (default: 5000)'
    )
    parser.add_argument(
        '--num-orders',
        type=int,
        default=200000,
        help='Number of orders to generate (default: 200000)'
    )
    parser.add_argument(
        '--num-events',
        type=int,
        default=1000000,
        help='Number of events to generate (default: 1000000)'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('../input'),
        help='Output directory for generated data (default: ../input)'
    )
    parser.add_argument(
        '--format',
        choices=['csv', 'json', 'parquet'],
        default='csv',
        help='Output format (default: csv)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    parser.add_argument(
        '--upload-to-s3',
        action='store_true',
        help='Upload generated files to S3 after generation'
    )
    parser.add_argument(
        '--s3-bucket',
        type=str,
        help='S3 bucket name for upload (required if --upload-to-s3 is set)'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.upload_to_s3 and not args.s3_bucket:
        parser.error("--s3-bucket is required when --upload-to-s3 is set")

    # Print configuration
    print("=" * 70)
    print("CloudMart Data Generator")
    print("=" * 70)
    print("Configuration:")
    print(f"  Customers:    {args.num_customers:,}")
    print(f"  Products:     {args.num_products:,}")
    print(f"  Orders:       {args.num_orders:,}")
    print(f"  Events:       {args.num_events:,}")
    print(f"  Output Dir:   {args.output_dir}")
    print(f"  Format:       {args.format.upper()}")
    print(f"  Random Seed:  {args.seed}")
    print("=" * 70)
    print()

    # Initialize generator
    generator = CloudMartDataGenerator(seed=args.seed)

    # Generate data
    start_time = datetime.now()

    try:
        customers_df = generator.generate_customers(args.num_customers)
        products_df = generator.generate_products(args.num_products)
        orders_df = generator.generate_orders(
            customers_df,
            products_df,
            args.num_orders
        )
        events_df = generator.generate_events(customers_df, args.num_events)

        # Prepare dataframes
        dataframes = {
            'customers': customers_df,
            'products': products_df,
            'orders': orders_df,
            'events': events_df
        }

        # Add ingestion timestamps
        dataframes = add_ingestion_timestamps(dataframes)

        # Save to files
        save_dataframes(dataframes, args.output_dir, args.format)

        # Calculate generation time
        elapsed_time = (datetime.now() - start_time).total_seconds()

        print()
        print("=" * 70)
        print("Generation Summary")
        print("=" * 70)
        print(f"Total records generated: {sum(len(df) for df in dataframes.values()):,}")
        print(f"Time elapsed: {elapsed_time:.2f} seconds")
        print(f"Output location: {args.output_dir.absolute()}")
        print()

        # Upload to S3 if requested
        if args.upload_to_s3:
            print("Uploading to S3...")
            try:
                import boto3
                from upload_to_s3 import upload_files_to_s3
                upload_files_to_s3(args.output_dir, args.s3_bucket)
                print("✓ Upload completed successfully")
            except ImportError:
                print("ERROR: boto3 not installed. Install with: pip install boto3")
                sys.exit(1)
            except Exception as e:
                print(f"ERROR during upload: {e}")
                sys.exit(1)

        print("✓ Data generation completed successfully!")

    except Exception as e:
        print(f"\n✗ Error during data generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
