#!/usr/bin/env python3
"""
Generate synthetic sample datasets for Module 01 exercises
"""

import json
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
OUTPUT_DIR = Path(__file__).parent
NUM_TRANSACTIONS = 10000
NUM_USERS = 1000
NUM_PRODUCTS = 500


def generate_transactions():
    """Generate sample e-commerce transactions"""
    print("Generating transactions...")

    start_date = datetime(2024, 1, 1)
    transactions = []

    for i in range(NUM_TRANSACTIONS):
        transaction_date = start_date + timedelta(
            days=random.randint(0, 365),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

        transactions.append({
            'transaction_id': f'TXN{i+1:06d}',
            'user_id': f'USER{random.randint(1, NUM_USERS):04d}',
            'product_id': f'PROD{random.randint(1, NUM_PRODUCTS):04d}',
            'quantity': random.randint(1, 5),
            'unit_price': round(random.uniform(9.99, 299.99), 2),
            'total_amount': 0,  # Will calculate
            'payment_method': random.choice(['credit_card', 'debit_card', 'paypal', 'gift_card']),
            'status': random.choice(['completed', 'pending', 'failed', 'refunded']),
            'timestamp': transaction_date.isoformat(),
            'country': random.choice(['US', 'UK', 'CA', 'AU', 'DE', 'FR', 'ES', 'IT']),
            'device': random.choice(['mobile', 'desktop', 'tablet'])
        })

        # Calculate total
        transactions[-1]['total_amount'] = round(
            transactions[-1]['quantity'] * transactions[-1]['unit_price'], 2
        )

    # Write CSV
    csv_file = OUTPUT_DIR / 'transactions-sample.csv'
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=transactions[0].keys())
        writer.writeheader()
        writer.writerows(transactions)

    print(f"✓ Created {csv_file} ({len(transactions)} rows)")
    return transactions


def generate_logs():
    """Generate sample application logs"""
    print("Generating logs...")

    event_types = ['page_view', 'add_to_cart', 'checkout', 'purchase',
                   'search', 'login', 'logout', 'error']

    start_date = datetime(2024, 1, 1)
    logs = []

    for i in range(50000):
        log_date = start_date + timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )

        logs.append({
            'timestamp': log_date.isoformat(),
            'level': random.choice(['INFO', 'INFO', 'INFO', 'WARN', 'ERROR']),
            'event_type': random.choice(event_types),
            'user_id': f'USER{random.randint(1, NUM_USERS):04d}',
            'session_id': f'SESSION{random.randint(1, 10000):06d}',
            'ip_address': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
            'user_agent': random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
            ]),
            'page_url': random.choice([
                '/home', '/products', '/cart', '/checkout',
                '/account', '/search', '/product/123'
            ]),
            'response_time_ms': random.randint(50, 2000),
            'status_code': random.choice([200, 200, 200, 200, 301, 404, 500])
        })

    # Write JSON Lines
    json_file = OUTPUT_DIR / 'logs-sample.jsonl'
    with open(json_file, 'w') as f:
        for log in logs:
            f.write(json.dumps(log) + '\n')

    print(f"✓ Created {json_file} ({len(logs)} events)")
    return logs


def generate_users():
    """Generate sample user data"""
    print("Generating users...")

    first_names = ['John', 'Jane', 'Bob', 'Alice', 'Charlie', 'Diana',
                   'Eve', 'Frank', 'Grace', 'Henry']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones',
                  'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']

    users = []
    start_date = datetime(2023, 1, 1)

    for i in range(NUM_USERS):
        signup_date = start_date + timedelta(days=random.randint(0, 365))

        first = random.choice(first_names)
        last = random.choice(last_names)

        users.append({
            'user_id': f'USER{i+1:04d}',
            'email': f"{first.lower()}.{last.lower()}{random.randint(1,999)}@example.com",
            'first_name': first,
            'last_name': last,
            'signup_date': signup_date.date().isoformat(),
            'country': random.choice(['US', 'UK', 'CA', 'AU', 'DE', 'FR']),
            'account_type': random.choice(['free', 'premium', 'enterprise']),
            'is_active': random.choice([True, True, True, False]),
            'lifetime_value': round(random.uniform(0, 5000), 2)
        })

    # Write CSV
    csv_file = OUTPUT_DIR / 'users-sample.csv'
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=users[0].keys())
        writer.writeheader()
        writer.writerows(users)

    print(f"✓ Created {csv_file} ({len(users)} rows)")
    return users


