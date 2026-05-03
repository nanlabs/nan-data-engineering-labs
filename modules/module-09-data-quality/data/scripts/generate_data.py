#!/usr/bin/env python3
"""
Data Quality Sample Data Generator

Genera datasets con problemas de calidad intencionales para practicar:
- Missing values (nulls, empty strings)
- Duplicates (exact, fuzzy)
- Invalid formats (emails, phones, dates)
- Outliers y valores fuera de rango
- Inconsistencias lógicas
- Referential integrity issues
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from faker import Faker
import random
import argparse
from pathlib import Path

# Seed para reproducibilidad
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
fake = Faker()
Faker.seed(SEED)


class DataQualityDataGenerator:
    """Generador de datasets con problemas de calidad."""

    def __init__(self, output_dir: str = "data/samples"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_customers(self, n: int = 10000, quality: str = 'poor') -> pd.DataFrame:
        """
        Genera dataset de customers con problemas de calidad.

        Args:
            n: Número de registros
            quality: 'clean', 'medium', 'poor'
        """
        print(f"Generando {n} customers (quality: {quality})...")

        data = {
            'customer_id': range(1, n + 1),
            'first_name': [fake.first_name() for _ in range(n)],
            'last_name': [fake.last_name() for _ in range(n)],
            'email': [fake.email() for _ in range(n)],
            'phone': [fake.phone_number() for _ in range(n)],
            'date_of_birth': [fake.date_of_birth(minimum_age=18, maximum_age=90) for _ in range(n)],
            'registration_date': [fake.date_between(start_date='-5y', end_date='today') for _ in range(n)],
            'country': [fake.country_code() for _ in range(n)],
            'city': [fake.city() for _ in range(n)],
            'zipcode': [fake.postcode() for _ in range(n)],
            'account_status': [random.choice(['active', 'inactive', 'suspended', 'pending']) for _ in range(n)],
        }

        df = pd.DataFrame(data)

        if quality in ['medium', 'poor']:
            df = self._inject_quality_issues_customers(df, severity=quality)

        return df

    def _inject_quality_issues_customers(self, df: pd.DataFrame, severity: str) -> pd.DataFrame:
        """Inyecta problemas de calidad en customers."""
        n = len(df)

        if severity == 'medium':
            null_rate, duplicate_rate, invalid_rate = 0.05, 0.02, 0.03
        else:  # poor
            null_rate, duplicate_rate, invalid_rate = 0.15, 0.08, 0.10

        # 1. Missing values
        null_indices = random.sample(range(n), int(n * null_rate))
        for idx in null_indices:
            col = random.choice(['email', 'phone', 'zipcode', 'city'])
            df.loc[idx, col] = None

        # 2. Empty strings
        empty_indices = random.sample(range(n), int(n * null_rate / 2))
        for idx in empty_indices:
            col = random.choice(['first_name', 'last_name', 'city'])
            df.loc[idx, col] = ''

        # 3. Duplicates (exact)
        duplicate_indices = random.sample(range(n), int(n * duplicate_rate))
        for idx in duplicate_indices:
            source_idx = random.randint(0, n - 1)
            df.loc[idx] = df.loc[source_idx]

        # 4. Invalid emails
        invalid_indices = random.sample(range(n), int(n * invalid_rate))
        for idx in invalid_indices:
            if pd.notna(df.loc[idx, 'email']):
                # Corromper email
                corruptions = [
                    lambda e: e.replace('@', '@@'),
                    lambda e: e.replace('.com', ''),
                    lambda e: e.split('@')[0],
                    lambda e: '@' + e
                ]
                df.loc[idx, 'email'] = random.choice(corruptions)(df.loc[idx, 'email'])

        # 5. Invalid phone numbers
        for idx in invalid_indices[:len(invalid_indices)//2]:
            if pd.notna(df.loc[idx, 'phone']):
                df.loc[idx, 'phone'] = '123'  # Too short

        # 6. Future dates of birth (impossible)
        future_indices = random.sample(range(n), int(n * 0.01))
        for idx in future_indices:
            df.loc[idx, 'date_of_birth'] = datetime.now().date() + timedelta(days=random.randint(1, 365))

        # 7. Registration before birth
        logic_indices = random.sample(range(n), int(n * 0.02))
        for idx in logic_indices:
            dob = df.loc[idx, 'date_of_birth']
            if pd.notna(dob):
                df.loc[idx, 'registration_date'] = dob - timedelta(days=random.randint(1, 365))

        # 8. Invalid status values
        invalid_status_indices = random.sample(range(n), int(n * 0.01))
        for idx in invalid_status_indices:
            df.loc[idx, 'account_status'] = random.choice(['ACTIVE', 'deleted', 'unknown', ''])

        return df

    def generate_transactions(self, customer_ids: list, n: int = 50000, quality: str = 'poor') -> pd.DataFrame:
        """Genera dataset de transactions."""
        print(f"Generando {n} transactions (quality: {quality})...")

        data = {
            'transaction_id': range(1, n + 1),
            'customer_id': [random.choice(customer_ids) for _ in range(n)],
            'product_id': [random.randint(1, 1000) for _ in range(n)],
            'amount': [round(random.uniform(1, 1000), 2) for _ in range(n)],
            'quantity': [random.randint(1, 10) for _ in range(n)],
            'transaction_date': [fake.date_time_between(start_date='-2y', end_date='now') for _ in range(n)],
            'payment_method': [random.choice(['credit_card', 'debit_card', 'paypal', 'bank_transfer'])
                              for _ in range(n)],
            'status': [random.choice(['completed', 'pending', 'failed', 'refunded']) for _ in range(n)],
            'currency': [random.choice(['USD', 'EUR', 'GBP']) for _ in range(n)],
        }

        df = pd.DataFrame(data)

        # Calcular total (para validaciones lógicas)
        df['total'] = df['amount'] * df['quantity']

        if quality in ['medium', 'poor']:
            df = self._inject_quality_issues_transactions(df, customer_ids, severity=quality)

        return df

    def _inject_quality_issues_transactions(self, df: pd.DataFrame, valid_customer_ids: list, severity: str) -> pd.DataFrame:
        """Inyecta problemas de calidad en transactions."""
        n = len(df)

        if severity == 'medium':
            null_rate, orphan_rate, outlier_rate = 0.03, 0.05, 0.02
        else:  # poor
            null_rate, orphan_rate, outlier_rate = 0.10, 0.15, 0.05

        # 1. Missing values críticos
        null_indices = random.sample(range(n), int(n * null_rate))
        for idx in null_indices:
            col = random.choice(['customer_id', 'amount', 'transaction_date'])
            df.loc[idx, col] = None

        # 2. Orphan foreign keys (customer_id que no existe)
        orphan_indices = random.sample(range(n), int(n * orphan_rate))
        max_customer_id = max(valid_customer_ids)
        for idx in orphan_indices:
            df.loc[idx, 'customer_id'] = max_customer_id + random.randint(1, 10000)

        # 3. Negative amounts
        negative_indices = random.sample(range(n), int(n * 0.02))
        for idx in negative_indices:
            df.loc[idx, 'amount'] = -abs(df.loc[idx, 'amount'])

        # 4. Outliers (amounts extremos)
        outlier_indices = random.sample(range(n), int(n * outlier_rate))
        for idx in outlier_indices:
            df.loc[idx, 'amount'] = random.choice([
                random.uniform(10000, 100000),  # Very high
                random.uniform(0.001, 0.01)     # Very low
            ])

        # 5. Invalid status
        invalid_status_indices = random.sample(range(n), int(n * 0.01))
        for idx in invalid_status_indices:
            df.loc[idx, 'status'] = random.choice(['COMPLETED', 'error', '', None])

        # 6. Logical inconsistency: total != amount * quantity
        logic_indices = random.sample(range(n), int(n * 0.03))
        for idx in logic_indices:
            df.loc[idx, 'total'] = df.loc[idx, 'total'] * random.uniform(0.5, 1.5)

        # 7. Future dates
        future_indices = random.sample(range(n), int(n * 0.01))
        for idx in future_indices:
            df.loc[idx, 'transaction_date'] = datetime.now() + timedelta(days=random.randint(1, 365))

        # 8. Duplicates
        duplicate_indices = random.sample(range(n), int(n * 0.05))
        for idx in duplicate_indices:
            source_idx = random.randint(0, n - 1)
            df.loc[idx] = df.loc[source_idx]

        return df

    def generate_products(self, n: int = 1000, quality: str = 'poor') -> pd.DataFrame:
        """Genera dataset de products."""
        print(f"Generando {n} products (quality: {quality})...")

        categories = ['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books', 'Toys']

        data = {
            'product_id': range(1, n + 1),
            'product_name': [fake.catch_phrase() for _ in range(n)],
            'category': [random.choice(categories) for _ in range(n)],
            'price': [round(random.uniform(5, 500), 2) for _ in range(n)],
            'cost': [round(random.uniform(2, 400), 2) for _ in range(n)],
            'stock_quantity': [random.randint(0, 1000) for _ in range(n)],
            'weight_kg': [round(random.uniform(0.1, 50), 2) for _ in range(n)],
            'supplier_id': [random.randint(1, 100) for _ in range(n)],
            'is_active': [random.choice([True, False]) for _ in range(n)],
        }

        df = pd.DataFrame(data)

        if quality in ['medium', 'poor']:
            df = self._inject_quality_issues_products(df, severity=quality)

        return df

    def _inject_quality_issues_products(self, df: pd.DataFrame, severity: str) -> pd.DataFrame:
        """Inyecta problemas de calidad en products."""
        n = len(df)

        if severity == 'medium':
            null_rate = 0.05
        else:  # poor
            null_rate = 0.12

        # 1. Missing values
        null_indices = random.sample(range(n), int(n * null_rate))
        for idx in null_indices:
            col = random.choice(['product_name', 'category', 'price', 'stock_quantity'])
            df.loc[idx, col] = None

        # 2. Negative prices
        negative_indices = random.sample(range(n), int(n * 0.02))
        for idx in negative_indices:
            df.loc[idx, 'price'] = -abs(df.loc[idx, 'price'])

        # 3. Cost > Price (no profit)
        unprofitable_indices = random.sample(range(n), int(n * 0.08))
        for idx in unprofitable_indices:
            df.loc[idx, 'cost'] = df.loc[idx, 'price'] * random.uniform(1.1, 2.0)

        # 4. Negative stock
        negative_stock_indices = random.sample(range(n), int(n * 0.01))
        for idx in negative_stock_indices:
            df.loc[idx, 'stock_quantity'] = -random.randint(1, 100)

        # 5. Duplicates
        duplicate_indices = random.sample(range(n), int(n * 0.03))
        for idx in duplicate_indices:
            source_idx = random.randint(0, n - 1)
            df.loc[idx] = df.loc[source_idx]

        # 6. Invalid categories
        invalid_cat_indices = random.sample(range(n), int(n * 0.02))
        for idx in invalid_cat_indices:
            df.loc[idx, 'category'] = random.choice(['electronics', 'CLOTHING', '', None])

        return df

    def generate_all(self, quality: str = 'poor'):
        """Genera todos los datasets."""
        print(f"\n{'='*60}")
        print(f"Generando datasets de muestra (quality: {quality})")
        print(f"{'='*60}\n")

        # Generate datasets
        customers = self.generate_customers(n=10000, quality=quality)
        valid_customer_ids = customers['customer_id'].dropna().unique().tolist()

        transactions = self.generate_transactions(
            customer_ids=valid_customer_ids,
            n=50000,
            quality=quality
        )

        products = self.generate_products(n=1000, quality=quality)

        # Save to CSV
        customers.to_csv(self.output_dir / f'customers_{quality}.csv', index=False)
        transactions.to_csv(self.output_dir / f'transactions_{quality}.csv', index=False)
        products.to_csv(self.output_dir / f'products_{quality}.csv', index=False)

        # Save to Parquet
        customers.to_parquet(self.output_dir / f'customers_{quality}.parquet', index=False)
        transactions.to_parquet(self.output_dir / f'transactions_{quality}.parquet', index=False)
        products.to_parquet(self.output_dir / f'products_{quality}.parquet', index=False)

        print(f"\n{'='*60}")
        print(f"✅ Datasets generados en: {self.output_dir}")
        print(f"{'='*60}\n")

        # Print summary
        self._print_quality_summary(customers, transactions, products)

    def _print_quality_summary(self, customers: pd.DataFrame, transactions: pd.DataFrame, products: pd.DataFrame):
        """Imprime resumen de problemas de calidad."""
        print("\n📊 RESUMEN DE CALIDAD DE DATOS\n")

        datasets = {
            'Customers': customers,
            'Transactions': transactions,
            'Products': products
        }

        for name, df in datasets.items():
            print(f"{name}:")
            print(f"  Registros: {len(df):,}")
            print(f"  Columnas: {len(df.columns)}")

            # Nulls
            null_count = df.isnull().sum().sum()
            null_pct = (null_count / (df.shape[0] * df.shape[1])) * 100
            print(f"  Nulls: {null_count:,} ({null_pct:.2f}%)")

            # Duplicates
            dupes = df.duplicated().sum()
            dupe_pct = (dupes / len(df)) * 100
            print(f"  Duplicados: {dupes:,} ({dupe_pct:.2f}%)")

            print()


def main():
    parser = argparse.ArgumentParser(description='Genera datasets de muestra con problemas de calidad')
    parser.add_argument(
        '--quality',
        choices=['clean', 'medium', 'poor'],
        default='poor',
        help='Nivel de calidad de los datos (default: poor)'
    )
    parser.add_argument(
        '--output',
        default='data/samples',
        help='Directorio de salida (default: data/samples)'
    )

    args = parser.parse_args()

    generator = DataQualityDataGenerator(output_dir=args.output)
    generator.generate_all(quality=args.quality)


if __name__ == '__main__':
    main()
