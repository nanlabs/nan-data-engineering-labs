#!/usr/bin/env python3
"""
Script para generar todos los datasets del módulo
Ejecutar: python generate_all_datasets.py
"""

import subprocess
import sys
from pathlib import Path

# Crear directorios si no existen
Path("data/raw").mkdir(parents=True, exist_ok=True)
Path("data/processed").mkdir(parents=True, exist_ok=True)

scripts = [
    "generate_customers.py",
    "generate_orders.py",
    "generate_products.py",
    "generate_transactions.py",
    "generate_user_activity.py"
]

print("="*60)
print("Generando datasets para Módulo 04 - Python for Data")
print("="*60)

for script in scripts:
    print(f"\n🔄 Ejecutando {script}...")
    try:
        result = subprocess.run(
            [sys.executable, script],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando {script}:")
        print(e.stderr)
        sys.exit(1)

print("\n" + "="*60)
print("✅ Todos los datasets fueron generados exitosamente")
print("="*60)
print("\nArchivos creados en data/raw/:")
print("  - customers.csv (10,000 registros)")
print("  - orders.json (50,000 registros)")
print("  - products.parquet (500 registros)")
print("  - transactions.csv (100,000 registros)")
print("  - user_activity.json (20,000 registros)")
print("\nTotal: ~180,000 registros")
