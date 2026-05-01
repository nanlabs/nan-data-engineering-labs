#!/usr/bin/env python3
"""Generar dataset de clientes con datos sucios"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

# Asegurar que existe el directorio
Path("data/raw").mkdir(parents=True, exist_ok=True)

random.seed(42)

# Listas para generar datos realistas
first_names = [
    "María", "Juan", "Ana", "Carlos", "Laura", "Pedro", "Carmen", "José",
    "Isabel", "Miguel", "Rosa", "Antonio", "Sofía", "Francisco", "Elena",
    "Luis", "Patricia", "Javier", "Marta", "Diego", None, ""
]

last_names = [
    "García", "Rodríguez", "Martínez", "López", "González", "Pérez",
    "Sánchez", "Ramírez", "Torres", "Flores", "Rivera", "Gómez", "Díaz",
    "Cruz", "Morales", "Reyes", "Gutiérrez", None, ""
]

countries = [
    "México", "España", "Argentina", "Colombia", "Chile", "Perú",
    "Venezuela", "Ecuador", "Uruguay", "Paraguay", "Bolivia",
    "Guatemala", "Cuba", "Honduras", None, ""
]

cities = [
    "Ciudad de México", "Madrid", "Buenos Aires", "Bogotá", "Santiago",
    "Lima", "Caracas", "Quito", "Montevideo", "Asunción", "La Paz",
    "Guatemala City", "La Habana", None, ""
]

print("Generando customers.csv...")

with open('data/raw/customers.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow([
        'customer_id', 'first_name', 'last_name', 'email', 'phone',
        'country', 'city', 'registration_date', 'is_active', 'loyalty_points'
    ])
    
    for i in range(1, 10001):
        # Duplicados (~2%)
        if random.random() < 0.02 and i > 100:
            customer_id = random.randint(1, i-1)
        else:
            customer_id = i
        
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        
        # Email con inconsistencias
        if first_name and last_name and random.random() > 0.05:
            email_formats = [
                f"{first_name.lower()}.{last_name.lower()}@email.com",
                f"{first_name.lower()}{i}@email.com",
                f"{last_name.lower()}.{first_name.lower()}@gmail.com",
                f"{first_name.lower()}_{last_name.lower()}@hotmail.com"
            ]
            email = random.choice(email_formats)
            # Emails malformados (~2%)
            if random.random() < 0.02:
                email = email.replace('@', '')
        else:
            email = None if random.random() < 0.5 else ""
        
        # Teléfono con formatos inconsistentes
        if random.random() > 0.1:
            phone_formats = [
                f"+52{random.randint(1000000000, 9999999999)}",
                f"{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                f"({random.randint(100, 999)}) {random.randint(100, 999)}-{random.randint(1000, 9999)}",
                f"{random.randint(1000000000, 9999999999)}"
            ]
            phone = random.choice(phone_formats)
        else:
            phone = None if random.random() < 0.5 else ""
        
        country = random.choice(countries)
        city = random.choice(cities)
        
        # Fechas con formatos inconsistentes
        days_ago = random.randint(1, 1460)
        reg_date = datetime.now() - timedelta(days=days_ago)
        date_formats = [
            reg_date.strftime('%Y-%m-%d'),
            reg_date.strftime('%d/%m/%Y'),
            reg_date.strftime('%m-%d-%Y'),
            reg_date.strftime('%Y/%m/%d')
        ]
        registration_date = random.choice(date_formats)
        
        # is_active con valores inconsistentes
        active_values = [True, False, 'true', 'false', 'True', 'False',
                        1, 0, 'yes', 'no', 'Y', 'N', None, '']
        is_active = random.choice(active_values)
        
        # Loyalty points con valores anómalos
        if random.random() < 0.02:
            loyalty_points = random.randint(-100, -1)
        elif random.random() < 0.01:
            loyalty_points = random.randint(100000, 999999)
        else:
            loyalty_points = random.randint(0, 10000)
        
        writer.writerow([
            customer_id, first_name, last_name, email, phone,
            country, city, registration_date, is_active, loyalty_points
        ])

print("✅ Creado customers.csv con 10,000 registros")
