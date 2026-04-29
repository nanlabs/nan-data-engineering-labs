"""
Data generation utilities for Cloud Data Engineering exercises.

Provides functions to generate synthetic data for various use cases:
- IoT sensor data
- Financial transactions
- E-commerce events
- User activity logs
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from faker import Faker
import random
from pathlib import Path


fake = Faker()


class IoTDataGenerator:
    """Generate synthetic IoT sensor data."""

    @staticmethod
    def generate_sensor_readings(
        num_records: int = 10000,
        num_devices: int = 100,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> pd.DataFrame:
        """
        Generate IoT sensor readings dataset.

        Args:
            num_records: Number of records to generate
            num_devices: Number of unique devices
            start_date: Start datetime
            end_date: End datetime

        Returns:
            DataFrame with sensor readings
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()

        device_ids = [f"DEVICE_{i:05d}" for i in range(num_devices)]
        device_types = ['temperature', 'humidity', 'pressure', 'vibration', 'light']
        locations = ['warehouse_A', 'warehouse_B', 'factory_1', 'factory_2', 'office']

        data = {
            'timestamp': [
                start_date + (end_date - start_date) * random.random()
                for _ in range(num_records)
            ],
            'device_id': [random.choice(device_ids) for _ in range(num_records)],
            'device_type': [random.choice(device_types) for _ in range(num_records)],
            'location': [random.choice(locations) for _ in range(num_records)],
        }

        df = pd.DataFrame(data)

        # Generate sensor-specific values
        df['value'] = df['device_type'].apply(lambda x: IoTDataGenerator._generate_sensor_value(x))
        df['unit'] = df['device_type'].apply(lambda x: IoTDataGenerator._get_unit(x))
        df['status'] = np.random.choice(['OK', 'WARNING', 'ERROR'], size=num_records, p=[0.85, 0.10, 0.05])

        # Sort by timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)

        return df

    @staticmethod
    def _generate_sensor_value(sensor_type: str) -> float:
        """Generate realistic value based on sensor type."""
        ranges = {
            'temperature': (15.0, 35.0),
            'humidity': (30.0, 80.0),
            'pressure': (980.0, 1020.0),
            'vibration': (0.0, 10.0),
            'light': (0.0, 1000.0),
        }
        low, high = ranges.get(sensor_type, (0.0, 100.0))
        return round(random.uniform(low, high), 2)

    @staticmethod
    def _get_unit(sensor_type: str) -> str:
        """Get unit for sensor type."""
        units = {
            'temperature': 'celsius',
            'humidity': 'percent',
            'pressure': 'hPa',
            'vibration': 'mm/s',
            'light': 'lux',
        }
        return units.get(sensor_type, 'units')


