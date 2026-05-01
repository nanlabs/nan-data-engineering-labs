#!/usr/bin/env python3
"""
Generate synthetic transaction data for ETL exercises.
"""
import pandas as pd
from faker import Faker
import random
from pathlib import Path

fake = Faker()
random.seed(42)
Faker.seed(42)

def generate_transactions(n_transactions=50000, n_users=10000):
    """Generate synthetic transaction data."""
    transactions = []

    payment_methods = ['credit_card', 'debit_card', 'paypal', 'bank_transfer', 'cash']
    statuses = ['completed', 'pending', 'failed', 'refunded']
    status_weights = [0.85, 0.08, 0.05, 0.02]  # Most are completed

    for _ in range(n_transactions):
        timestamp = fake.date_time_between(start_date='-1y', end_date='now')

        # Generate transaction ID
        txn_id = f"TXN-{random.randint(10000000, 99999999)}"

        transaction = {
            'transaction_id': txn_id,
            'user_id': random.randint(1, n_users),
            'product_id': random.randint(1, 1000),
            'amount': round(random.uniform(5.0, 500.0), 2),
            'quantity': random.randint(1, 10),
            'payment_method': random.choice(payment_methods),
            'status': random.choices(statuses, weights=status_weights)[0],
            'timestamp': timestamp.isoformat(),
            'notes': fake.text(max_nb_chars=100) if random.random() < 0.3 else None
        }
        transactions.append(transaction)

    return pd.DataFrame(transactions)

def generate_transactions_with_issues(n_transactions=50000):
    """Generate transactions with data quality issues."""
    df = generate_transactions(n_transactions)

    # 3% missing user_id
    mask = df.sample(frac=0.03).index
    df.loc[mask, 'user_id'] = None

    # 2% negative amounts
    mask = df.sample(frac=0.02).index
    df.loc[mask, 'amount'] = -abs(df.loc[mask, 'amount'])

    # 1% invalid status
    mask = df.sample(frac=0.01).index
    df.loc[mask, 'status'] = 'unknown'

    # 5% duplicate transaction_ids
    n_duplicates = int(len(df) * 0.05)
    duplicates = df.sample(n=n_duplicates).copy()
    df = pd.concat([df, duplicates], ignore_index=True)

    return df

def main():
    """Generate and save transaction data."""
    output_dir = Path(__file__).parent.parent / 'raw'
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating transactions...")

    # Clean version
    df_clean = generate_transactions(50000)
    clean_path = output_dir / 'transactions_clean.csv'
    df_clean.to_csv(clean_path, index=False)
    print(f"✓ Generated {len(df_clean)} clean transactions → {clean_path}")

    # Dirty version
    df_dirty = generate_transactions_with_issues(50000)
    dirty_path = output_dir / 'transactions_dirty.csv'
    df_dirty.to_csv(dirty_path, index=False)
    print(f"✓ Generated {len(df_dirty)} dirty transactions → {dirty_path}")

    # JSON format
    json_path = output_dir / 'transactions.json'
    df_clean.to_json(json_path, orient='records', lines=True)
    print(f"✓ Generated JSON version → {json_path}")

    # Parquet format
    parquet_path = output_dir / 'transactions.parquet'
    df_clean.to_parquet(parquet_path, index=False)
    print(f"✓ Generated Parquet version → {parquet_path}")

    # Sample
    sample = df_clean.head(1000)
    sample_path = output_dir / 'transactions_sample.csv'
    sample.to_csv(sample_path, index=False)
    print(f"✓ Generated sample (1000 records) → {sample_path}")

    # Statistics
    print("\n📊 Statistics:")
    print(f"  Total transactions: {len(df_clean)}")
    print(f"  Total amount: ${df_clean['amount'].sum():,.2f}")
    print(f"  Average transaction: ${df_clean['amount'].mean():.2f}")
    print("  Status distribution:")
    print(df_clean['status'].value_counts().to_string())

if __name__ == '__main__':
    main()
