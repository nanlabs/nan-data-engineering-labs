# Data Quality Module - Sample Data

This directory contains sample data with intentional quality issues to practice validation and cleaning techniques.

## 📁 Estructura

```text
data/
├── schemas/              # JSON schemas para validation
├── scripts/
│   └── generate_data.py  # Script para generar datos
└── samples/              # Datos generados (CSV y Parquet)
    ├── customers_poor.csv
    ├── customers_medium.csv
    ├── customers_clean.csv
    ├── transactions_poor.csv
    ├── transactions_medium.csv
    ├── transactions_clean.csv
    ├── products_poor.csv
    ├── products_medium.csv
    └── products_clean.csv
```text

## 🎯 Datasets

### 1. Customers (10,000 registros)

**columns:**

- `customer_id`(int): Unique ID of the client
- `first_name` (string): Nombre
- `last_name` (string): Apellido
- `email` (string): Email
- `phone`(string): Phone
- `date_of_birth` (date): Fecha de nacimiento
- `registration_date` (date): Fecha de registro
- `country`(string): Country code
- `city` (string): Ciudad
- `zipcode`(string): Zip code
- `account_status` (string): Estado de cuenta

**Quality problems injected:**

- ❌ Missing values ​​(5-15% depending on quality level)
- ❌ Empty strings en nombres y ciudad
- ❌ Duplicados exactos (2-8%)
- ❌ Invalid emails (ex:`john@@example.com`, `john.example`)
- ❌ Phones too short
- ❌ Fechas de nacimiento en el futuro
- ❌ Fechas de registro antes del nacimiento
- ❌ Invalid statuses (ex:`ACTIVE` en vez de `active`)

### 2. Transactions (50,000 registros)

**columns:**

- `transaction_id`(int): unique transaction ID
- `customer_id` (int): Customer ID (foreign key)
- `product_id` (int): Product ID (foreign key)
- `amount` (float): Monto unitario
- `quantity` (int): Cantidad
- `total` (float): Total (amount * quantity)
- `transaction_date` (datetime): Fecha de transaction
- `payment_method`(string): Payment method
- `status` (string): Estado
- `currency` (string): Moneda

**Quality problems injected:**

- ❌ Missing values ​​in critical fields (3-10%)
- ❌ Orphan foreign keys (customer_id que no existe: 5-15%)
- ❌ Amounts negativos (2%)
- ❌ Outliers extremos (muy altos o muy bajos)
- ❌ Invalid statuses
- ❌ Logical inconsistency:`total != amount * quantity` (3%)
- ❌ Fechas futuras (1%)
- ❌ Duplicados (5%)

### 3. Products (1,000 registros)

**columns:**

- `product_id`(int): Unique product ID
- `product_name` (string): Nombre del producto
- `category`(string): Category
- `price` (float): Precio de venta
- `cost` (float): Costo
- `stock_quantity` (int): Cantidad en stock
- `weight_kg` (float): Peso en kg
- `supplier_id` (int): ID del proveedor
- `is_active` (bool): Producto activo

**Quality problems injected:**

- ❌ Missing values (5-12%)
- ❌ Precios negativos (2%)
- ❌ Costo mayor que precio (8%)
- ❌ Stock negativo (1%)
- ❌ Duplicados (3%)
- ❌ Inconsistent categories (uppercase, empty)

## 🚀 Generate Data

### Installing dependencies

```bash
pip install pandas numpy faker pyarrow
```text

### Generar datasets

```bash
# Generar con calidad "poor" (muchos problemas)
python data/scripts/generate_data.py --quality poor

# Generar con calidad "medium" (problemas moderados)
python data/scripts/generate_data.py --quality medium

# Generar con calidad "clean" (sin problemas)
python data/scripts/generate_data.py --quality clean

# Especificar directorio de salida
python data/scripts/generate_data.py --quality poor --output data/samples
```

### Output

El script genera:

- Archivos CSV para facilidad de lectura
- Archivos Parquet para mejor performance
- Summary of quality problems found

## 📊 Quality Levels

### Clean (Sin problemas)

- ✅ 0% missing values
- ✅ 0% duplicates
- ✅ 100% valid formats
- ✅ 100% logical consistency

### Medium (Problemas moderados)

- ⚠️ 5% missing values
- ⚠️ 2% duplicates
- ⚠️ 3% invalid formats
- ⚠️ 5% orphan foreign keys

### Poor (Muchos problemas)

- ❌ 10-15% missing values
- ❌ 5-8% duplicates
- ❌ 10% invalid formats
- ❌ 15% orphan foreign keys
- ❌ Outliers, logical inconsistencies, etc.

## 💻 Use in Exercises

### Exercise 01: Data Profiling

```python
import pandas as pd

# Cargar datos
df = pd.read_csv('data/samples/customers_poor.csv')

# Analizar calidad
print(f"Total registros: {len(df)}")
print(f"Nulls por columna:\n{df.isnull().sum()}")
print(f"Duplicados: {df.duplicated().sum()}")
```text

### Exercise 02: Validation Rules

```python
# Validar reglas básicas
assert df['customer_id'].notna().all(), "customer_id no puede ser null"
assert (df['amount'] >= 0).all(), "amount debe ser positivo"
```text

### Exercise 03: Great Expectations

```python
import great_expectations as gx

context = gx.get_context()
validator = context.sources.add_pandas("my_datasource").read_csv(
    'data/samples/transactions_poor.csv'
)

validator.expect_column_values_to_not_be_null("transaction_id")
validator.expect_column_values_to_be_between("amount", min_value=0)
```text

## 🔍 Exploring the Data

### Pandas

```python
import pandas as pd

# Cargar
df = pd.read_parquet('data/samples/transactions_poor.parquet')

# Info básica
print(df.info())
print(df.describe())

# Problemas de calidad
print(f"\nNulls:\n{df.isnull().sum()}")
print(f"\nDuplicados: {df.duplicated().sum()}")
print(f"\nAmounts negativos: {(df['amount'] < 0).sum()}")
```

### DuckDB

```bash
duckdb -c "
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) as null_customer_id
FROM 'data/samples/transactions_poor.parquet'
"
```text

### Data Profiling

```python
from ydata_profiling import ProfileReport

df = pd.read_csv('data/samples/customers_poor.csv')
profile = ProfileReport(df, title="Customer Data Quality Report")
profile.to_file("customers_profile.html")
```text

## 📝 Esquemas Esperados

Ver `data/schemas/` para los JSON schemas que definen:

- columns requeridas
- Data types
- Valid ranges
- Formatos esperados
- Reglas de negocio

## ⚠️ Note on Synthetic Data

All data is **synthetic** generated with Faker:

- Nombres, emails, direcciones son ficticios
- They do not contain real or sensitive information
- Designed exclusively for training

## 🎓 resources Adicionales

- **theory/01-concepts.md**: Dimensiones de data quality
- **theory/02-architecture.md**: Frameworks (Great Expectations, PyDeequ)
- **exercises/**: Hands-on practices with this data

---

**Happy Data Quality Testing!** 🔍✨
