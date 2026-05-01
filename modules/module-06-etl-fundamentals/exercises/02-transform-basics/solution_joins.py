#!/usr/bin/env python3
"""
Exercise 02 - Joins - SOLUTION
"""
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def join_users_transactions(
    users_df: pd.DataFrame,
    transactions_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Join users and transactions.

    Returns enriched transactions with user info.
    """
    logger.info("Joining users and transactions")

    # Left join: keep all transactions
    result = transactions_df.merge(
        users_df[['id', 'email', 'country', 'status']],
        left_on='user_id',
        right_on='id',
        how='left',
        suffixes=('_txn', '_user')
    )

    # Rename columns
    result = result.rename(columns={
        'status_txn': 'transaction_status',
        'status_user': 'user_status'
    })

    # Drop redundant id column
    result = result.drop('id', axis=1)

    logger.info(f"Joined: {len(result)} records")
    return result

def aggregate_user_stats(
    users_df: pd.DataFrame,
    transactions_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Calculate user statistics from transactions.
    """
    # Aggregate transactions by user
    user_stats = transactions_df.groupby('user_id').agg({
        'transaction_id': 'count',
        'amount': ['sum', 'mean', 'max']
    }).round(2)

    # Flatten column names
    user_stats.columns = ['_'.join(col).strip() for col in user_stats.columns.values]
    user_stats = user_stats.rename(columns={
        'transaction_id_count': 'transaction_count',
        'amount_sum': 'total_spent',
        'amount_mean': 'avg_transaction',
        'amount_max': 'max_transaction'
    })

    # Join with users
    result = users_df.merge(
        user_stats,
        left_on='id',
        right_index=True,
        how='left'
    )

    # Fill NaN for users with no transactions
    result[['transaction_count', 'total_spent', 'avg_transaction', 'max_transaction']] = \
        result[['transaction_count', 'total_spent', 'avg_transaction', 'max_transaction']].fillna(0)

    return result

def main():
    """Test joins."""
    data_dir = Path(__file__).parents[2] / 'data' / 'raw'
    users_file = data_dir / 'users_clean.csv'
    trans_file = data_dir / 'transactions_clean.csv'

    if not users_file.exists() or not trans_file.exists():
        print("⚠️  Data files not found. Run data generation first.")
        return

    print("Loading data...")
    users_df = pd.read_csv(users_file)
    trans_df = pd.read_csv(trans_file)

    print(f"Users: {len(users_df)}")
    print(f"Transactions: {len(trans_df)}")

    print("\nJoining users and transactions...")
    enriched = join_users_transactions(users_df, trans_df)
    print(f"✓ Enriched transactions: {len(enriched)}")
    print(enriched.head())

    print("\nCalculating user stats...")
    user_stats = aggregate_user_stats(users_df, trans_df)
    print("✓ User stats calculated")
    print(user_stats.nlargest(10, 'total_spent')[
        ['email', 'country', 'transaction_count', 'total_spent', 'avg_transaction']
    ])

if __name__ == '__main__':
    main()
