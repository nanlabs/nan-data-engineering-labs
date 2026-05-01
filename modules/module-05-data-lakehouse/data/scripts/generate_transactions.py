#!/usr/bin/env python3
"""
Generate synthetic e-commerce transaction data with intentional quality issues.

This script generates realistic transaction data for practicing data lakehouse
patterns, including the Bronze → Silver → Gold medallion architecture.

Quality issues included (10-15%):
- Missing required fields (nulls)
- Duplicate transaction_ids
- Invalid formats (malformed IDs, dates)
- Inconsistent calculations (total != price * quantity)
- Outliers (negative prices, future dates)
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from faker import Faker

# Initialize Faker
fake = Faker()
Faker.seed(42)  # For reproducibility
random.seed(42)

# Constants
NUM_RECORDS = 300000  # 300K transactions
QUALITY_ISSUE_RATE = 0.12  # 12% of records have issues
OUTPUT_DIR = Path(__file__).parent.parent / "raw"
OUTPUT_FILE = OUTPUT_DIR / "transactions.json"

# Product categories and names
CATEGORIES = {
    "Electronics": ["Laptop", "Smartphone", "Tablet", "Headphones", "Smart Watch", "Camera", "Monitor", "Keyboard"],
    "Clothing": ["T-Shirt", "Jeans", "Dress", "Jacket", "Shoes", "Hat", "Sweater", "Socks"],
    "Home & Garden": ["Sofa", "Table", "Lamp", "Rug", "Plant", "Curtains", "Mirror", "Cushion"],
    "Books": ["Fiction Novel", "Cookbook", "Biography", "Self-Help", "Textbook", "Comic", "Magazine", "Dictionary"],
    "Sports": ["Running Shoes", "Yoga Mat", "Dumbbells", "Tennis Racket", "Basketball", "Bicycle", "Helmet", "Jump Rope"],
    "Toys": ["Action Figure", "Puzzle", "Board Game", "Doll", "LEGO Set", "RC Car", "Stuffed Animal", "Building Blocks"],
    "Food & Beverage": ["Coffee", "Tea", "Snacks", "Chocolate", "Wine", "Juice", "Pasta", "Cereal"],
    "Beauty": ["Shampoo", "Moisturizer", "Lipstick", "Perfume", "Sunscreen", "Face Mask", "Nail Polish", "Soap"],
    "Automotive": ["Car Wax", "Floor Mats", "Phone Mount", "Air Freshener", "Jump Starter", "Tool Kit", "Tire Gauge", "Dash Cam"],
    "Other": ["Gift Card", "Subscription", "Service", "Warranty", "Insurance", "Membership", "Voucher", "Coupon"]
}

PAYMENT_METHODS = ["credit_card", "debit_card", "paypal", "apple_pay", "google_pay", "bank_transfer", "cash"]
STATUSES = ["completed", "pending", "cancelled", "refunded", "failed"]
DEVICE_TYPES = ["desktop", "mobile", "tablet"]
BROWSERS = ["Chrome", "Firefox", "Safari", "Edge", "Other"]


def generate_user_id() -> str:
    """Generate user ID in format U0000123456."""
    return f"U{random.randint(0, 9999999999):010d}"


def generate_product_id() -> str:
    """Generate product ID in format P00012345."""
    return f"P{random.randint(0, 99999999):08d}"


def generate_clean_transaction() -> Dict:
    """Generate a clean, valid transaction record."""
    category = random.choice(list(CATEGORIES.keys()))
    product_name = random.choice(CATEGORIES[category])
    price = round(random.uniform(5.0, 999.99), 2)
    quantity = random.randint(1, 10)
    total_amount = round(price * quantity, 2)
    
    # Generate timestamp within last 90 days
    days_ago = random.randint(0, 90)
    hours = random.randint(0, 23)
    minutes = random.randint(0, 59)
    seconds = random.randint(0, 59)
    timestamp = datetime.now() - timedelta(days=days_ago, hours=hours, minutes=minutes, seconds=seconds)
    
    return {
        "transaction_id": str(uuid.uuid4()),
        "user_id": generate_user_id(),
        "product_id": generate_product_id(),
        "product_name": product_name,
        "category": category,
        "price": price,
        "quantity": quantity,
        "total_amount": total_amount,
        "payment_method": random.choice(PAYMENT_METHODS),
        "status": random.choice(STATUSES),
        "timestamp": timestamp.isoformat() + "Z",
        "country": fake.country_code(),
        "city": fake.city(),
        "ip_address": fake.ipv4(),
        "device_type": random.choice(DEVICE_TYPES),
        "browser": random.choice(BROWSERS)
    }


def inject_quality_issue(transaction: Dict, issue_type: str) -> Dict:
    """Inject a specific quality issue into a transaction."""
    
    if issue_type == "missing_required":
        # Remove a required field
        required_fields = ["user_id", "product_id", "price", "quantity", "timestamp"]
        field_to_remove = random.choice(required_fields)
        transaction[field_to_remove] = None
        
    elif issue_type == "invalid_format_id":
        # Malformed ID
        if random.choice([True, False]):
            transaction["user_id"] = f"INVALID{random.randint(1000, 9999)}"
        else:
            transaction["product_id"] = f"BAD{random.randint(100, 999)}"
            
    elif issue_type == "invalid_timestamp":
        # Future date or malformed
        if random.choice([True, False]):
            # Future date
            future = datetime.now() + timedelta(days=random.randint(1, 365))
            transaction["timestamp"] = future.isoformat() + "Z"
        else:
            # Malformed
            transaction["timestamp"] = "2024-13-45T25:99:99Z"  # Invalid date
            
    elif issue_type == "negative_price":
        # Negative price
        transaction["price"] = -round(random.uniform(1.0, 100.0), 2)
        transaction["total_amount"] = transaction["price"] * transaction["quantity"]
        
    elif issue_type == "inconsistent_total":
        # total_amount doesn't match price * quantity
        transaction["total_amount"] = round(random.uniform(1.0, 5000.0), 2)
        
    elif issue_type == "duplicate_id":
        # This will be handled separately to create actual duplicates
        pass
    
    elif issue_type == "missing_optional":
        # Remove optional fields
        optional_fields = ["product_name", "category", "city", "browser", "device_type"]
        for _ in range(random.randint(1, 3)):
            field = random.choice(optional_fields)
            transaction[field] = None
            
    elif issue_type == "outlier_quantity":
        # Unrealistic quantity
        transaction["quantity"] = random.randint(1000, 10000)
        transaction["total_amount"] = round(transaction["price"] * transaction["quantity"], 2)
        
    elif issue_type == "empty_string":
        # Empty strings instead of proper values
        string_fields = ["product_name", "category", "city"]
        field = random.choice(string_fields)
        transaction[field] = ""
    
    return transaction


def generate_all_transactions() -> List[Dict]:
    """Generate all transactions with quality issues."""
    print(f"🏭 Generating {NUM_RECORDS:,} transactions...")
    
    transactions = []
    issue_types = [
        "missing_required",
        "invalid_format_id",
        "invalid_timestamp",
        "negative_price",
        "inconsistent_total",
        "missing_optional",
        "outlier_quantity",
        "empty_string"
    ]
    
    # Generate clean records
    num_clean = int(NUM_RECORDS * (1 - QUALITY_ISSUE_RATE))
    num_issues = NUM_RECORDS - num_clean
    
    print(f"  ✅ Clean records: {num_clean:,} ({(1-QUALITY_ISSUE_RATE)*100:.1f}%)")
    print(f"  ⚠️  Records with issues: {num_issues:,} ({QUALITY_ISSUE_RATE*100:.1f}%)")
    
    # Generate clean transactions
    for i in range(num_clean):
        transactions.append(generate_clean_transaction())
        if (i + 1) % 50000 == 0:
            print(f"     Generated {i + 1:,} clean records...")
    
    # Generate transactions with issues
    for i in range(num_issues):
        transaction = generate_clean_transaction()
        issue_type = random.choice(issue_types)
        transaction = inject_quality_issue(transaction, issue_type)
        transactions.append(transaction)
        if (i + 1) % 10000 == 0:
            print(f"     Generated {i + 1:,} records with issues...")
    
    # Add some duplicates (3% of records)
    num_duplicates = int(NUM_RECORDS * 0.03)
    print(f"  🔁 Adding {num_duplicates:,} duplicate records...")
    for _ in range(num_duplicates):
        duplicate = random.choice(transactions).copy()
        transactions.append(duplicate)
    
    # Shuffle to mix clean and dirty records
    random.shuffle(transactions)
    
    return transactions


def save_transactions(transactions: List[Dict]):
    """Save transactions to JSON file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"\n💾 Saving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        for transaction in transactions:
            f.write(json.dumps(transaction) + '\n')
    
    file_size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)
    print(f"✅ Saved {len(transactions):,} transactions ({file_size_mb:.2f} MB)")


