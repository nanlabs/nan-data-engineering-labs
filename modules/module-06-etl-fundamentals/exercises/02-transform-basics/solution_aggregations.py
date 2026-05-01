#!/usr/bin/env python3
"""
Exercise 02 - Aggregations - SOLUTION
"""
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def aggregate_transactions(df: pd.DataFrame) -> dict:
    """
    Calculate transaction aggregations.

    Returns:
        Dictionary with various aggregations
    """
    logger.info("Calculating aggregations")

    results = {}

    # Overall statistics
    results['total_transactions'] = len(df)
    results['total_amount'] = df['amount'].sum()
    results['avg_amount'] = df['amount'].mean()
    results['median_amount'] = df['amount'].median()

    # By status
    results['by_status'] = df.groupby('status').agg({
        'transaction_id': 'count',
        'amount': ['sum', 'mean']
    }).to_dict()

    # By payment method
    results['by_payment'] = df.groupby('payment_method').agg({
        'amount': ['sum', 'count', 'mean']
    }).round(2).to_dict()

    # Top users by transaction count
    top_users = df.groupby('user_id').size().sort_values(ascending=False).head(10)
    results['top_users_by_count'] = top_users.to_dict()

    # Top users by amount
    top_users_amount = df.groupby('user_id')['amount'].sum().sort_values(ascending=False).head(10)
    results['top_users_by_amount'] = top_users_amount.to_dict()

    logger.info("Aggregations complete")
    return results

def aggregate_by_date(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate transactions by date."""
    df['date'] = pd.to_datetime(df['timestamp']).dt.date

    daily = df.groupby('date').agg({
        'transaction_id': 'count',
        'amount': ['sum', 'mean', 'std']
    }).round(2)

    daily.columns = ['_'.join(col).strip() for col in daily.columns.values]
    daily = daily.rename(columns={
        'transaction_id_count': 'count',
        'amount_sum': 'total',
        'amount_mean': 'avg',
        'amount_std': 'std_dev'
    })

    return daily

def main():
    """Test aggregations."""
    data_dir = Path(__file__).parents[2] / 'data' / 'raw'
    trans_file = data_dir / 'transactions_clean.csv'

    if not trans_file.exists():
        print("⚠️  Transaction data not found. Run data generation first.")
        return

    print("Loading transactions...")
    df = pd.read_csv(trans_file, parse_dates=['timestamp'])

    print("\nCalculating aggregations...")
    results = aggregate_transactions(df)

    print("\n📊 Overall Statistics:")
    print(f"  Total transactions: {results['total_transactions']:,}")
    print(f"  Total amount: ${results['total_amount']:,.2f}")
    print(f"  Average amount: ${results['avg_amount']:.2f}")
    print(f"  Median amount: ${results['median_amount']:.2f}")

    print("\n📈 Daily aggregations:")
    daily = aggregate_by_date(df)
    print(daily.head(10))

if __name__ == '__main__':
    main()
