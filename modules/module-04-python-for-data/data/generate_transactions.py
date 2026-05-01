#!/usr/bin/env python3
"""Generar dataset de transacciones"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

Path("data/raw").mkdir(parents=True, exist_ok=True)

random.seed(42)

transaction_types = ['purchase', 'refund', 'adjustment', 'bonus', None]
currencies = ['USD', 'EUR', 'MXN', 'ARS', 'COP', None]
payment_statuses = ['completed', 'pending', 'failed', 'cancelled', None]
payment_providers = ['Stripe', 'PayPal', 'Square', 'MercadoPago', 'Bank Transfer', None]

print("Generando transactions.csv (esto puede tardar un minuto)...")

with open('data/raw/transactions.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow([
        'transaction_id', 'order_id', 'customer_id', 'transaction_date',
        'transaction_type', 'amount', 'currency', 'payment_status',
        'payment_provider', 'fee', 'net_amount'
    ])
    
    for i in range(1, 100001):
        if i % 20000 == 0:
            print(f"  {i}/100000 transacciones generadas...")
        
        transaction_id = f"TXN-{i:08d}"
        
        # Orphan order_ids (~5%)
        if random.random() < 0.05:
            order_id = f"ORD-{random.randint(50001, 60000):06d}"
        else:
            order_id = f"ORD-{random.randint(1, 50000):06d}"
        
        customer_id = random.randint(1, 10000)
        
        # Fechas con formatos inconsistentes
        days_ago = random.randint(1, 730)
        trans_date = datetime.now() - timedelta(
            days=days_ago,
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        date_formats = [
            trans_date.isoformat(),
            trans_date.strftime('%Y-%m-%d %H:%M:%S'),
            trans_date.strftime('%d/%m/%Y %H:%M'),
            trans_date.strftime('%Y-%m-%d')
        ]
        transaction_date = random.choice(date_formats)
        
        transaction_type = random.choice(transaction_types)
        
        # Montos con valores anómalos
        if transaction_type == 'refund':
            amount = round(random.uniform(-1000, -10), 2)
        elif random.random() < 0.01:
            amount = 0
        elif random.random() < 0.005:
            amount = round(random.uniform(100000, 999999), 2)
        else:
            amount = round(random.uniform(10, 5000), 2)
        
        currency = random.choice(currencies)
        payment_status = random.choice(payment_statuses)
        payment_provider = random.choice(payment_providers)
        
        # Fee como porcentaje
        if payment_provider and amount > 0:
            fee = round(amount * random.uniform(0.02, 0.05), 2)
        else:
            fee = 0 if random.random() > 0.1 else None
        
        net_amount = round(amount - (fee if fee else 0), 2)
        
        writer.writerow([
            transaction_id, order_id, customer_id, transaction_date,
            transaction_type, amount, currency, payment_status,
            payment_provider, fee, net_amount
        ])

print("✅ Creado transactions.csv con 100,000 transacciones")