def generate_products():
    """Generate sample product catalog"""
    print("Generating products...")

    categories = ['Electronics', 'Clothing', 'Home & Garden', 'Sports',
                  'Books', 'Toys', 'Food & Beverage']

    products = []

    for i in range(NUM_PRODUCTS):
        products.append({
            'product_id': f'PROD{i+1:04d}',
            'name': f'Product {i+1}',
            'category': random.choice(categories),
            'price': round(random.uniform(9.99, 999.99), 2),
            'cost': 0,  # Will calculate
            'stock_quantity': random.randint(0, 1000),
            'rating': round(random.uniform(1, 5), 1),
            'num_reviews': random.randint(0, 5000),
            'is_featured': random.choice([True, False]),
            'created_at': (datetime(2023, 1, 1) + timedelta(days=random.randint(0, 365))).isoformat()
        })

        # Calculate cost (60-80% of price)
        products[-1]['cost'] = round(products[-1]['price'] * random.uniform(0.6, 0.8), 2)

    # Write JSON
    json_file = OUTPUT_DIR / 'products-sample.json'
    with open(json_file, 'w') as f:
        json.dump(products, f, indent=2)

    print(f"✓ Created {json_file} ({len(products)} products)")
    return products


def generate_summary():
    """Generate summary statistics"""
    print("\nGenerating summary...")

    summary = {
        'generated_at': datetime.now().isoformat(),
        'datasets': {
            'transactions': {
                'file': 'transactions-sample.csv',
                'rows': NUM_TRANSACTIONS,
                'columns': 12,
                'format': 'CSV',
                'size_mb': 1.2
            },
            'logs': {
                'file': 'logs-sample.jsonl',
                'events': 50000,
                'format': 'JSON Lines',
                'size_mb': 8.5
            },
            'users': {
                'file': 'users-sample.csv',
                'rows': NUM_USERS,
                'columns': 9,
                'format': 'CSV',
                'size_mb': 0.08
            },
            'products': {
                'file': 'products-sample.json',
                'products': NUM_PRODUCTS,
                'format': 'JSON',
                'size_mb': 0.05
            }
        },
        'usage': {
            'description': 'Synthetic datasets for Module 01 exercises',
            'scenarios': [
                'S3 upload/download operations',
                'Data format conversion (CSV → Parquet)',
                'Partitioning strategies',
                'Compression analysis',
                'Schema evolution testing'
            ]
        }
    }

    summary_file = OUTPUT_DIR / 'README.md'
    with open(summary_file, 'w') as f:
        f.write('# Sample Datasets\n\n')
        f.write('Synthetic datasets generated for Module 01 exercises.\n\n')
        f.write('## Files\n\n')
        for name, info in summary['datasets'].items():
            f.write(f"### {info['file']}\n")
            f.write(f"- **Format:** {info['format']}\n")
            f.write(f"- **Size:** ~{info['size_mb']} MB\n")
            if 'rows' in info:
                f.write(f"- **Rows:** {info['rows']:,}\n")
            f.write('\n')

        f.write('## Usage\n\n')
        f.write('These datasets are used in:\n\n')
        for scenario in summary['usage']['scenarios']:
            f.write(f"- {scenario}\n")

        f.write('\n## Regenerate\n\n')
        f.write('```bash\n')
        f.write('python3 generate_sample_data.py\n')
        f.write('```\n')

    print(f"✓ Created {summary_file}")


def main():
    print("=" * 60)
    print("Sample Data Generator for Module 01")
    print("=" * 60)
    print()

    generate_transactions()
    generate_logs()
    generate_users()
    generate_products()
    generate_summary()

    print()
    print("=" * 60)
    print("✓ All sample datasets generated successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
