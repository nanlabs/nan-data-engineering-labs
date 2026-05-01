#!/usr/bin/env python3
"""
Generate sample datasets for Module 02 exercises.
Creates realistic e-commerce data in multiple formats.
"""

import pandas as pd
import numpy as np
from faker import Faker
from pathlib import Path
import argparse
from datetime import datetime, timedelta
import fastavro
import json


class SampleDataGenerator:
    """Generate realistic sample data for training exercises."""

    def __init__(self, seed=42):
        self.fake = Faker()
        Faker.seed(seed)
        np.random.seed(seed)
        self.countries = ['USA', 'UK', 'Canada', 'Germany', 'France', 'Spain', 'Italy', 'Australia']
        self.statuses = ['completed', 'pending', 'cancelled', 'refunded']
        self.categories = ['Electronics', 'Clothing', 'Home', 'Books', 'Sports', 'Toys']

    def generate_transactions(self, num_rows: int = 100000) -> pd.DataFrame:
        """Generate transaction data."""
        print(f"Generating {num_rows:,} transactions...")

        # Generate dates (last 365 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        timestamps = [
            start_date + timedelta(
                seconds=np.random.randint(0, int((end_date - start_date).total_seconds()))
            )
            for _ in range(num_rows)
        ]

        data = {
            'transaction_id': range(1, num_rows + 1),
            'user_id': np.random.randint(1, 50000, num_rows),
            'product_id': np.random.randint(1, 10000, num_rows),
            'amount': np.round(np.random.uniform(5.0, 500.0, num_rows), 2),
            'timestamp': timestamps,
            'country': np.random.choice(self.countries, num_rows),
            'status': np.random.choice(self.statuses, num_rows, p=[0.7, 0.15, 0.1, 0.05])
        }

        df = pd.DataFrame(data)
        df = df.sort_values('timestamp').reset_index(drop=True)

        print(f"✓ Generated {len(df):,} transactions")
        print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"  Countries: {df['country'].nunique()}")

        return df

    def generate_users(self, num_rows: int = 10000) -> pd.DataFrame:
        """Generate user data."""
        print(f"Generating {num_rows:,} users...")

        data = {
            'user_id': range(1, num_rows + 1),
            'email': [self.fake.email() for _ in range(num_rows)],
            'first_name': [self.fake.first_name() for _ in range(num_rows)],
            'last_name': [self.fake.last_name() for _ in range(num_rows)],
            'registration_date': [
                self.fake.date_between(start_date='-2y', end_date='today')
                for _ in range(num_rows)
            ],
            'country': np.random.choice(self.countries, num_rows),
            'age': np.random.randint(18, 75, num_rows)
        }

        df = pd.DataFrame(data)
        print(f"✓ Generated {len(df):,} users")

        return df

    def generate_products(self, num_rows: int = 5000) -> pd.DataFrame:
        """Generate product catalog."""
        print(f"Generating {num_rows:,} products...")

        data = {
            'product_id': range(1, num_rows + 1),
            'name': [self.fake.catch_phrase() for _ in range(num_rows)],
            'category': np.random.choice(self.categories, num_rows),
            'price': np.round(np.random.uniform(10.0, 1000.0, num_rows), 2),
            'stock': np.random.randint(0, 1000, num_rows),
            'rating': np.round(np.random.uniform(1.0, 5.0, num_rows), 1)
        }

        df = pd.DataFrame(data)
        print(f"✓ Generated {len(df):,} products")

        return df

    def generate_logs(self, num_rows: int = 50000) -> list:
        """Generate event logs (JSON format)."""
        print(f"Generating {num_rows:,} log events...")

        events = ['page_view', 'click', 'search', 'add_to_cart', 'checkout']

        logs = []
        for i in range(num_rows):
            logs.append({
                'event_id': i + 1,
                'timestamp': (datetime.now() - timedelta(days=np.random.randint(0, 30))).isoformat(),
                'event_type': np.random.choice(events),
                'user_id': int(np.random.randint(1, 50000)),
                'session_id': self.fake.uuid4(),
                'metadata': {
                    'page': self.fake.uri_path(),
                    'device': np.random.choice(['mobile', 'desktop', 'tablet']),
                    'browser': np.random.choice(['Chrome', 'Firefox', 'Safari', 'Edge'])
                }
            })

        print(f"✓ Generated {len(logs):,} log events")

        return logs

    def save_transactions_csv(self, df: pd.DataFrame, output_path: Path):
        """Save transactions as CSV."""
        print(f"Saving transactions to {output_path}...")
        df.to_csv(output_path, index=False)
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"✓ Saved CSV: {size_mb:.2f} MB")

    def save_users_parquet(self, df: pd.DataFrame, output_path: Path):
        """Save users as Parquet."""
        print(f"Saving users to {output_path}...")
        df.to_parquet(output_path, engine='pyarrow', compression='snappy', index=False)
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"✓ Saved Parquet: {size_mb:.2f} MB")

    def save_products_avro(self, df: pd.DataFrame, output_path: Path):
        """Save products as Avro."""
        print(f"Saving products to {output_path}...")

        schema = {
            'type': 'record',
            'name': 'Product',
            'namespace': 'com.globalmart.catalog',
            'fields': [
                {'name': 'product_id', 'type': 'int'},
                {'name': 'name', 'type': 'string'},
                {'name': 'category', 'type': 'string'},
                {'name': 'price', 'type': 'double'},
                {'name': 'stock', 'type': 'int'},
                {'name': 'rating', 'type': 'double'}
            ]
        }

        records = df.to_dict('records')

        with open(output_path, 'wb') as out:
            fastavro.writer(out, schema, records)

        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"✓ Saved Avro: {size_mb:.2f} MB")

    def save_logs_json(self, logs: list, output_path: Path):
        """Save logs as JSONL."""
        print(f"Saving logs to {output_path}...")

        with open(output_path, 'w') as f:
            for log in logs:
                f.write(json.dumps(log) + '\n')

        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"✓ Saved JSONL: {size_mb:.2f} MB")

    def generate_all(self, output_dir: Path,
                     transactions: int = 100000,
                     users: int = 10000,
                     products: int = 5000,
                     logs: int = 50000):
        """Generate all sample datasets."""
        output_dir.mkdir(parents=True, exist_ok=True)

        print("\n" + "="*80)
        print("GENERATING SAMPLE DATA FOR MODULE 02")
        print("="*80 + "\n")

        # Generate and save transactions (CSV for Exercise 02)
        df_transactions = self.generate_transactions(transactions)
        self.save_transactions_csv(df_transactions, output_dir / 'transactions.csv')

        # Generate and save users (Parquet)
        df_users = self.generate_users(users)
        self.save_users_parquet(df_users, output_dir / 'users.parquet')

        # Generate and save products (Avro for format diversity)
        df_products = self.generate_products(products)
        self.save_products_avro(df_products, output_dir / 'products.avro')

        # Generate and save logs (JSONL for semi-structured data)
        logs = self.generate_logs(logs)
        self.save_logs_json(logs, output_dir / 'logs.jsonl')

        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"✓ transactions.csv: {transactions:,} rows (CSV format)")
        print(f"✓ users.parquet: {users:,} rows (Parquet format)")
        print(f"✓ products.avro: {products:,} rows (Avro format)")
        print(f"✓ logs.jsonl: {logs:,} rows (JSONL format)")
        print(f"\nAll files saved to: {output_dir.absolute()}")
        print("="*80)


