#!/usr/bin/env python3
"""Generar dataset de órdenes en JSON con estructura nested"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

Path("data/raw").mkdir(parents=True, exist_ok=True)

random.seed(42)

statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled', 'returned', None]
payment_methods = ['credit_card', 'debit_card', 'paypal', 'bank_transfer', 'cash', None]
shipping_methods = ['standard', 'express', 'overnight', 'pickup', None]

print("Generando orders.json (esto puede tardar un minuto)...")

orders = []

for i in range(1, 50001):
    if i % 10000 == 0:
        print(f"  {i}/50000 órdenes generadas...")
    
    days_ago = random.randint(1, 730)
    order_date = datetime.now() - timedelta(days=days_ago)
    
    # order_id con formato inconsistente (~2%)
    order_id = f"ORD-{i:06d}" if random.random() > 0.02 else str(i)
    customer_id = random.randint(1, 10000)
    
    # Items nested
    num_items = random.randint(1, 8)
    items = []
    total = 0
    
    for _ in range(num_items):
        product_id = random.randint(1, 500)
        quantity = random.randint(1, 5)
        price = round(random.uniform(10, 500), 2)
        subtotal = round(quantity * price, 2)
        total += subtotal
        
        items.append({
            "product_id": product_id,
            "quantity": quantity,
            "price": price,
            "subtotal": subtotal
        })
    
    # Shipping address nested
    shipping_address = {
        "street": f"Calle {random.randint(1, 100)}",
        "number": str(random.randint(1, 999)),
        "city": random.choice(["Ciudad de México", "Madrid", "Buenos Aires", "Bogotá", None]),
        "state": random.choice(["CDMX", "Madrid", "Buenos Aires", "Cundinamarca", None]),
        "postal_code": str(random.randint(10000, 99999)) if random.random() > 0.05 else None,
        "country": random.choice(["México", "España", "Argentina", "Colombia"])
    } if random.random() > 0.03 else None
    
    # Algunos totales incorrectos (~5%)
    if random.random() < 0.05:
        total = round(total * random.uniform(0.8, 1.2), 2)
    
    order = {
        "order_id": order_id,
        "customer_id": customer_id,
        "order_date": order_date.isoformat() if random.random() > 0.02 
                      else order_date.strftime('%Y-%m-%d %H:%M:%S'),
        "status": random.choice(statuses),
        "payment_method": random.choice(payment_methods),
        "shipping_method": random.choice(shipping_methods),
        "items": items,
        "subtotal": round(total, 2),
        "tax": round(total * 0.16, 2) if random.random() > 0.03 else None,
        "shipping_cost": round(random.uniform(0, 50), 2) if random.random() > 0.1 else 0,
        "total": round(total * 1.16 + random.uniform(0, 50), 2),
        "shipping_address": shipping_address,
        "notes": random.choice([None, "", "Entrega urgente", "Dejar con portero", "Llamar antes"])
    }
    
    orders.append(order)

# Guardar en JSON
print("  Guardando archivo...")
with open('data/raw/orders.json', 'w', encoding='utf-8') as f:
    json.dump(orders, f, indent=2, ensure_ascii=False)

print("✅ Creado orders.json con 50,000 órdenes")
