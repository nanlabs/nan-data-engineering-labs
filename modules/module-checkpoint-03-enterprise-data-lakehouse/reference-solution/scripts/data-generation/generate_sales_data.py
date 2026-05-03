#!/usr/bin/env python3
"""
Sales Data Generator for Enterprise Data Lakehouse
Generates synthetic sales domain data including orders, customers, products, and returns.
Writes data to S3 as Parquet files for efficient analytics.
"""

import argparse
import logging
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import json

import boto3
import pandas as pd
from faker import Faker
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SalesDataGenerator:
    """Generator for synthetic sales data."""

    PRODUCT_CATEGORIES = [
        'Electronics', 'Clothing', 'Home & Garden', 'Sports & Outdoors',
        'Books', 'Toys & Games', 'Health & Beauty', 'Automotive',
        'Food & Beverage', 'Pet Supplies', 'Office Supplies', 'Jewelry'
    ]

    ORDER_STATUSES = ['PENDING', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED', 'RETURNED']

    PAYMENT_METHODS = ['CREDIT_CARD', 'DEBIT_CARD', 'PAYPAL', 'APPLE_PAY', 'GOOGLE_PAY', 'BANK_TRANSFER']

    SHIPPING_METHODS = ['STANDARD', 'EXPRESS', 'OVERNIGHT', 'INTERNATIONAL']

    CUSTOMER_SEGMENTS = ['PREMIUM', 'REGULAR', 'OCCASIONAL', 'NEW']

    RETURN_REASONS = [
        'Defective Product', 'Wrong Item', 'Not as Described', 'Changed Mind',
        'Better Price Found', 'Quality Issues', 'Size/Fit Issues', 'Late Delivery'
    ]

    def __init__(self, seed: Optional[int] = 42):
        """Initialize the generator with optional seed for reproducibility."""
        self.fake = Faker()
        if seed:
            Faker.seed(seed)
            random.seed(seed)

        self.products = []
        self.customers = []
        self.orders = []
        self.returns = []

    def generate_products(self, num_products: int = 1000) -> List[Dict]:
        """Generate product catalog data."""
        logger.info(f"Generating {num_products} products...")

        products = []

        for i in range(num_products):
            category = random.choice(self.PRODUCT_CATEGORIES)

            # Generate price based on category
            if category == 'Electronics':
                base_price = random.uniform(50, 2000)
            elif category == 'Jewelry':
                base_price = random.uniform(100, 5000)
            elif category == 'Clothing':
                base_price = random.uniform(20, 300)
            elif category == 'Books':
                base_price = random.uniform(10, 50)
            else:
                base_price = random.uniform(15, 500)

            cost = base_price * random.uniform(0.40, 0.70)

            product = {
                'product_id': f'PROD{i+1:06d}',
                'product_name': f"{self.fake.catch_phrase()} {category}",
                'category': category,
                'subcategory': f"{category} - {random.choice(['Premium', 'Standard', 'Budget'])}",
                'brand': self.fake.company(),
                'sku': self.fake.bothify(text='SKU-####-????').upper(),
                'description': self.fake.text(max_nb_chars=200),
                'unit_price': round(base_price, 2),
                'cost': round(cost, 2),
                'margin': round(base_price - cost, 2),
                'margin_pct': round(((base_price - cost) / base_price) * 100, 2),
                'weight_kg': round(random.uniform(0.1, 20.0), 2),
                'dimensions': f"{random.randint(10, 100)}x{random.randint(10, 100)}x{random.randint(5, 50)}",
                'stock_quantity': random.randint(0, 1000),
                'reorder_point': random.randint(10, 100),
                'supplier_id': f'SUP{random.randint(1, 200):04d}',
                'is_active': random.choices([True, False], weights=[0.90, 0.10])[0],
                'rating_avg': round(random.uniform(3.0, 5.0), 2),
                'review_count': random.randint(0, 5000),
                'created_at': self.fake.date_between(start_date='-5y', end_date='-6m').isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            products.append(product)

        self.products = products
        logger.info(f"Generated {len(products)} products")
        return products

    def generate_customers(self, num_customers: int = 50000) -> List[Dict]:
        """Generate customer data with demographics and purchase history."""
        logger.info(f"Generating {num_customers} customers...")

        customers = []

        for i in range(num_customers):
            # Registration date
            registration_date = self.fake.date_between(start_date='-5y', end_date='today')

            # Customer segment based on tenure and activity
            days_since_registration = (datetime.now().date() - registration_date).days
            if days_since_registration < 90:
                segment = 'NEW'
            else:
                segment = random.choices(
                    ['PREMIUM', 'REGULAR', 'OCCASIONAL'],
                    weights=[0.20, 0.50, 0.30]
                )[0]

            # Generate purchase history metrics
            if segment == 'PREMIUM':
                total_orders = random.randint(20, 100)
                total_spent = round(random.uniform(5000, 50000), 2)
            elif segment == 'REGULAR':
                total_orders = random.randint(5, 25)
                total_spent = round(random.uniform(1000, 10000), 2)
            elif segment == 'OCCASIONAL':
                total_orders = random.randint(1, 8)
                total_spent = round(random.uniform(100, 2000), 2)
            else:  # NEW
                total_orders = random.randint(0, 3)
                total_spent = round(random.uniform(0, 500), 2)

            avg_order_value = round(total_spent / total_orders, 2) if total_orders > 0 else 0.0

            # Demographics
            age = random.randint(18, 75)
            gender = random.choice(['Male', 'Female', 'Other', 'Prefer not to say'])

            customer = {
                'customer_id': f'CUST{i+1:08d}',
                'first_name': self.fake.first_name(),
                'last_name': self.fake.last_name(),
                'email': self.fake.email(),
                'phone': self.fake.phone_number(),
                'date_of_birth': self.fake.date_of_birth(minimum_age=age, maximum_age=age).isoformat(),
                'gender': gender,
                'registration_date': registration_date.isoformat(),
                'customer_segment': segment,
                'loyalty_points': random.randint(0, 10000) if segment in ['PREMIUM', 'REGULAR'] else 0,
                'loyalty_tier': random.choice(['BRONZE', 'SILVER', 'GOLD', 'PLATINUM']) if segment == 'PREMIUM' else 'NONE',
                'total_orders': total_orders,
                'total_spent': total_spent,
                'avg_order_value': avg_order_value,
                'last_order_date': self.fake.date_between(
                    start_date=registration_date,
                    end_date='today'
                ).isoformat() if total_orders > 0 else None,
                'preferred_payment_method': random.choice(self.PAYMENT_METHODS),
                'preferred_shipping_method': random.choice(self.SHIPPING_METHODS),
                'address_street': self.fake.street_address(),
                'address_city': self.fake.city(),
                'address_state': self.fake.state_abbr(),
                'address_zip': self.fake.zipcode(),
                'address_country': 'USA',
                'email_verified': random.choices([True, False], weights=[0.85, 0.15])[0],
                'marketing_opt_in': random.choices([True, False], weights=[0.60, 0.40])[0],
                'is_active': random.choices([True, False], weights=[0.85, 0.15])[0],
                'created_at': registration_date.isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            customers.append(customer)

        self.customers = customers
        logger.info(f"Generated {len(customers)} customers")
        return customers

    def generate_orders(
        self,
        num_orders: int = 200000,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Generate order data with line items."""
        logger.info(f"Generating {num_orders} orders...")

        if not self.products:
            logger.warning("No products generated. Generating products first.")
            self.generate_products()

        if not self.customers:
            logger.warning("No customers generated. Generating customers first.")
            self.generate_customers()

        if not start_date:
            start_date = datetime.now() - timedelta(days=365)
        if not end_date:
            end_date = datetime.now()

        orders = []

        for i in range(num_orders):
            # Select customer
            customer = random.choice(self.customers)

            # Generate order timestamp
            time_delta = end_date - start_date
            random_seconds = random.randint(0, int(time_delta.total_seconds()))
            order_date = start_date + timedelta(seconds=random_seconds)

            # Generate line items (1-5 products per order)
            num_items = random.choices([1, 2, 3, 4, 5], weights=[0.40, 0.30, 0.15, 0.10, 0.05])[0]
            order_items = random.sample(self.products, min(num_items, len(self.products)))

            subtotal = 0.0
            total_quantity = 0

            line_items = []
            for item_idx, product in enumerate(order_items, start=1):
                quantity = random.randint(1, 5)
                unit_price = product['unit_price']

                # Apply discounts randomly
                discount_pct = random.choices(
                    [0, 5, 10, 15, 20, 25],
                    weights=[0.60, 0.15, 0.10, 0.08, 0.05, 0.02]
                )[0]
                discount_amount = round(unit_price * quantity * (discount_pct / 100), 2)
                line_total = round(unit_price * quantity - discount_amount, 2)

                line_items.append({
                    'line_item_id': f"{i+1:010d}-{item_idx:02d}",
                    'product_id': product['product_id'],
                    'product_name': product['product_name'],
                    'category': product['category'],
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'discount_pct': discount_pct,
                    'discount_amount': discount_amount,
                    'line_total': line_total
                })

                subtotal += line_total
                total_quantity += quantity

            # Calculate shipping and tax
            shipping_method = random.choice(self.SHIPPING_METHODS)
            if shipping_method == 'STANDARD':
                shipping_cost = 5.99 if subtotal < 50 else 0.0
            elif shipping_method == 'EXPRESS':
                shipping_cost = 15.99
            elif shipping_method == 'OVERNIGHT':
                shipping_cost = 29.99
            else:  # INTERNATIONAL
                shipping_cost = round(random.uniform(25, 100), 2)

            tax_rate = random.uniform(0.06, 0.10)
            tax_amount = round(subtotal * tax_rate, 2)
            total_amount = round(subtotal + shipping_cost + tax_amount, 2)

            # Order status based on date
            days_since_order = (datetime.now() - order_date).days
            if days_since_order > 14:
                status = random.choices(
                    ['DELIVERED', 'CANCELLED', 'RETURNED'],
                    weights=[0.88, 0.08, 0.04]
                )[0]
            elif days_since_order > 7:
                status = random.choices(
                    ['DELIVERED', 'SHIPPED', 'CANCELLED'],
                    weights=[0.80, 0.15, 0.05]
                )[0]
            elif days_since_order > 2:
                status = random.choices(
                    ['SHIPPED', 'PROCESSING', 'CANCELLED'],
                    weights=[0.70, 0.25, 0.05]
                )[0]
            else:
                status = random.choices(
                    ['PROCESSING', 'PENDING', 'CANCELLED'],
                    weights=[0.70, 0.25, 0.05]
                )[0]

            order = {
                'order_id': f'ORD{i+1:010d}',
                'customer_id': customer['customer_id'],
                'order_date': order_date.isoformat(),
                'order_status': status,
                'payment_method': random.choice(self.PAYMENT_METHODS),
                'payment_status': 'PAID' if status not in ['PENDING', 'CANCELLED'] else 'PENDING',
                'shipping_method': shipping_method,
                'subtotal': round(subtotal, 2),
                'tax_amount': tax_amount,
                'shipping_cost': shipping_cost,
                'total_amount': total_amount,
                'total_quantity': total_quantity,
                'currency': 'USD',
                'shipping_address': {
                    'street': customer['address_street'],
                    'city': customer['address_city'],
                    'state': customer['address_state'],
                    'zip': customer['address_zip'],
                    'country': customer['address_country']
                },
                'billing_address': {
                    'street': customer['address_street'],
                    'city': customer['address_city'],
                    'state': customer['address_state'],
                    'zip': customer['address_zip'],
                    'country': customer['address_country']
                },
                'line_items': line_items,
                'tracking_number': self.fake.bothify(text='TRK##########') if status in ['SHIPPED', 'DELIVERED'] else None,
                'estimated_delivery': (order_date + timedelta(days=random.randint(3, 10))).date().isoformat(),
                'actual_delivery': (order_date + timedelta(days=random.randint(2, 12))).date().isoformat() if status == 'DELIVERED' else None,
                'notes': self.fake.sentence(nb_words=8) if random.random() < 0.1 else '',
                'ip_address': self.fake.ipv4(),
                'user_agent': self.fake.user_agent(),
                'referral_source': random.choice(['DIRECT', 'GOOGLE', 'FACEBOOK', 'EMAIL', 'AFFILIATE']),
                'promo_code': self.fake.bothify(text='PROMO###') if random.random() < 0.15 else None,
                'created_at': order_date.isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            orders.append(order)

        self.orders = orders
        logger.info(f"Generated {len(orders)} orders")
        return orders

    def generate_returns(self, return_rate: float = 0.05) -> List[Dict]:
        """Generate return records for delivered orders."""
        logger.info(f"Generating returns with {return_rate*100}% return rate...")

        if not self.orders:
            logger.warning("No orders generated. Generating orders first.")
            self.generate_orders()

        # Filter delivered orders
        delivered_orders = [order for order in self.orders if order['order_status'] == 'DELIVERED']

        num_returns = int(len(delivered_orders) * return_rate)
        orders_to_return = random.sample(delivered_orders, min(num_returns, len(delivered_orders)))

        returns = []

        for i, order in enumerate(orders_to_return, start=1):
            order_date = datetime.fromisoformat(order['order_date'])
            return_date = order_date + timedelta(days=random.randint(5, 30))

            # Select items to return (may be partial return)
            items_to_return = random.sample(
                order['line_items'],
                random.randint(1, len(order['line_items']))
            )

            refund_amount = sum(item['line_total'] for item in items_to_return)

            # Determine refund method (usually same as payment)
            refund_status = random.choices(
                ['APPROVED', 'PENDING', 'REJECTED'],
                weights=[0.85, 0.10, 0.05]
            )[0]

            return_record = {
                'return_id': f'RET{i:08d}',
                'order_id': order['order_id'],
                'customer_id': order['customer_id'],
                'return_date': return_date.isoformat(),
                'return_reason': random.choice(self.RETURN_REASONS),
                'return_reason_detail': self.fake.sentence(nb_words=10),
                'items_returned': [
                    {
                        'line_item_id': item['line_item_id'],
                        'product_id': item['product_id'],
                        'quantity': item['quantity'],
                        'refund_amount': item['line_total']
                    }
                    for item in items_to_return
                ],
                'refund_amount': round(refund_amount, 2),
                'refund_method': order['payment_method'],
                'refund_status': refund_status,
                'refund_processed_date': (return_date + timedelta(days=random.randint(1, 5))).isoformat() if refund_status == 'APPROVED' else None,
                'restocking_fee': round(refund_amount * 0.10, 2) if random.random() < 0.20 else 0.0,
                'condition': random.choice(['NEW', 'LIKE_NEW', 'USED', 'DAMAGED']),
                'approved_by': self.fake.name() if refund_status != 'PENDING' else None,
                'notes': self.fake.sentence(nb_words=8),
                'created_at': return_date.isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            returns.append(return_record)

        self.returns = returns
        logger.info(f"Generated {len(returns)} returns")
        return returns

    def write_to_parquet_local(self, output_dir: str):
        """Write generated data to local Parquet files."""
        logger.info(f"Writing sales data to local directory: {output_dir}")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Write products
        if self.products:
            df = pd.DataFrame(self.products)
            df.to_parquet(output_path / 'products.parquet', index=False, compression='snappy')
            logger.info(f"Wrote {len(self.products)} products to Parquet")

        # Write customers
        if self.customers:
            df = pd.DataFrame(self.customers)
            df.to_parquet(output_path / 'customers.parquet', index=False, compression='snappy')
            logger.info(f"Wrote {len(self.customers)} customers to Parquet")

        # Write orders (convert nested structures to JSON strings)
        if self.orders:
            orders_flat = []
            for order in self.orders:
                order_flat = order.copy()
                order_flat['shipping_address'] = json.dumps(order['shipping_address'])
                order_flat['billing_address'] = json.dumps(order['billing_address'])
                order_flat['line_items'] = json.dumps(order['line_items'])
                orders_flat.append(order_flat)

            df = pd.DataFrame(orders_flat)
            df.to_parquet(output_path / 'orders.parquet', index=False, compression='snappy')
            logger.info(f"Wrote {len(self.orders)} orders to Parquet")

        # Write returns
        if self.returns:
            returns_flat = []
            for ret in self.returns:
                ret_flat = ret.copy()
                ret_flat['items_returned'] = json.dumps(ret['items_returned'])
                returns_flat.append(ret_flat)

            df = pd.DataFrame(returns_flat)
            df.to_parquet(output_path / 'returns.parquet', index=False, compression='snappy')
            logger.info(f"Wrote {len(self.returns)} returns to Parquet")

    def write_to_s3(self, s3_bucket: str, s3_prefix: str = 'raw/sales'):
        """Write generated data to S3 as Parquet files."""
        logger.info(f"Writing sales data to S3: s3://{s3_bucket}/{s3_prefix}")

        try:
            s3_client = boto3.client('s3')

            # Write products
            if self.products:
                df = pd.DataFrame(self.products)
                parquet_buffer = df.to_parquet(index=False, compression='snappy')
                s3_client.put_object(
                    Bucket=s3_bucket,
                    Key=f"{s3_prefix}/products/products.parquet",
                    Body=parquet_buffer
                )
                logger.info(f"Wrote {len(self.products)} products to S3")

            # Write customers
            if self.customers:
                df = pd.DataFrame(self.customers)
                parquet_buffer = df.to_parquet(index=False, compression='snappy')
                s3_client.put_object(
                    Bucket=s3_bucket,
                    Key=f"{s3_prefix}/customers/customers.parquet",
                    Body=parquet_buffer
                )
                logger.info(f"Wrote {len(self.customers)} customers to S3")

            # Write orders
            if self.orders:
                orders_flat = []
                for order in self.orders:
                    order_flat = order.copy()
                    order_flat['shipping_address'] = json.dumps(order['shipping_address'])
                    order_flat['billing_address'] = json.dumps(order['billing_address'])
                    order_flat['line_items'] = json.dumps(order['line_items'])
                    orders_flat.append(order_flat)

                df = pd.DataFrame(orders_flat)
                parquet_buffer = df.to_parquet(index=False, compression='snappy')
                s3_client.put_object(
                    Bucket=s3_bucket,
                    Key=f"{s3_prefix}/orders/orders.parquet",
                    Body=parquet_buffer
                )
                logger.info(f"Wrote {len(self.orders)} orders to S3")

            # Write returns
            if self.returns:
                returns_flat = []
                for ret in self.returns:
                    ret_flat = ret.copy()
                    ret_flat['items_returned'] = json.dumps(ret['items_returned'])
                    returns_flat.append(ret_flat)

                df = pd.DataFrame(returns_flat)
                parquet_buffer = df.to_parquet(index=False, compression='snappy')
                s3_client.put_object(
                    Bucket=s3_bucket,
                    Key=f"{s3_prefix}/returns/returns.parquet",
                    Body=parquet_buffer
                )
                logger.info(f"Wrote {len(self.returns)} returns to S3")

        except ClientError as e:
            logger.error(f"Error writing to S3: {e}")
            raise


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate synthetic sales data for Enterprise Data Lakehouse'
    )

    parser.add_argument(
        '--orders',
        type=int,
        default=200000,
        help='Number of order records to generate (default: 200000)'
    )

    parser.add_argument(
        '--customers',
        type=int,
        default=50000,
        help='Number of customer records to generate (default: 50000)'
    )

    parser.add_argument(
        '--products',
        type=int,
        default=1000,
        help='Number of product records to generate (default: 1000)'
    )

    parser.add_argument(
        '--return-rate',
        type=float,
        default=0.05,
        help='Return rate as decimal (default: 0.05 = 5%%)'
    )

    parser.add_argument(
        '--start-date',
        type=str,
        help='Start date for order generation (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--end-date',
        type=str,
        help='End date for order generation (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--output-path',
        type=str,
        default='./data/sales',
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
        default='raw/sales',
        help='S3 key prefix (default: raw/sales)'
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
    logger.info("Initializing Sales Data Generator...")
    generator = SalesDataGenerator(seed=args.seed)

    # Generate data
    generator.generate_products(num_products=args.products)
    generator.generate_customers(num_customers=args.customers)
    generator.generate_orders(
        num_orders=args.orders,
        start_date=start_date,
        end_date=end_date
    )
    generator.generate_returns(return_rate=args.return_rate)

    # Write to local
    generator.write_to_parquet_local(args.output_path)

    # Write to S3 if bucket specified
    if args.s3_bucket:
        generator.write_to_s3(args.s3_bucket, args.s3_prefix)

    logger.info("Sales data generation completed successfully!")
    logger.info(f"Generated: {len(generator.products)} products, "
                f"{len(generator.customers)} customers, "
                f"{len(generator.orders)} orders, "
                f"{len(generator.returns)} returns")


if __name__ == '__main__':
    main()