def print_summary(transactions: List[Dict]):
    """Print summary statistics."""
    print("\n" + "=" * 60)
    print("📊 SUMMARY STATISTICS")
    print("=" * 60)
    
    # Count records by status
    status_counts = {}
    for t in transactions:
        status = t.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print("\nRecords by status:")
    for status, count in sorted(status_counts.items(), key=lambda x: -x[1]):
        pct = (count / len(transactions)) * 100
        print(f"  {status:15s}: {count:8,} ({pct:5.2f}%)")
    
    # Count nulls
    null_count = sum(1 for t in transactions if any(v is None for v in t.values()))
    print(f"\nRecords with null values: {null_count:,} ({null_count/len(transactions)*100:.2f}%)")
    
    # Count potential duplicates
    transaction_ids = [t.get("transaction_id") for t in transactions if t.get("transaction_id")]
    duplicate_count = len(transaction_ids) - len(set(transaction_ids))
    print(f"Duplicate transaction_ids: {duplicate_count:,}")
    
    print("\n" + "=" * 60)


def main():
    """Main execution."""
    print("=" * 60)
    print("🏭 E-COMMERCE TRANSACTIONS DATA GENERATOR")
    print("=" * 60)
    print(f"\nTarget records: {NUM_RECORDS:,}")
    print(f"Quality issue rate: {QUALITY_ISSUE_RATE*100:.1f}%")
    print(f"Output: {OUTPUT_FILE}")
    print()
    
    # Generate transactions
    transactions = generate_all_transactions()
    
    # Save to file
    save_transactions(transactions)
    
    # Print summary
    print_summary(transactions)
    
    print("\n✅ Transaction data generation complete!")
    print("\n💡 Next steps:")
    print("   1. Inspect the data: head -n 5 data/raw/transactions.json")
    print("   2. Load into Bronze layer with PySpark")
    print("   3. Clean and validate for Silver layer")
    print("   4. Aggregate for Gold layer metrics")


if __name__ == "__main__":
    main()
