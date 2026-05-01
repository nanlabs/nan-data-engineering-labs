#!/usr/bin/env python3
"""Generar dataset de productos en formato Parquet"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

Path("data/raw").mkdir(parents=True, exist_ok=True)

random.seed(42)

categories = [
    'Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books',
    'Toys', 'Food & Beverage', 'Beauty', 'Automotive', None
]

brands = ['BrandA', 'BrandB', 'BrandC', 'BrandD', 'BrandE', 'Generic', None, '']

print("Generando products.parquet...")

products_data = []

for i in range(1, 501):
    product_id = i
    product_name = f"Product {i}"
    
    category = random.choice(categories)
    brand = random.choice(brands)
    
    # Precios con valores anómalos
    if random.random() < 0.02:
        price = round(random.uniform(-50, 0), 2)  # Negativos
    elif random.random() < 0.01:
        price = round(random.uniform(10000, 99999), 2)  # Muy altos
    else:
        price = round(random.uniform(10, 500), 2)
    
    # Stock con valores negativos
    if random.random() < 0.05:
        stock = random.randint(-100, -1)
    else:
        stock = random.randint(0, 1000)
    
    # Rating fuera de rango
    if random.random() < 0.03:
        rating = round(random.uniform(-1, 0), 1)
    elif random.random() < 0.02:
        rating = round(random.uniform(5.1, 10), 1)
    elif random.random() < 0.1:
        rating = None
    else:
        rating = round(random.uniform(1, 5), 1)
    
    num_reviews = random.randint(0, 5000) if rating else 0
    
    # Dimensiones con nulls
    weight = round(random.uniform(0.1, 50), 2) if random.random() > 0.1 else None
    length = round(random.uniform(5, 200), 1) if random.random() > 0.1 else None
    width = round(random.uniform(5, 150), 1) if random.random() > 0.1 else None
    height = round(random.uniform(5, 100), 1) if random.random() > 0.1 else None
    
    # Fechas
    days_ago = random.randint(1, 1825)
    created_at = datetime.now() - timedelta(days=days_ago)
    
    # is_active inconsistente
    is_active = random.choice([True, False, None, 1, 0])
    
    products_data.append({
        'product_id': product_id,
        'product_name': product_name,
        'category': category,
        'brand': brand,
        'price': price,
        'stock': stock,
        'rating': rating,
        'num_reviews': num_reviews,
        'weight_kg': weight,
        'length_cm': length,
        'width_cm': width,
        'height_cm': height,
        'created_at': created_at,
        'is_active': is_active
    })

# Guardar como CSV primero (Parquet requiere pandas/pyarrow)
# El usuario lo convertirá a Parquet en los ejercicios
with open('data/raw/products.csv', 'w', newline='', encoding='utf-8') as f:
    fieldnames = products_data[0].keys()
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in products_data:
        writer.writerow(row)

print(f"✅ Creado products.csv con 500 productos")
print(f"   (Convertir a Parquet en ejercicios con pandas)")
print(f"   Columnas: {len(fieldnames)}")
