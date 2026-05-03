#!/usr/bin/env python3
"""
Generate large transaction dataset for batch processing exercises.

This script generates realistic e-commerce transaction data with:
- 10M+ transactions
- Date-based partitioning
- Various product categories
- Multiple payment methods
- Different countries
"""

import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any
import pandas as pd
from tqdm import tqdm


# Configuration
CATEGORIES = ["electronics", "clothing", "books", "home", "sports", "toys", "food", "beauty"]
STATUSES = ["completed", "pending", "failed", "refunded"]
PAYMENT_METHODS = ["credit_card", "debit_card", "paypal", "bank_transfer", "crypto"]
COUNTRIES = ["US", "UK", "CA", "DE", "FR", "ES", "IT", "BR", "MX", "AR"]

# Weighted distributions (more realistic)
STATUS_WEIGHTS = [0.85, 0.10, 0.04, 0.01]  # Most completed
PAYMENT_WEIGHTS = [0.50, 0.25, 0.15, 0.08, 0.02]
CATEGORY_WEIGHTS = [0.25, 0.20, 0.15, 0.12, 0.10, 0.08, 0.06, 0.04]


def generate_transaction(
    transaction_id: int,
    timestamp: datetime,
    num_users: int = 1000000,
    num_products: int = 100000
) -> Dict[str, Any]:
    """Generate a single transaction record."""

    # IDs
    user_id = f"USER{random.randint(1, num_users):06d}"
    product_id = f"PROD{random.randint(1, num_products):05d}"

    # Amount based on category
    category = random.choices(CATEGORIES, weights=CATEGORY_WEIGHTS)[0]

    if category == "electronics":
        amount = round(random.uniform(50, 5000), 2)
    elif category == "clothing":
        amount = round(random.uniform(20, 300), 2)
    elif category == "books":
        amount = round(random.uniform(10, 100), 2)
    else:
        amount = round(random.uniform(5, 500), 2)

    # Quantity (inversely proportional to amount)
    if amount > 1000:
        quantity = random.randint(1, 3)
    else:
        quantity = random.randint(1, 10)

    # Other fields
    status = random.choices(STATUSES, weights=STATUS_WEIGHTS)[0]
    payment_method = random.choices(PAYMENT_METHODS, weights=PAYMENT_WEIGHTS)[0]
    country = random.choice(COUNTRIES)
    discount = random.choice([0, 0, 0, 5, 10, 15, 20, 25])  # Most no discount

    return {
        "transaction_id": f"TXN{transaction_id:010d}",
        "user_id": user_id,
        "product_id": product_id,
        "amount": amount,
        "quantity": quantity,
        "timestamp": timestamp.isoformat(),
        "status": status,
        "payment_method": payment_method,
        "country": country,
        "category": category,
        "discount": discount
    }


def generate_batch(
    start_date: datetime,
    num_transactions: int,
    start_id: int = 1
) -> pd.DataFrame:
    """Generate a batch of transactions for a single day."""

    transactions = []

    # Generate timestamps throughout the day (weighted towards business hours)
    for i in range(num_transactions):
        # Add some hour weighting (more transactions during daytime)
        hour = random.choices(
            range(24),
            weights=[1, 1, 1, 1, 2, 3, 5, 8, 10, 12, 12, 12,
                    11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 2, 1]
        )[0]
        minute = random.randint(0, 59)
        second = random.randint(0, 59)

        timestamp = start_date + timedelta(hours=hour, minutes=minute, seconds=second)

        transaction = generate_transaction(
            transaction_id=start_id + i,
            timestamp=timestamp
        )
        transactions.append(transaction)

    return pd.DataFrame(transactions)


def main():
    parser = argparse.ArgumentParser(description="Generate transaction dataset")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw/transactions",
        help="Output directory for generated data"
    )
    parser.add_argument(
        "--total-records",
        type=int,
        default=10_000_000,
        help="Total number of transactions to generate"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2024-01-01",
        help="Start date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=90,
        help="Number of days to generate"
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["parquet", "csv", "json"],
        default="parquet",
        help="Output format"
    )
    parser.add_argument(
        "--partition-by",
        type=str,
        choices=["date", "none"],
        default="date",
        help="Partitioning strategy"
    )

    args = parser.parse_args()

    # Setup
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    transactions_per_day = args.total_records // args.days

    print(f"Generating {args.total_records:,} transactions")
    print(f"Date range: {args.start_date} to {(start_date + timedelta(days=args.days-1)).date()}")
    print(f"Transactions per day: {transactions_per_day:,}")
    print(f"Output format: {args.format}")
    print(f"Partitioning: {args.partition_by}")
    print()

    # Generate data
    transaction_id = 1

    for day in tqdm(range(args.days), desc="Generating days"):
        current_date = start_date + timedelta(days=day)

        # Generate day's transactions
        df = generate_batch(
            start_date=current_date,
            num_transactions=transactions_per_day,
            start_id=transaction_id
        )

        transaction_id += transactions_per_day

        # Determine output path
        if args.partition_by == "date":
            partition_dir = output_dir / f"year={current_date.year}" / \
                           f"month={current_date.month:02d}" / \
                           f"day={current_date.day:02d}"
            partition_dir.mkdir(parents=True, exist_ok=True)
            output_path = partition_dir / f"transactions.{args.format}"
        else:
            output_path = output_dir / f"transactions_{current_date.date()}.{args.format}"

        # Write data
        if args.format == "parquet":
            df.to_parquet(output_path, index=False, compression="snappy")
        elif args.format == "csv":
            df.to_csv(output_path, index=False)
        elif args.format == "json":
            df.to_json(output_path, orient="records", lines=True)

    # Generate summary
    total_size_mb = sum(f.stat().st_size for f in output_dir.rglob("*") if f.is_file()) / (1024 * 1024)

    print()
    print("=" * 50)
    print("Generation Complete!")
    print("=" * 50)
    print(f"Total records: {args.total_records:,}")
    print(f"Total files: {len(list(output_dir.rglob('*.[pjc]*')))}")
    print(f"Total size: {total_size_mb:.2f} MB")
    print(f"Output directory: {output_dir}")
    print()

    # Sample data
    if args.partition_by == "date":
        sample_path = output_dir / f"year={start_date.year}" / \
                     f"month={start_date.month:02d}" / \
                     f"day={start_date.day:02d}" / f"transactions.{args.format}"
    else:
        sample_path = output_dir / f"transactions_{start_date.date()}.{args.format}"

    if args.format == "parquet":
        sample = pd.read_parquet(sample_path)
    elif args.format == "csv":
        sample = pd.read_csv(sample_path)
    else:
        sample = pd.read_json(sample_path, lines=True)

    print("Sample data (first 5 records):")
    print(sample.head())


if __name__ == "__main__":
    main()