def main():
    """Main function with CLI."""
    parser = argparse.ArgumentParser(description='Generate sample data for Module 02 exercises')
    parser.add_argument('--output-dir', '-o', default='data', help='Output directory')
    parser.add_argument('--transactions', '-t', type=int, default=100000, help='Number of transactions')
    parser.add_argument('--users', '-u', type=int, default=10000, help='Number of users')
    parser.add_argument('--products', '-p', type=int, default=5000, help='Number of products')
    parser.add_argument('--logs', '-l', type=int, default=50000, help='Number of log events')
    parser.add_argument('--seed', '-s', type=int, default=42, help='Random seed for reproducibility')

    args = parser.parse_args()

    generator = SampleDataGenerator(seed=args.seed)
    output_dir = Path(args.output_dir)

    generator.generate_all(
        output_dir,
        transactions=args.transactions,
        users=args.users,
        products=args.products,
        logs=args.logs
    )

    print("\n✅ Sample data generation completed successfully!")
    print("\nNext steps:")
    print("  • Run Exercise 02: python exercises/02-file-formats/solution/convert_formats.py data/transactions.csv output/")
    print("  • Run Exercise 03: python exercises/03-partitioning-strategies/solution/partition_data.py data/transactions.csv output/")


if __name__ == '__main__':
    main()
