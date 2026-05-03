#!/usr/bin/env python3
"""
Generate sample datasets for Databricks Lakehouse training exercises.

This script creates realistic sample data for:
- Customers (10,000 records)
- Orders (50,000 records)
- Products (1,000 records)
- Events (100,000 records) - for streaming
- IoT Sensors (200,000 records) - for streaming

Usage:
    python create_sample_data.py --output-dir ./data/sample --format parquet
"""

import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path

try:
    import pandas as pd
    import numpy as np
except ImportError:
    print("ERROR: Required packages not installed.")
    print("Install with: pip install pandas numpy")
    exit(1)

# Faker for realistic data
try:
    from faker import Faker
except ImportError:
    print("ERROR: faker package not installed.")
    print("Install with: pip install faker")
    exit(1)

fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)


def generate_customers(n=10000):
    """Generate customer dimension data."""
    print(f"Generating {n:,} customers...")

    countries = ["USA", "Canada", "UK", "Germany", "France", "Australia", "Brazil", "India"]
    tiers = ["bronze", "silver", "gold", "platinum"]

    customers = []
    for i in range(1, n + 1):
        country = random.choice(countries)
        signup_date = fake.date_between(start_date="-3y", end_date="today")

        customers.append({
            "customer_id": i,
            "email": fake.email(),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "phone": fake.phone_number(),
            "country": country,
            "city": fake.city(),
            "address": fake.street_address(),
            "postal_code": fake.postcode(),
            "signup_date": signup_date.strftime("%Y-%m-%d"),
            "tier": random.choice(tiers),
            "lifetime_value": round(random.uniform(100, 10000), 2),
            "is_active": random.choice([True, True, True, False]),  # 75% active
            "created_at": (signup_date - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    df = pd.DataFrame(customers)
    print(f"✅ Generated {len(df):,} customer records")
    return df


def generate_products(n=1000):
    """Generate product catalog data."""
    print(f"Generating {n:,} products...")

    categories = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books", "Toys", "Food"]
    brands = ["BrandA", "BrandB", "BrandC", "BrandD", "BrandE"]

    products = []
    for i in range(1, n + 1):
        products.append({
            "product_id": i,
            "product_name": fake.bs().title(),
            "category": random.choice(categories),
            "brand": random.choice(brands),
            "price": round(random.uniform(10, 1000), 2),
            "cost": round(random.uniform(5, 500), 2),
            "stock_quantity": random.randint(0, 1000),
            "rating": round(random.uniform(1, 5), 1),
            "num_reviews": random.randint(0, 500),
            "is_available": random.choice([True, True, True, False]),
            "created_at": fake.date_between(start_date="-2y", end_date="today").strftime("%Y-%m-%d %H:%M:%S")
        })

    df = pd.DataFrame(products)
    print(f"✅ Generated {len(df):,} product records")
    return df


def generate_orders(n=50000, customers_df=None, products_df=None):
    """Generate orders fact table."""
    print(f"Generating {n:,} orders...")

    if customers_df is None or products_df is None:
        raise ValueError("customers_df and products_df are required")

    customer_ids = customers_df["customer_id"].tolist()
    product_ids = products_df["product_id"].tolist()
    statuses = ["completed", "completed", "completed", "pending", "cancelled"]

    orders = []
    for i in range(1, n + 1):
        order_date = fake.date_time_between(start_date="-1y", end_date="now")
        num_items = random.randint(1, 5)

        order_products = random.sample(product_ids, min(num_items, len(product_ids)))
        total_amount = sum([
            products_df[products_df["product_id"] == pid]["price"].iloc[0]
            for pid in order_products
        ])

        orders.append({
            "order_id": i,
            "customer_id": random.choice(customer_ids),
            "order_date": order_date.strftime("%Y-%m-%d"),
            "order_timestamp": order_date.strftime("%Y-%m-%d %H:%M:%S"),
            "total_amount": round(total_amount, 2),
            "num_items": num_items,
            "status": random.choice(statuses),
            "payment_method": random.choice(["credit_card", "debit_card", "paypal", "bitcoin"]),
            "shipping_country": random.choice(["USA", "Canada", "UK", "Germany"]),
            "created_at": order_date.strftime("%Y-%m-%d %H:%M:%S")
        })

    df = pd.DataFrame(orders)
    print(f"✅ Generated {len(df):,} order records")
    return df


def generate_events(n=100000):
    """Generate clickstream events for streaming exercise."""
    print(f"Generating {n:,} events...")

    event_types = ["page_view", "page_view", "page_view", "add_to_cart", "purchase", "search"]
    devices = ["desktop", "mobile", "tablet"]
    browsers = ["chrome", "firefox", "safari", "edge"]

    events = []
    base_time = datetime.now() - timedelta(days=7)

    for i in range(1, n + 1):
        event_time = base_time + timedelta(seconds=random.randint(0, 7*24*3600))

        events.append({
            "event_id": i,
            "user_id": random.randint(1, 10000),
            "session_id": fake.uuid4(),
            "event_type": random.choice(event_types),
            "event_timestamp": event_time.strftime("%Y-%m-%d %H:%M:%S"),
            "page_url": f"/products/{random.randint(1, 1000)}",
            "device_type": random.choice(devices),
            "browser": random.choice(browsers),
            "country": random.choice(["USA", "Canada", "UK", "Germany", "France"]),
            "session_duration_sec": random.randint(10, 3600),
            "created_at": event_time.strftime("%Y-%m-%d %H:%M:%S")
        })

    df = pd.DataFrame(events)
    print(f"✅ Generated {len(df):,} event records")
    return df


def generate_iot_sensors(n=200000):
    """Generate IoT sensor data for streaming analytics."""
    print(f"Generating {n:,} IoT sensor readings...")

    sensor_ids = [f"sensor_{i:04d}" for i in range(1, 101)]  # 100 sensors
    sensor_types = ["temperature", "humidity", "pressure", "vibration"]
    locations = ["factory_a", "factory_b", "warehouse_north", "warehouse_south"]

    readings = []
    base_time = datetime.now() - timedelta(days=1)

    for i in range(1, n + 1):
        reading_time = base_time + timedelta(seconds=random.randint(0, 24*3600))
        sensor_type = random.choice(sensor_types)

        # Generate realistic sensor values based on type
        if sensor_type == "temperature":
            value = round(random.uniform(15, 35), 2)  # Celsius
        elif sensor_type == "humidity":
            value = round(random.uniform(30, 80), 2)  # Percentage
        elif sensor_type == "pressure":
            value = round(random.uniform(980, 1020), 2)  # hPa
        else:  # vibration
            value = round(random.uniform(0, 5), 2)  # mm/s

        readings.append({
            "reading_id": i,
            "sensor_id": random.choice(sensor_ids),
            "sensor_type": sensor_type,
            "location": random.choice(locations),
            "value": value,
            "unit": {"temperature": "celsius", "humidity": "percent", "pressure": "hpa", "vibration": "mm_s"}[sensor_type],
            "reading_timestamp": reading_time.strftime("%Y-%m-%d %H:%M:%S"),
            "is_anomaly": random.choice([False] * 95 + [True] * 5),  # 5% anomalies
            "created_at": reading_time.strftime("%Y-%m-%d %H:%M:%S")
        })

    df = pd.DataFrame(readings)
    print(f"✅ Generated {len(df):,} IoT sensor readings")
    return df


def save_dataset(df, name, output_dir, file_format="parquet"):
    """Save dataset to specified format."""
    output_path = Path(output_dir) / name
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if file_format == "parquet":
        file_path = f"{output_path}.parquet"
        df.to_parquet(file_path, index=False)
    elif file_format == "csv":
        file_path = f"{output_path}.csv"
        df.to_csv(file_path, index=False)
    elif file_format == "json":
        file_path = f"{output_path}.json"
        df.to_json(file_path, orient="records", lines=True)
    else:
        raise ValueError(f"Unsupported format: {file_format}")

    print(f"💾 Saved {name} to {file_path} ({df.memory_usage(deep=True).sum() / 1024**2:.2f} MB)")


def generate_all_datasets(output_dir="./data/sample", file_format="parquet"):
    """Generate all sample datasets."""
    print("\n" + "="*60)
    print("Databricks Lakehouse - Sample Data Generator")
    print("="*60 + "\n")

    # Generate datasets
    customers_df = generate_customers(n=10000)
    products_df = generate_products(n=1000)
    orders_df = generate_orders(n=50000, customers_df=customers_df, products_df=products_df)
    events_df = generate_events(n=100000)
    iot_sensors_df = generate_iot_sensors(n=200000)

    # Save datasets
    print("\n" + "-"*60)
    print("Saving datasets...")
    print("-"*60 + "\n")

    save_dataset(customers_df, "customers", output_dir, file_format)
    save_dataset(products_df, "products", output_dir, file_format)
    save_dataset(orders_df, "orders", output_dir, file_format)
    save_dataset(events_df, "events", output_dir, file_format)
    save_dataset(iot_sensors_df, "iot_sensors", output_dir, file_format)

    # Generate summary
    total_rows = sum([len(df) for df in [customers_df, products_df, orders_df, events_df, iot_sensors_df]])
    total_size = sum([df.memory_usage(deep=True).sum() for df in [customers_df, products_df, orders_df, events_df, iot_sensors_df]]) / 1024**2

    print("\n" + "="*60)
    print("Generation Complete!")
    print("="*60)
    print(f"📊 Total records: {total_rows:,}")
    print(f"💾 Total size: {total_size:.2f} MB")
    print(f"📁 Output directory: {output_dir}")
    print(f"📄 Format: {file_format}")
    print("\nDatasets:")
    print(f"  - customers: {len(customers_df):,} records")
    print(f"  - products: {len(products_df):,} records")
    print(f"  - orders: {len(orders_df):,} records")
    print(f"  - events: {len(events_df):,} records")
    print(f"  - iot_sensors: {len(iot_sensors_df):,} records")
    print("\n✅ Ready to upload to Databricks DBFS!")
    print("\nUpload command:")
    print(f"  databricks fs cp -r {output_dir} dbfs:/FileStore/training/")


def main():
    parser = argparse.ArgumentParser(description="Generate sample datasets for Databricks training")
    parser.add_argument("--output-dir", default="./data/sample", help="Output directory for datasets")
    parser.add_argument("--format", choices=["parquet", "csv", "json"], default="parquet", help="Output format")
    parser.add_argument("--customers", type=int, default=10000, help="Number of customers to generate")
    parser.add_argument("--products", type=int, default=1000, help="Number of products to generate")
    parser.add_argument("--orders", type=int, default=50000, help="Number of orders to generate")
    parser.add_argument("--events", type=int, default=100000, help="Number of events to generate")
    parser.add_argument("--iot-sensors", type=int, default=200000, help="Number of IoT sensor readings")

    args = parser.parse_args()

    generate_all_datasets(
        output_dir=args.output_dir,
        file_format=args.format
    )


if __name__ == "__main__":
    main()
