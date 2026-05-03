#!/usr/bin/env python3
"""
Generate sample data for Module 18: Advanced Architectures

This script generates sample datasets for all exercises:
- Event Store events (CQRS/Event Sourcing)
- Streaming events (Kappa Architecture)
- Batch transactions (Lambda Architecture)
- Domain data (Data Mesh)
"""

import json
import random
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd

# --- Configuration ---
DEFAULT_EVENTS = 50
DEFAULT_TRANSACTIONS = 10000
DEFAULT_PRODUCTS = 500
DEFAULT_CUSTOMERS = 200
DEFAULT_ORDERS = 1000

# --- Helper Functions ---

def generate_timestamp(start_date: datetime, days_offset: int = 0, hours_offset: int = 0) -> str:
    """Generate ISO 8601 timestamp"""
    ts = start_date + timedelta(days=days_offset, hours=hours_offset)
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


# --- Event Store (CQRS) ---

def generate_event_store_data(num_events: int = DEFAULT_EVENTS) -> List[Dict[str, Any]]:
    """Generate sample events for Event Sourcing"""
    events = []
    event_types = [
        ("OrderPlaced", 0.3),
        ("PaymentProcessed", 0.25),
        ("OrderShipped", 0.2),
        ("OrderDelivered", 0.15),
        ("OrderCancelled", 0.1)
    ]

    start_date = datetime(2024, 1, 1)
    aggregate_ids = [f"ORD_{i:06d}" for i in range(1, num_events // 3 + 1)]

    for i in range(num_events):
        # Weighted random event type
        event_type = random.choices(
            [e[0] for e in event_types],
            weights=[e[1] for e in event_types]
        )[0]

        aggregate_id = random.choice(aggregate_ids)
        days_offset = random.randint(0, 90)
        hours_offset = random.randint(0, 23)

        event = {
            "event_id": f"EVT_{i+1:08d}",
            "aggregate_id": aggregate_id,
            "event_type": event_type,
            "timestamp": generate_timestamp(start_date, days_offset, hours_offset),
            "version": random.randint(1, 5),
            "data": {}
        }

        # Event-specific data
        if event_type == "OrderPlaced":
            event["data"] = {
                "customer_id": f"CUST_{random.randint(1, 500):06d}",
                "items": [
                    {
                        "product_id": f"PROD_{random.randint(1, 1000):06d}",
                        "quantity": random.randint(1, 5),
                        "price": round(random.uniform(10.0, 500.0), 2)
                    }
                    for _ in range(random.randint(1, 3))
                ],
                "amount": round(random.uniform(50.0, 1000.0), 2),
                "currency": "USD"
            }
        elif event_type == "PaymentProcessed":
            event["data"] = {
                "payment_id": f"PAY_{i+1:08d}",
                "payment_method": random.choice(["credit_card", "paypal", "bank_transfer"]),
                "amount": round(random.uniform(50.0, 1000.0), 2),
                "status": "success"
            }
        elif event_type == "OrderShipped":
            event["data"] = {
                "shipment_id": f"SHIP_{i+1:08d}",
                "carrier": random.choice(["FedEx", "UPS", "DHL", "USPS"]),
                "tracking_number": f"TRACK{random.randint(10000000, 99999999)}"
            }
        elif event_type == "OrderDelivered":
            event["data"] = {
                "delivery_time": generate_timestamp(start_date, days_offset + random.randint(2, 7)),
                "signature": random.choice([True, False])
            }
        elif event_type == "OrderCancelled":
            event["data"] = {
                "reason": random.choice([
                    "customer_request",
                    "payment_failed",
                    "out_of_stock",
                    "fraud_detected"
                ]),
                "refund_amount": round(random.uniform(50.0, 1000.0), 2)
            }

        events.append(event)

    # Sort by timestamp
    events.sort(key=lambda e: e["timestamp"])
    return events


# --- Kinesis Stream Events (Kappa) ---

def generate_kinesis_events(num_events: int = 100) -> List[Dict[str, Any]]:
    """Generate sample streaming events"""
    events = []
    event_types = [
        ("page_view", 0.5),
        ("click", 0.3),
        ("purchase", 0.15),
        ("add_to_cart", 0.05)
    ]

    start_date = datetime(2024, 1, 15)

    for i in range(num_events):
        event_type = random.choices(
            [e[0] for e in event_types],
            weights=[e[1] for e in event_types]
        )[0]

        minutes_offset = i * 5

        event = {
            "event_id": f"EVT_{i+1:08d}",
            "user_id": f"USER_{random.randint(1, 100):06d}",
            "event_type": event_type,
            "timestamp": generate_timestamp(start_date, hours_offset=minutes_offset // 60),
            "session_id": f"SESS_{random.randint(1, 50):08d}",
            "metadata": {}
        }

        # Event-specific metadata
        if event_type == "page_view":
            event["metadata"] = {
                "page": random.choice(["/home", "/products", "/cart", "/checkout"]),
                "duration_seconds": random.randint(5, 300),
                "referrer": random.choice(["google", "facebook", "direct", "email"])
            }
        elif event_type == "click":
            event["metadata"] = {
                "element": random.choice(["banner", "product", "button", "link"]),
                "coordinates": {
                    "x": random.randint(0, 1920),
                    "y": random.randint(0, 1080)
                }
            }
        elif event_type == "purchase":
            event["metadata"] = {
                "product_id": f"PROD_{random.randint(1, 1000):06d}",
                "amount": round(random.uniform(10.0, 500.0), 2),
                "payment_method": random.choice(["credit_card", "paypal", "apple_pay"])
            }
        elif event_type == "add_to_cart":
            event["metadata"] = {
                "product_id": f"PROD_{random.randint(1, 1000):06d}",
                "quantity": random.randint(1, 5)
            }

        events.append(event)

    return events


# --- Batch Data (Lambda) ---

def generate_batch_data(num_transactions: int = DEFAULT_TRANSACTIONS) -> pd.DataFrame:
    """Generate sample batch transactions"""
    start_date = datetime(2024, 1, 1)

    data = {
        "transaction_id": range(1, num_transactions + 1),
        "user_id": [random.randint(1, 10000) for _ in range(num_transactions)],
        "product_id": [random.randint(1, 1000) for _ in range(num_transactions)],
        "amount": [round(random.uniform(5.0, 500.0), 2) for _ in range(num_transactions)],
        "timestamp": [
            generate_timestamp(start_date, days_offset=random.randint(0, 90))
            for _ in range(num_transactions)
        ],
        "country": [
            random.choice(["US", "GB", "DE", "FR", "ES", "IT", "JP", "AU", "CA", "BR"])
            for _ in range(num_transactions)
        ],
        "status": [
            random.choices(
                ["completed", "pending", "failed", "refunded"],
                weights=[0.85, 0.08, 0.05, 0.02]
            )[0]
            for _ in range(num_transactions)
        ]
    }

    return pd.DataFrame(data)


# --- Data Mesh Domains ---

def generate_product_catalog(num_products: int = DEFAULT_PRODUCTS) -> List[Dict[str, Any]]:
    """Generate product catalog (Product Domain)"""
    categories = ["Electronics", "Clothing", "Home & Garden", "Books", "Sports", "Toys"]

    products = []
    for i in range(1, num_products + 1):
        product = {
            "product_id": f"PROD_{i:06d}",
            "name": f"Product {i}",
            "category": random.choice(categories),
            "price": round(random.uniform(10.0, 1000.0), 2),
            "stock": random.randint(0, 500),
            "supplier_id": f"SUP_{random.randint(1, 50):04d}",
            "rating": round(random.uniform(1.0, 5.0), 1),
            "reviews_count": random.randint(0, 1000)
        }
        products.append(product)

    return products


def generate_customer_profiles(num_customers: int = DEFAULT_CUSTOMERS) -> List[Dict[str, Any]]:
    """Generate customer profiles (Customer Domain)"""
    segments = ["Premium", "Standard", "New", "Churned"]
    countries = ["US", "GB", "DE", "FR", "ES", "IT", "JP", "AU", "CA", "BR"]

    customers = []
    for i in range(1, num_customers + 1):
        customer = {
            "customer_id": f"CUST_{i:06d}",
            "name": f"Customer {i}",
            "email": f"customer{i}@example.com",
            "country": random.choice(countries),
            "lifetime_value": round(random.uniform(100.0, 10000.0), 2),
            "segment": random.choice(segments),
            "registration_date": generate_timestamp(
                datetime(2020, 1, 1),
                days_offset=random.randint(0, 1460)
            ),
            "orders_count": random.randint(0, 100)
        }
        customers.append(customer)

    return customers


def generate_sales_orders(num_orders: int = DEFAULT_ORDERS) -> List[Dict[str, Any]]:
    """Generate sales orders (Sales Domain)"""
    start_date = datetime(2024, 1, 1)

    orders = []
    for i in range(1, num_orders + 1):
        order = {
            "order_id": f"ORD_{i:06d}",
            "customer_id": f"CUST_{random.randint(1, 500):06d}",
            "product_id": f"PROD_{random.randint(1, 1000):06d}",
            "quantity": random.randint(1, 10),
            "amount": round(random.uniform(50.0, 2000.0), 2),
            "order_date": generate_timestamp(start_date, days_offset=random.randint(0, 90)),
            "status": random.choices(
                ["completed", "pending", "cancelled"],
                weights=[0.8, 0.15, 0.05]
            )[0]
        }
        orders.append(order)

    return orders


# --- Main Generation Function ---

def save_json_lines(data: List[Dict[str, Any]], filepath: Path):
    """Save data as JSON Lines format"""
    with open(filepath, 'w') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')
    print(f"✅ Generated: {filepath} ({len(data)} records)")


def main():
    parser = argparse.ArgumentParser(description="Generate sample data for Module 18")
    parser.add_argument('--events', type=int, default=DEFAULT_EVENTS, help='Number of event store events')
    parser.add_argument('--transactions', type=int, default=DEFAULT_TRANSACTIONS, help='Number of batch transactions')
    parser.add_argument('--products', type=int, default=DEFAULT_PRODUCTS, help='Number of products')
    parser.add_argument('--customers', type=int, default=DEFAULT_CUSTOMERS, help='Number of customers')
    parser.add_argument('--orders', type=int, default=DEFAULT_ORDERS, help='Number of sales orders')
    parser.add_argument('--exercise', type=str, choices=['lambda', 'kappa', 'mesh', 'cqrs', 'all'], default='all', help='Generate data for specific exercise')
    parser.add_argument('--output', type=str, default=None, help='Output directory (default: data/sample/)')

    args = parser.parse_args()

    # Determine output directory
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = Path(__file__).parent

    output_dir.mkdir(parents=True, exist_ok=True)

    print("📦 Generating sample data for Module 18")
    print(f"📁 Output directory: {output_dir}")
    print("")

    # Generate Event Store data (CQRS)
    if args.exercise in ['cqrs', 'all']:
        events = generate_event_store_data(args.events)
        save_json_lines(events, output_dir / 'event-store-sample.json')

    # Generate Kinesis events (Kappa)
    if args.exercise in ['kappa', 'all']:
        kinesis_events = generate_kinesis_events(100)
        save_json_lines(kinesis_events, output_dir / 'kinesis-stream-events.json')

    # Generate batch data (Lambda)
    if args.exercise in ['lambda', 'all']:
        batch_df = generate_batch_data(args.transactions)
        batch_file = output_dir / 'batch-data-sample.parquet'
        batch_df.to_parquet(batch_file, index=False)
        print(f"✅ Generated: {batch_file} ({len(batch_df)} records)")

    # Generate Data Mesh domains
    if args.exercise in ['mesh', 'all']:
        products = generate_product_catalog(args.products)
        save_json_lines(products, output_dir / 'domain-products-sample.json')

        customers = generate_customer_profiles(args.customers)
        save_json_lines(customers, output_dir / 'domain-customer-sample.json')

        orders = generate_sales_orders(args.orders)
        save_json_lines(orders, output_dir / 'domain-sales-sample.json')

    print("")
    print("✨ Done! All sample data generated successfully.")


if __name__ == "__main__":
    main()
