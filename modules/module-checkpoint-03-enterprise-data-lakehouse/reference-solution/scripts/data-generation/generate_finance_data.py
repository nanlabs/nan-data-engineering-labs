#!/usr/bin/env python3
"""
Financial Data Generator for Enterprise Data Lakehouse
Generates synthetic finance domain data including transactions, accounts, budgets, and GL entries.
Writes data to S3 raw zone as JSON with date partitioning.
"""

import argparse
import json
import logging
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import boto3
from faker import Faker
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FinanceDataGenerator:
    """Generator for synthetic financial data."""

    # Transaction types and their characteristics
    TRANSACTION_TYPES = {
        'DEBIT': {'weight': 0.45, 'avg_amount': 150.00, 'std_dev': 100.00},
        'CREDIT': {'weight': 0.30, 'avg_amount': 500.00, 'std_dev': 300.00},
        'TRANSFER': {'weight': 0.15, 'avg_amount': 1000.00, 'std_dev': 800.00},
        'PAYMENT': {'weight': 0.10, 'avg_amount': 250.00, 'std_dev': 150.00}
    }

    ACCOUNT_TYPES = ['CHECKING', 'SAVINGS', 'CREDIT', 'LOAN', 'INVESTMENT', 'BUSINESS']

    MERCHANT_CATEGORIES = [
        'Grocery', 'Restaurant', 'Gas Station', 'Retail', 'Online Shopping',
        'Entertainment', 'Healthcare', 'Utilities', 'Insurance', 'Travel',
        'Education', 'Automotive', 'Home Improvement', 'Electronics', 'Clothing'
    ]

    GL_ACCOUNT_TYPES = [
        'ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE'
    ]

    BUDGET_CATEGORIES = [
        'Payroll', 'Marketing', 'Operations', 'Technology', 'Facilities',
        'Travel', 'Training', 'Consulting', 'Legal', 'Insurance'
    ]

    def __init__(self, seed: Optional[int] = 42):
        """Initialize the generator with optional seed for reproducibility."""
        self.fake = Faker()
        if seed:
            Faker.seed(seed)
            random.seed(seed)

        self.accounts = []
        self.transactions = []
        self.budgets = []
        self.gl_entries = []

    def generate_accounts(self, num_accounts: int = 10000) -> List[Dict]:
        """Generate synthetic account data."""
        logger.info(f"Generating {num_accounts} accounts...")

        accounts = []
        for i in range(num_accounts):
            account_type = random.choice(self.ACCOUNT_TYPES)
            open_date = self.fake.date_between(start_date='-10y', end_date='today')

            # Generate balance based on account type
            if account_type in ['CHECKING', 'SAVINGS']:
                balance = round(random.uniform(100, 50000), 2)
            elif account_type == 'CREDIT':
                balance = round(random.uniform(-10000, 0), 2)
            elif account_type == 'LOAN':
                balance = round(random.uniform(-100000, -1000), 2)
            elif account_type == 'INVESTMENT':
                balance = round(random.uniform(5000, 500000), 2)
            else:  # BUSINESS
                balance = round(random.uniform(10000, 1000000), 2)

            account = {
                'account_id': f'ACC{i+1:08d}',
                'customer_id': f'CUST{random.randint(1, num_accounts//2):08d}',
                'account_type': account_type,
                'balance': balance,
                'currency': 'USD',
                'open_date': open_date.isoformat(),
                'status': random.choices(
                    ['ACTIVE', 'DORMANT', 'CLOSED'],
                    weights=[0.85, 0.10, 0.05]
                )[0],
                'interest_rate': round(random.uniform(0.01, 5.00), 3) if account_type in ['SAVINGS', 'LOAN', 'CREDIT'] else None,
                'credit_limit': round(random.uniform(1000, 50000), 2) if account_type == 'CREDIT' else None,
                'branch_id': f'BR{random.randint(1, 100):03d}',
                'created_at': datetime.now().isoformat()
            }
            accounts.append(account)

        self.accounts = accounts
        logger.info(f"Generated {len(accounts)} accounts")
        return accounts

    def generate_transactions(
        self,
        num_transactions: int = 100000,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Generate synthetic transaction data."""
        logger.info(f"Generating {num_transactions} transactions...")

        if not self.accounts:
            logger.warning("No accounts generated. Generating default accounts first.")
            self.generate_accounts()

        if not start_date:
            start_date = datetime.now() - timedelta(days=365)
        if not end_date:
            end_date = datetime.now()

        transactions = []
        transaction_types = list(self.TRANSACTION_TYPES.keys())
        type_weights = [self.TRANSACTION_TYPES[t]['weight'] for t in transaction_types]

        for i in range(num_transactions):
            transaction_type = random.choices(transaction_types, weights=type_weights)[0]
            type_config = self.TRANSACTION_TYPES[transaction_type]

            # Generate amount with some randomness
            amount = abs(random.gauss(type_config['avg_amount'], type_config['std_dev']))
            amount = max(0.01, min(amount, 100000.00))  # Cap at reasonable limits
            amount = round(amount, 2)

            # Generate timestamp
            time_delta = end_date - start_date
            random_seconds = random.randint(0, int(time_delta.total_seconds()))
            transaction_time = start_date + timedelta(seconds=random_seconds)

            # Select account
            account = random.choice(self.accounts)

            # Generate merchant/description
            merchant_category = random.choice(self.MERCHANT_CATEGORIES)
            merchant_name = f"{self.fake.company()} {merchant_category}"

            transaction = {
                'transaction_id': f'TXN{i+1:010d}',
                'account_id': account['account_id'],
                'transaction_type': transaction_type,
                'amount': amount,
                'currency': 'USD',
                'merchant': merchant_name,
                'merchant_category': merchant_category,
                'merchant_id': f'MER{random.randint(1, 10000):06d}',
                'description': self.fake.sentence(nb_words=6),
                'timestamp': transaction_time.isoformat(),
                'posting_date': (transaction_time + timedelta(days=random.randint(0, 2))).date().isoformat(),
                'status': random.choices(
                    ['COMPLETED', 'PENDING', 'FAILED', 'REVERSED'],
                    weights=[0.90, 0.06, 0.03, 0.01]
                )[0],
                'channel': random.choice(['ONLINE', 'ATM', 'POS', 'MOBILE', 'BRANCH']),
                'auth_code': self.fake.bothify(text='AUTH######'),
                'location': {
                    'city': self.fake.city(),
                    'state': self.fake.state_abbr(),
                    'country': 'USA',
                    'lat': float(self.fake.latitude()),
                    'lon': float(self.fake.longitude())
                },
                'is_international': random.choices([True, False], weights=[0.05, 0.95])[0],
                'is_fraudulent': random.choices([True, False], weights=[0.001, 0.999])[0],
                'created_at': datetime.now().isoformat()
            }
            transactions.append(transaction)

        self.transactions = transactions
        logger.info(f"Generated {len(transactions)} transactions")
        return transactions

    def generate_budgets(self, num_budgets: int = 1000) -> List[Dict]:
        """Generate budget allocation data."""
        logger.info(f"Generating {num_budgets} budget entries...")

        budgets = []
        current_year = datetime.now().year

        for i in range(num_budgets):
            year = random.randint(current_year - 2, current_year + 1)
            quarter = random.randint(1, 4)
            category = random.choice(self.BUDGET_CATEGORIES)

            # Generate budget amounts
            allocated_amount = round(random.uniform(10000, 1000000), 2)
            spent_amount = round(random.uniform(0, allocated_amount * 1.1), 2)  # Allow overruns

            budget = {
                'budget_id': f'BDG{i+1:08d}',
                'department_id': f'DEPT{random.randint(1, 50):03d}',
                'category': category,
                'fiscal_year': year,
                'quarter': quarter,
                'allocated_amount': allocated_amount,
                'spent_amount': spent_amount,
                'remaining_amount': allocated_amount - spent_amount,
                'utilization_pct': round((spent_amount / allocated_amount * 100), 2),
                'status': 'ACTIVE' if year >= current_year else 'CLOSED',
                'approved_by': self.fake.name(),
                'approval_date': self.fake.date_between(
                    start_date=f'{year-1}-10-01',
                    end_date=f'{year}-01-31'
                ).isoformat(),
                'notes': self.fake.sentence(nb_words=8),
                'created_at': datetime.now().isoformat()
            }
            budgets.append(budget)

        self.budgets = budgets
        logger.info(f"Generated {len(budgets)} budget entries")
        return budgets

    def generate_gl_entries(self, num_entries: int = 50000) -> List[Dict]:
        """Generate General Ledger entries."""
        logger.info(f"Generating {num_entries} GL entries...")

        gl_entries = []

        for i in range(num_entries):
            account_type = random.choice(self.GL_ACCOUNT_TYPES)
            entry_date = self.fake.date_between(start_date='-2y', end_date='today')

            # Generate amounts
            debit_amount = round(random.uniform(100, 100000), 2)
            credit_amount = round(random.uniform(100, 100000), 2)

            gl_entry = {
                'entry_id': f'GL{i+1:010d}',
                'gl_account_number': f'{random.randint(1000, 9999)}-{random.randint(100, 999)}',
                'gl_account_name': f"{account_type} - {self.fake.bs().title()}",
                'account_type': account_type,
                'entry_date': entry_date.isoformat(),
                'posting_date': (entry_date + timedelta(days=random.randint(0, 3))).isoformat(),
                'fiscal_period': f"{entry_date.year}-{entry_date.month:02d}",
                'debit_amount': debit_amount if random.random() > 0.5 else 0.0,
                'credit_amount': credit_amount if random.random() > 0.5 else 0.0,
                'currency': 'USD',
                'description': self.fake.sentence(nb_words=8),
                'reference_number': self.fake.bothify(text='REF#######'),
                'journal_id': f'JNL{random.randint(1, 10000):06d}',
                'created_by': self.fake.name(),
                'approved_by': self.fake.name(),
                'status': random.choices(
                    ['POSTED', 'PENDING', 'REVERSED'],
                    weights=[0.92, 0.05, 0.03]
                )[0],
                'created_at': datetime.now().isoformat()
            }
            gl_entries.append(gl_entry)

        self.gl_entries = gl_entries
        logger.info(f"Generated {len(gl_entries)} GL entries")
        return gl_entries

    def write_to_local(self, output_dir: str):
        """Write generated data to local JSON files with date partitioning."""
        logger.info(f"Writing data to local directory: {output_dir}")

        output_path = Path(output_dir)

        # Write accounts
        accounts_path = output_path / 'accounts'
        accounts_path.mkdir(parents=True, exist_ok=True)
        with open(accounts_path / f'accounts_{datetime.now().strftime("%Y%m%d")}.json', 'w') as f:
            json.dump(self.accounts, f, indent=2)
        logger.info(f"Wrote {len(self.accounts)} accounts to {accounts_path}")

        # Write transactions with date partitioning
        transactions_by_date = {}
        for txn in self.transactions:
            txn_date = datetime.fromisoformat(txn['timestamp']).date()
            date_key = txn_date.strftime('%Y-%m-%d')
            if date_key not in transactions_by_date:
                transactions_by_date[date_key] = []
            transactions_by_date[date_key].append(txn)

        for date_key, txns in transactions_by_date.items():
            date_path = output_path / 'transactions' / f'date={date_key}'
            date_path.mkdir(parents=True, exist_ok=True)
            with open(date_path / f'transactions_{date_key}.json', 'w') as f:
                json.dump(txns, f, indent=2)
        logger.info(f"Wrote {len(self.transactions)} transactions to {output_path / 'transactions'}")

        # Write budgets
        budgets_path = output_path / 'budgets'
        budgets_path.mkdir(parents=True, exist_ok=True)
        with open(budgets_path / f'budgets_{datetime.now().strftime("%Y%m%d")}.json', 'w') as f:
            json.dump(self.budgets, f, indent=2)
        logger.info(f"Wrote {len(self.budgets)} budgets to {budgets_path}")

        # Write GL entries
        gl_path = output_path / 'gl_entries'
        gl_path.mkdir(parents=True, exist_ok=True)
        with open(gl_path / f'gl_entries_{datetime.now().strftime("%Y%m%d")}.json', 'w') as f:
            json.dump(self.gl_entries, f, indent=2)
        logger.info(f"Wrote {len(self.gl_entries)} GL entries to {gl_path}")

    def write_to_s3(self, s3_bucket: str, s3_prefix: str = 'raw/finance'):
        """Write generated data to S3 with date partitioning."""
        logger.info(f"Writing data to S3: s3://{s3_bucket}/{s3_prefix}")

        try:
            s3_client = boto3.client('s3')

            # Write accounts
            accounts_key = f"{s3_prefix}/accounts/accounts_{datetime.now().strftime('%Y%m%d')}.json"
            s3_client.put_object(
                Bucket=s3_bucket,
                Key=accounts_key,
                Body=json.dumps(self.accounts).encode('utf-8'),
                ContentType='application/json'
            )
            logger.info(f"Wrote {len(self.accounts)} accounts to s3://{s3_bucket}/{accounts_key}")

            # Write transactions with date partitioning
            transactions_by_date = {}
            for txn in self.transactions:
                txn_date = datetime.fromisoformat(txn['timestamp']).date()
                date_key = txn_date.strftime('%Y-%m-%d')
                if date_key not in transactions_by_date:
                    transactions_by_date[date_key] = []
                transactions_by_date[date_key].append(txn)

            for date_key, txns in transactions_by_date.items():
                txn_key = f"{s3_prefix}/transactions/date={date_key}/transactions_{date_key}.json"
                s3_client.put_object(
                    Bucket=s3_bucket,
                    Key=txn_key,
                    Body=json.dumps(txns).encode('utf-8'),
                    ContentType='application/json'
                )
            logger.info(f"Wrote {len(self.transactions)} transactions to S3 (partitioned by date)")

            # Write budgets
            budgets_key = f"{s3_prefix}/budgets/budgets_{datetime.now().strftime('%Y%m%d')}.json"
            s3_client.put_object(
                Bucket=s3_bucket,
                Key=budgets_key,
                Body=json.dumps(self.budgets).encode('utf-8'),
                ContentType='application/json'
            )
            logger.info(f"Wrote {len(self.budgets)} budgets to s3://{s3_bucket}/{budgets_key}")

            # Write GL entries
            gl_key = f"{s3_prefix}/gl_entries/gl_entries_{datetime.now().strftime('%Y%m%d')}.json"
            s3_client.put_object(
                Bucket=s3_bucket,
                Key=gl_key,
                Body=json.dumps(self.gl_entries).encode('utf-8'),
                ContentType='application/json'
            )
            logger.info(f"Wrote {len(self.gl_entries)} GL entries to s3://{s3_bucket}/{gl_key}")

        except ClientError as e:
            logger.error(f"Error writing to S3: {e}")
            raise


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate synthetic financial data for Enterprise Data Lakehouse'
    )

    parser.add_argument(
        '--records',
        type=int,
        default=100000,
        help='Number of transaction records to generate (default: 100000)'
    )

    parser.add_argument(
        '--accounts',
        type=int,
        default=10000,
        help='Number of account records to generate (default: 10000)'
    )

    parser.add_argument(
        '--budgets',
        type=int,
        default=1000,
        help='Number of budget records to generate (default: 1000)'
    )

    parser.add_argument(
        '--gl-entries',
        type=int,
        default=50000,
        help='Number of GL entry records to generate (default: 50000)'
    )

    parser.add_argument(
        '--start-date',
        type=str,
        help='Start date for transaction generation (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--end-date',
        type=str,
        help='End date for transaction generation (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--output-path',
        type=str,
        default='./data/finance',
        help='Local output path for generated data'
    )

    parser.add_argument(
        '--s3-bucket',
        type=str,
        help='S3 bucket name for output (if not specified, writes to local only)'
    )

    parser.add_argument(
        '--s3-prefix',
        type=str,
        default='raw/finance',
        help='S3 key prefix (default: raw/finance)'
    )

    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )

    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_args()

    # Parse dates if provided
    start_date = None
    end_date = None

    if args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        except ValueError:
            logger.error(f"Invalid start date format: {args.start_date}. Use YYYY-MM-DD")
            sys.exit(1)

    if args.end_date:
        try:
            end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
        except ValueError:
            logger.error(f"Invalid end date format: {args.end_date}. Use YYYY-MM-DD")
            sys.exit(1)

    # Initialize generator
    logger.info("Initializing Finance Data Generator...")
    generator = FinanceDataGenerator(seed=args.seed)

    # Generate data
    generator.generate_accounts(num_accounts=args.accounts)
    generator.generate_transactions(
        num_transactions=args.records,
        start_date=start_date,
        end_date=end_date
    )
    generator.generate_budgets(num_budgets=args.budgets)
    generator.generate_gl_entries(num_entries=args.gl_entries)

    # Write to local
    generator.write_to_local(args.output_path)

    # Write to S3 if bucket specified
    if args.s3_bucket:
        generator.write_to_s3(args.s3_bucket, args.s3_prefix)

    logger.info("Finance data generation completed successfully!")
    logger.info(f"Generated: {len(generator.accounts)} accounts, "
                f"{len(generator.transactions)} transactions, "
                f"{len(generator.budgets)} budgets, "
                f"{len(generator.gl_entries)} GL entries")


if __name__ == '__main__':
    main()