class FinancialDataGenerator:
    """Generate synthetic financial transaction data."""

    @staticmethod
    def generate_transactions(
        num_records: int = 10000,
        num_customers: int = 1000,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> pd.DataFrame:
        """
        Generate financial transactions dataset.

        Args:
            num_records: Number of transactions
            num_customers: Number of unique customers
            start_date: Start datetime
            end_date: End datetime

        Returns:
            DataFrame with transactions
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=90)
        if end_date is None:
            end_date = datetime.now()

        transaction_types = ['purchase', 'refund', 'withdrawal', 'deposit', 'transfer']
        categories = ['groceries', 'entertainment', 'utilities', 'transport', 'healthcare', 'other']
        payment_methods = ['credit_card', 'debit_card', 'bank_transfer', 'cash', 'mobile_payment']

        data = {
            'transaction_id': [f"TXN_{i:010d}" for i in range(num_records)],
            'timestamp': [
                start_date + (end_date - start_date) * random.random()
                for _ in range(num_records)
            ],
            'customer_id': [f"CUST_{random.randint(1, num_customers):06d}" for _ in range(num_records)],
            'transaction_type': [random.choice(transaction_types) for _ in range(num_records)],
            'category': [random.choice(categories) for _ in range(num_records)],
            'amount': [round(random.uniform(5.0, 500.0), 2) for _ in range(num_records)],
            'currency': ['USD'] * num_records,
            'payment_method': [random.choice(payment_methods) for _ in range(num_records)],
            'merchant_id': [f"MERCH_{random.randint(1, 500):05d}" for _ in range(num_records)],
            'status': np.random.choice(['completed', 'pending', 'failed'], size=num_records, p=[0.90, 0.07, 0.03]),
        }

        df = pd.DataFrame(data)

        # Refunds should have negative amounts
        df.loc[df['transaction_type'] == 'refund', 'amount'] *= -1

        # Sort by timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)

        return df


class ECommerceDataGenerator:
    """Generate synthetic e-commerce event data."""

    @staticmethod
    def generate_user_events(
        num_records: int = 10000,
        num_users: int = 1000,
        num_products: int = 500,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> pd.DataFrame:
        """
        Generate e-commerce user event stream.

        Args:
            num_records: Number of events
            num_users: Number of unique users
            num_products: Number of unique products
            start_date: Start datetime
            end_date: End datetime

        Returns:
            DataFrame with user events
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()

        event_types = ['page_view', 'product_view', 'add_to_cart', 'remove_from_cart', 'purchase', 'search']
        product_categories = ['electronics', 'clothing', 'home', 'sports', 'books', 'toys']

        data = {
            'event_id': [f"EVT_{i:012d}" for i in range(num_records)],
            'timestamp': [
                start_date + (end_date - start_date) * random.random()
                for _ in range(num_records)
            ],
            'user_id': [f"USER_{random.randint(1, num_users):06d}" for _ in range(num_records)],
            'session_id': [fake.uuid4() for _ in range(num_records)],
            'event_type': [random.choice(event_types) for _ in range(num_records)],
            'product_id': [f"PROD_{random.randint(1, num_products):05d}" if random.random() > 0.2 else None for _ in range(num_records)],
            'product_category': [random.choice(product_categories) if random.random() > 0.2 else None for _ in range(num_records)],
            'price': [round(random.uniform(10.0, 1000.0), 2) if random.random() > 0.3 else None for _ in range(num_records)],
            'device_type': np.random.choice(['mobile', 'desktop', 'tablet'], size=num_records, p=[0.5, 0.4, 0.1]),
            'country': [fake.country_code() for _ in range(num_records)],
        }

        df = pd.DataFrame(data)
        df = df.sort_values('timestamp').reset_index(drop=True)

        return df


class LogDataGenerator:
    """Generate synthetic application log data."""

    @staticmethod
    def generate_application_logs(
        num_records: int = 10000,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> pd.DataFrame:
        """
        Generate application log entries.

        Args:
            num_records: Number of log entries
            start_date: Start datetime
            end_date: End datetime

        Returns:
            DataFrame with log entries
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=7)
        if end_date is None:
            end_date = datetime.now()

        log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        services = ['auth-service', 'payment-service', 'inventory-service', 'user-service', 'api-gateway']

        messages = {
            'DEBUG': ['Request received', 'Cache hit', 'Query executed'],
            'INFO': ['User logged in', 'Payment processed', 'Order created', 'Email sent'],
            'WARNING': ['Slow query detected', 'High memory usage', 'Rate limit approaching'],
            'ERROR': ['Database connection failed', 'Invalid token', 'Payment declined', 'Service unavailable'],
            'CRITICAL': ['System crash', 'Data corruption detected', 'Security breach attempt'],
        }

        data = []
        for _ in range(num_records):
            level = np.random.choice(log_levels, p=[0.30, 0.45, 0.15, 0.08, 0.02])
            service = random.choice(services)
            message = random.choice(messages[level])

            data.append({
                'timestamp': start_date + (end_date - start_date) * random.random(),
                'level': level,
                'service': service,
                'message': message,
                'request_id': fake.uuid4(),
                'user_id': f"USER_{random.randint(1, 1000):06d}" if random.random() > 0.3 else None,
                'duration_ms': random.randint(10, 5000) if level in ['DEBUG', 'INFO'] else None,
                'error_code': f"E{random.randint(1000, 9999)}" if level in ['ERROR', 'CRITICAL'] else None,
            })

        df = pd.DataFrame(data)
        df = df.sort_values('timestamp').reset_index(drop=True)

        return df


def save_dataset(df: pd.DataFrame, output_path: Path, format: str = 'parquet'):
    """
    Save DataFrame to file in specified format.

    Args:
        df: DataFrame to save
        output_path: Output file path
        format: Output format ('parquet', 'csv', 'json')
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if format == 'parquet':
        df.to_parquet(output_path, index=False)
    elif format == 'csv':
        df.to_csv(output_path, index=False)
    elif format == 'json':
        df.to_json(output_path, orient='records', lines=True)
    else:
        raise ValueError(f"Unsupported format: {format}")

    print(f"✓ Saved {len(df)} records to {output_path}")


# Example usage
if __name__ == "__main__":
    # Generate sample datasets
    output_dir = Path("../data/common-datasets")
    output_dir.mkdir(parents=True, exist_ok=True)

    # IoT sensor data
    iot_data = IoTDataGenerator.generate_sensor_readings(num_records=10000)
    save_dataset(iot_data, output_dir / "iot_sensor_data.parquet")

    # Financial transactions
    financial_data = FinancialDataGenerator.generate_transactions(num_records=10000)
    save_dataset(financial_data, output_dir / "financial_transactions.parquet")

    # E-commerce events
    ecommerce_data = ECommerceDataGenerator.generate_user_events(num_records=10000)
    save_dataset(ecommerce_data, output_dir / "ecommerce_events.parquet")

    # Application logs
    log_data = LogDataGenerator.generate_application_logs(num_records=10000)
    save_dataset(log_data, output_dir / "application_logs.parquet")

    print("\n✅ All sample datasets generated successfully!")
