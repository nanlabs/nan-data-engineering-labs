#!/usr/bin/env python3
"""
Generate user dataset for batch processing exercises.

Creates a realistic user base with:
- 1M users
- Different tiers
- Geographic distribution
- Activity levels
"""

import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any
import pandas as pd
from tqdm import tqdm


# Configuration
COUNTRIES = ["US", "UK", "CA", "DE", "FR", "ES", "IT", "BR", "MX", "AR"]
TIERS = ["bronze", "silver", "gold", "platinum"]
TIER_WEIGHTS = [0.60, 0.25, 0.12, 0.03]

# Sample names
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Barbara", "David", "Elizabeth", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Thompson", "White"
]


def generate_email(name: str, user_id: int) -> str:
    """Generate realistic email address."""
    name_part = name.lower().replace(" ", ".")
    domains = ["gmail.com", "yahoo.com", "outlook.com", "example.com", "mail.com"]
    domain = random.choice(domains)

    # Sometimes add number to email
    if random.random() > 0.7:
        return f"{name_part}{user_id % 1000}@{domain}"
    return f"{name_part}@{domain}"


def generate_user(user_id: int, start_date: datetime) -> Dict[str, Any]:
    """Generate a single user record."""

    # Name
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    name = f"{first_name} {last_name}"

    # Email
    email = generate_email(name, user_id)

    # Age distribution (25-55 peak)
    age = int(random.normalvariate(40, 15))
    age = max(18, min(100, age))

    # Country
    country = random.choice(COUNTRIES)

    # Created date (random date in past 3 years)
    days_ago = random.randint(0, 1095)  # 3 years
    created_at = start_date - timedelta(days=days_ago)

    # Tier based on account age and activity
    if days_ago > 730:  # > 2 years
        tier = random.choices(TIERS, weights=[0.30, 0.30, 0.25, 0.15])[0]
    elif days_ago > 365:  # > 1 year
        tier = random.choices(TIERS, weights=[0.50, 0.30, 0.15, 0.05])[0]
    else:
        tier = random.choices(TIERS, weights=[0.80, 0.15, 0.04, 0.01])[0]

    # Total spent (correlated with tier)
    tier_spending = {
        "bronze": (0, 1000),
        "silver": (1000, 5000),
        "gold": (5000, 20000),
        "platinum": (20000, 100000)
    }
    min_spent, max_spent = tier_spending[tier]
    total_spent = round(random.uniform(min_spent, max_spent), 2)

    # Active status (95% active)
    is_active = random.random() > 0.05

    return {
        "user_id": f"USER{user_id:06d}",
        "email": email,
        "name": name,
        "age": age,
        "country": country,
        "created_at": created_at.isoformat(),
        "tier": tier,
        "total_spent": total_spent,
        "is_active": is_active
    }


def main():
    parser = argparse.ArgumentParser(description="Generate user dataset")
    parser.add_argument(
        "--output-path",
        type=str,
        default="data/raw/users.parquet",
        help="Output file path"
    )
    parser.add_argument(
        "--num-users",
        type=int,
        default=1_000_000,
        help="Number of users to generate"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10000,
        help="Batch size for generation"
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["parquet", "csv", "json"],
        default="parquet",
        help="Output format"
    )

    args = parser.parse_args()

    # Setup
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    start_date = datetime.now()

    print(f"Generating {args.num_users:,} users")
    print(f"Output: {output_path}")
    print(f"Format: {args.format}")
    print()

    # Generate users in batches
    all_users = []

    for user_id in tqdm(range(1, args.num_users + 1), desc="Generating users"):
        user = generate_user(user_id, start_date)
        all_users.append(user)

        # Write batch
        if len(all_users) >= args.batch_size or user_id == args.num_users:
            df = pd.DataFrame(all_users)

            if user_id == len(all_users):  # First batch
                mode = "w"
            else:
                mode = "a"

            if args.format == "parquet":
                if mode == "w":
                    df.to_parquet(output_path, index=False, compression="snappy")
                else:
                    # Append to parquet
                    existing = pd.read_parquet(output_path)
                    combined = pd.concat([existing, df], ignore_index=True)
                    combined.to_parquet(output_path, index=False, compression="snappy")
            elif args.format == "csv":
                df.to_csv(output_path, index=False, mode=mode, header=(mode == "w"))
            elif args.format == "json":
                df.to_json(output_path, orient="records", lines=True, mode=mode)

            all_users = []

    # Summary
    if args.format == "parquet":
        df = pd.read_parquet(output_path)
    elif args.format == "csv":
        df = pd.read_csv(output_path)
    else:
        df = pd.read_json(output_path, lines=True)

    size_mb = output_path.stat().st_size / (1024 * 1024)

    print()
    print("=" * 50)
    print("Generation Complete!")
    print("=" * 50)
    print(f"Total users: {len(df):,}")
    print(f"File size: {size_mb:.2f} MB")
    print()

    print("Tier distribution:")
    print(df["tier"].value_counts())
    print()

    print("Country distribution:")
    print(df["country"].value_counts().head(5))
    print()

    print("Sample data (first 5 users):")
    print(df.head())


if __name__ == "__main__":
    main()
