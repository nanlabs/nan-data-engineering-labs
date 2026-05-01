#!/usr/bin/env python3
"""
Generate synthetic product data for ETL exercises.
"""
import pandas as pd
from faker import Faker
import random
from pathlib import Path

fake = Faker()
random.seed(42)
Faker.seed(42)

def generate_products(n_products=1000):
    """Generate synthetic product data."""
    products = []

    categories = ['electronics', 'clothing', 'books', 'home', 'sports']

    for i in range(1, n_products + 1):
        # Generate SKU (e.g., ELC-0001)
        category_code = random.choice(['ELC', 'CLO', 'BOO', 'HOM', 'SPO'])
        sku = f"{category_code}-{i:04d}"

        product = {
            'product_id': i,
            'sku': sku,
            'name': fake.catch_phrase(),
            'description': fake.text(max_nb_chars=200),
            'price': round(random.uniform(9.99, 999.99), 2),
            'category': random.choice(categories),
            'stock': random.randint(0, 1000),
            'supplier_id': random.randint(1, 50),
            'created_at': fake.date_time_between(start_date='-5y', end_date='now').isoformat(),
            'weight_kg': round(random.uniform(0.1, 50.0), 2),
            'dimensions_cm': f"{random.randint(10, 100)}x{random.randint(10, 100)}x{random.randint(5, 50)}"
        }
        products.append(product)

    return pd.DataFrame(products)

def main():
    """Generate and save product data."""
    output_dir = Path(__file__).parent.parent / 'raw'
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating products...")
    df_products = generate_products(1000)

    # CSV version
    csv_path = output_dir / 'products.csv'
    df_products.to_csv(csv_path, index=False)
    print(f"✓ Generated {len(df_products)} products → {csv_path}")

    # JSON version
    json_path = output_dir / 'products.json'
    df_products.to_json(json_path, orient='records', indent=2)
    print(f"✓ Generated JSON version → {json_path}")

    # Statistics
    print("\n📊 Statistics:")
    print(f"  Total products: {len(df_products)}")
    print(f"  Categories: {df_products['category'].nunique()}")
    print(f"  Average price: ${df_products['price'].mean():.2f}")
    print(f"  Total stock: {df_products['stock'].sum():,}")
    print("\n  Category distribution:")
    print(df_products['category'].value_counts().to_string())

if __name__ == '__main__':
    main()
