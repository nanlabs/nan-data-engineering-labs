# Data Generation for Module 07

Este directorio contiene esquemas y scripts para generar datos de batch processing.

## 📦 Datasets Disponibles

### 1. Transactions (10M+ records)

transactions de e-commerce con:

- Timestamps distributed in 90 days
- Multiple product categories
- Different payment methods
- Diverse countries
- Particionado por fecha (year/month/day)

### 2. Users (1M records)

Perfiles de usuarios con:

- Diferentes tiers (bronze, silver, gold, platinum)
- Geographic distribution
- Leveles de actividad
- Creation timestamps

### 3. Products (100K records)

Product catalog with:

- 8 different categories
- Marcas populares
- Ratings y reviews
- Leveles de stock

## 🚀 Data Generation

### Requirements

```bash
pip install pandas pyarrow tqdm
```text

### Generar transactions

```bash
# Default: 10M transactions, 90 days, Parquet format, date partitioned
python data/scripts/generate_transactions.py

# Custom configuration
python data/scripts/generate_transactions.py \
  --total-records 5000000 \
  --days 60 \
  --start-date 2024-01-01 \
  --format parquet \
  --partition-by date \
  --output-dir data/raw/transactions
```text

**Opciones**:

- `--total-records`: Total number of transactions (default: 10M)
- `--days`: Number of days to generate (default: 90)
- `--start-date`: Fecha de inicio YYYY-MM-DD (default: 2024-01-01)
- `--format`: parquet, csv, json (default: parquet)
- `--partition-by`: date o none (default: date)
- `--output-dir`: Directorio de salida

**Output structure** (con `--partition-by date`):

```text
data/raw/transactions/
├── year=2024/
│   ├── month=01/
│   │   ├── day=01/
│   │   │   └── transactions.parquet
│   │   ├── day=02/
│   │   └── ...
│   ├── month=02/
│   └── ...
```

**Estimated size**:

- 10M records: ~500 MB (Parquet snappy)
- 1M records: ~50 MB
- CSV is ~5x larger

### Generar Usuarios

```bash
# Default: 1M users
python data/scripts/generate_users.py

# Custom configuration
python data/scripts/generate_users.py \
  --num-users 500000 \
  --format parquet \
  --output-path data/raw/users.parquet
```text

**Size**: ~50 MB for 1M users (Parquet)

### Generar Productos

```bash
# Default: 100K products
python data/scripts/generate_products.py

# Custom configuration
python data/scripts/generate_products.py \
  --num-products 50000 \
  --format parquet \
  --output-path data/raw/products.parquet
```text

**Size**: ~10 MB for 100K products (Parquet)

## 📊 Schemas

Los schemas JSON en `schemas/` definen la estructura de cada dataset:

- `transactions.json`: Schema de transactions
- `users.json`: Schema de usuarios
- `products.json`: Schema de productos

Use them for validation with tools like`jsonschema` o `pydantic`.

## 💡 Tips

### Generate Small Dataset (Testing)

```bash
# 100K transactions para testing rápido
python data/scripts/generate_transactions.py \
  --total-records 100000 \
  --days 7 \
  --output-dir data/raw/transactions_small
```text

### Generar Dataset Grande (Performance Testing)

```bash
# 50M transactions para performance testing
python data/scripts/generate_transactions.py \
  --total-records 50000000 \
  --days 180 \
  --output-dir data/raw/transactions_large
```

**Nota**: 50M records = ~2.5 GB Parquet, toma ~30 minutes generar

### Formato Recomendado

✅ **Parquet**: Columnr format, compressed, fast

- Usa `--format parquet` (default)
- Automatic compression (snappy)
- Mejor para batch processing

❌ **CSV**: Only for small exports

- 5x larger than Parquet
- 10x slower to read
- No recomendado para > 1M records

## 🎯 Usage in Exercises

### Exercise 01: Batch Basics

Use small dataset (100K records)

### Exercise 02-03: Partitioning & PySpark

Usa dataset mediano (1M-5M records)

### Exercise 04-06: Pipelines & Optimization

Usa dataset grande (10M-50M records)

## 🔍 Data Quality

Los scripts generan datos realistas con:

- ✅ Weighted distributions (more "completed" than "failed")
- ✅ Correlaciones (tier alto → mayor gasto)
- ✅ Realistic timestamps (more activity during business hours)
- ✅ Data integrity (valid foreign keys)
- ✅ Edge cases (algunas transactions failed, users inactivos)

## 📁 Estructura de Archivos

```text
data/
├── schemas/
│   ├── transactions.json     # Transaction schema
│   ├── users.json            # User schema
│   └── products.json         # Product schema
│
├── scripts/
│   ├── generate_transactions.py  # Genera transacciones
│   ├── generate_users.py         # Genera usuarios
│   └── generate_products.py      # Genera productos
│
└── raw/                      # Data generada (git ignored)
    ├── transactions/         # Transacciones particionadas
    ├── users.parquet         # 1M usuarios
    └── products.parquet      # 100K productos
```text

## ⚠️ Notas

1. **Data es git ignored**: Los archivos en `data/raw/` no se suben a git
2. **Generation takes time**: 10M records = ~10 minutes
3. **Espacio en disco**: 10M records = ~500 MB
4. **Memoria**: Scripts usan batching, safe para RAM limitado

## 🚀 Quick Start

```bash
# Generar todos los datasets con defaults
python data/scripts/generate_transactions.py
python data/scripts/generate_users.py
python data/scripts/generate_products.py

# Verificar
ls -lh data/raw/
```text

Total: ~560 MB de data de entrenamiento
