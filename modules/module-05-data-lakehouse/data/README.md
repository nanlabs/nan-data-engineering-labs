# 📊 Datasets - Module 05: Data Lakehouse

This directory contains **synthetic datasets** generated to practice Data Lakehouse concepts with **Apache Spark**, **Delta Lake** and **Iceberg**.

## 📁 Estructura de Directorios

```
data/
├── raw/                    # Datos brutos generados (Bronze layer)
│   ├── transactions.json   # Transacciones e-commerce (300K registros)
│   ├── events.json         # Eventos de usuarios (200K registros)
│   └── logs.jsonl          # Logs de aplicaciones (100K registros)
├── schemas/                # Esquemas JSON de los datos
│   ├── transactions.json   # Schema para transacciones
│   ├── events.json         # Schema para eventos
│   └── logs.json           # Schema para logs
├── scripts/                # Scripts de generación de datos
│   ├── generate_transactions.py
│   ├── generate_events.py
│   ├── generate_logs.py
│   └── generate_all_datasets.py  # Script maestro
└── README.md              # Este archivo
```

## 🎯 Datasets Disponibles

### 1. 💳 E-Commerce Transactions (`transactions.json`)

**Description**: e-commerce transactions with product, user, payment and location information.

**Size**: ~300,000 records (~40 MB)

**Campos Principales**:
- `transaction_id`(UUID): Unique transaction identifier
- `user_id` (U0000123456): Identificador de usuario
- `product_id` (P00012345): Identificador de producto
- `product_name`: Nombre del producto
- `category`: Product Category (Electronics, Clothing, etc.)
- `price`: Precio unitario en USD
- `quantity`: Cantidad comprada
- `total_amount`: Monto total (price × quantity)
- `payment_method`: Payment method (credit_card, paypal, etc.)
- `status`: Estado (completed, pending, cancelled, refunded, failed)
- `timestamp`: Fecha y hora de la transaction (ISO 8601)
- `country`: Country code (ISO 3166-1 alpha-2)
- `city`: Ciudad
- `ip_address`: Client IP address
- `device_type`: Tipo de dispositivo (desktop, mobile, tablet)
- `browser`: Navegador utilizado

**Casos de Uso**:
- Sales analysis by category
- Fraud detection
- Customer segmentation
- Purchasing behavior analysis
- Inventory optimization

---

### 2. 🌐 User Events (`events.json`)

**Description**: Clickstream events of users browsing an e-commerce platform.

**Size**: ~200,000 records (~35 MB)

**Campos Principales**:
- `event_id`(UUID): Unique event identifier
- `user_id` (U0000123456): Identificador de usuario
- `session_id`(UUID): Session identifier
- `event_type`: Tipo de evento (page_view, click, search, add_to_cart, checkout, purchase, etc.)
- `page_url`: URL of the page where the event occurred
- `referrer_url`: URL de referencia (opcional)
- `timestamp`: Fecha y hora del evento (ISO 8601 con microsegundos)
- `user_agent`: User agent string completo
- `ip_address`: Client IP address
- `country`: Country code
- `device_type`: Tipo de dispositivo
- `os`: Sistema operativo (Windows, macOS, Linux, iOS, Android)
- `browser`: Navegador
- `screen_width`, `screen_height`: Screen resolution
- `event_data`: Additional event-specific data (JSON)

**Casos de Uso**:
- Conversion funnel analysis
- User segmentation by behavior
- A/B testing and UX optimization
- Cart abandonment analysis
- Navigation patterns

---

### 3. 📝 Application Logs (`logs.jsonl`)

**Description**: Microservices application logs with different levels of severity.

**Size**: ~100,000 records (~25 MB)

**Format**: JSON Lines (one line per log entry)

**Campos Principales**:
- `log_id`(UUID): Unique log identifier
- `timestamp`: Fecha y hora del log (ISO 8601 con microsegundos)
- `level`: Nivel de severidad (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `service`: Nombre del service (api-gateway, auth-service, payment-service, etc.)
- `host`: Hostname o IP del server
- `process_id`: ID del proceso
- `thread_id`: ID del thread
- `message`: Mensaje del log
- `error_code`: Error code (optional, format: ERR5001, WRN2003)
- `stack_trace`: Stack trace completo (opcional, para errores)
- `user_id`: ID de usuario asociado (opcional)
- `request_id` (UUID): ID de request para tracing (opcional)
- `duration_ms`: Duration of the operation in milliseconds (optional)
- `http_status`: HTTP status code (optional)
- `endpoint`: API endpoint (opcional)
- `method`: HTTP method (GET, POST, etc.)
- `ip_address`: IP del cliente (opcional)
- `environment`: Entorno (development, staging, production)

**Casos de Uso**:
- Monitoreo de errores y alertas
- Performance analysis (duration of requests)
- Troubleshooting y debugging
- Analysis of API usage patterns
- Anomaly detection

---

## ⚠️ Problemas de Calidad de Datos (Intencionales)

The datasets contain **~12% of records with quality problems** to practice cleaning techniques on the Medallion architecture (Bronze → Silver → Gold).

### Problemas Comunes en Todos los Datasets:

1. **Valores Nulos** (Missing Required Fields)
   - Campos obligatorios con valores `null`
   - Ejemplo: `user_id: null`, `timestamp: null`

2. **Duplicados**
   - IDs duplicados (2-3% de registros)
   - Ejemplo: Mismo `transaction_id` aparece 2+ veces

3. **Invalid Formats**
   - IDs malformados: `"INVALID1234"` en lugar de `"U0000123456"`
   - Invalid timestamps:`"2024-13-45T25:99:99Z"`
   - URLs malformadas: `"not-a-valid-url"`

4. **Valores Fuera de Rango**
   - Fechas futuras (clock drift simulado)
   - Negative values ​​where they should not exist
   - Outliers extremos

5. **Logical Inconsistencies**
   - `total_amount ≠ price × quantity`
   - Sesiones inconsistentes (mismo user, evento logout con misma session_id)
   - Service name no coincide con host

6. **Empty Strings**
   - Campos con `""`instead of valid values
   - Mensajes truncados o incompletos

### Dataset Specific Problems:

#### Transactions:
- ✗ Precios negativos
- ✗ Cantidades irrealistas (>1000)
- ✗ Total amount inconsistente con price × quantity
- ✗ IDs de producto/usuario malformados

#### Events:
- ✗ Invalid or empty event types
- ✗ URLs malformadas
- ✗ Resoluciones de pantalla irrealistas (>50000px)
- ✗ Dimensiones negativas

#### Logs:
- ✗ Invalid log levels (`"debug"`, `"err"`, `"UNKNOWN"`)
- ✗ Invalid HTTP status codes (0, 999, -200)
- ✗ Duraciones negativas
- ✗ Empty messages
- ✗ ERROR/CRITICAL sin stack trace

---

## 🚀 Data Generation

### Prerrequisitos

Instala las dependencias de Python:

```bash
pip install faker mimesis
```

### Generar Todos los Datasets

```bash
cd data/scripts
python generate_all_datasets.py
```

This master script will run all 3 generators in sequence.

### Generar Datasets Individuales

```bash
# Solo transacciones (300K registros, ~2-3 minutos)
python generate_transactions.py

# Solo eventos (200K registros, ~2 minutos)
python generate_events.py

# Solo logs (100K registros, ~1 minuto)
python generate_logs.py
```

---

## 📖 Uso en Ejercicios

### 1️⃣ Bronze Layer (Raw Data Ingestion)

Load the data as is, without transformations:

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("BronzeLayer") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

# Leer datos crudos
transactions_df = spark.read.json("data/raw/transactions.json")

# Escribir a Bronze layer (Delta Lake)
transactions_df.write \
    .format("delta") \
    .mode("append") \
    .save("s3a://bronze/transactions")
```

### 2️⃣ Silver Layer (Data Cleaning & Validation)

Limpia los datos y aplica validaciones:

```python
from pyspark.sql import functions as F

# Leer desde Bronze
bronze_df = spark.read.format("delta").load("s3a://bronze/transactions")

# Limpieza de datos
silver_df = bronze_df \
    .filter(F.col("transaction_id").isNotNull()) \
    .filter(F.col("user_id").rlike("^U[0-9]{10}$")) \
    .filter(F.col("price") > 0) \
    .filter(F.col("quantity") > 0) \
    .filter(F.col("timestamp").cast("timestamp").isNotNull()) \
    .withColumn("total_amount", F.col("price") * F.col("quantity")) \
    .dropDuplicates(["transaction_id"])

# Escribir a Silver layer
silver_df.write \
    .format("delta") \
    .mode("overwrite") \
    .save("s3a://silver/transactions")
```

### 3️⃣ Gold Layer (Business Aggregations)

Create aggregate metrics for analysis:

```python
# Leer desde Silver
silver_df = spark.read.format("delta").load("s3a://silver/transactions")

# Agregación diaria de ventas
gold_df = silver_df \
    .withColumn("date", F.to_date(F.col("timestamp"))) \
    .groupBy("date", "category") \
    .agg(
        F.count("*").alias("num_transactions"),
        F.sum("total_amount").alias("total_sales"),
        F.avg("total_amount").alias("avg_transaction_value"),
        F.countDistinct("user_id").alias("unique_customers")
    )

# Escribir a Gold layer
gold_df.write \
    .format("delta") \
    .mode("overwrite") \
    .partitionBy("date") \
    .save("s3a://gold/daily_sales_by_category")
```

---

## 📊 Esquemas JSON

Los esquemas JSON en `schemas/` definen la estructura esperada de cada dataset usando **JSON Schema Draft 7**:

- **transactions.json**: Schema para transactions e-commerce
- **events.json**: Schema para eventos de usuarios
- **logs.json**: Schema para logs de aplicaciones

These schemes are useful for:
- Data validation with Great Expectations
- Documentation generation
- Schema evolution
- Testing de compatibilidad

### Use of Schemas for Validation

```python
import json
from pyspark.sql import types as T

# Cargar schema
with open("data/schemas/transactions.json") as f:
    schema_def = json.load(f)

# Convertir a PySpark schema
spark_schema = T.StructType([
    T.StructField("transaction_id", T.StringType(), False),
    T.StructField("user_id", T.StringType(), False),
    T.StructField("product_id", T.StringType(), False),
    # ... más campos
])

# Leer con schema enforcement
df = spark.read.schema(spark_schema).json("data/raw/transactions.json")
```

---

## 🎓 Ejercicios Recomendados

1. **Data Quality Assessment** (⭐)
   - Identifica todos los tipos de problemas de calidad
   - Calcula porcentajes de registros con cada tipo de problema
   - Crea un reporte de calidad

2. **Bronze → Silver pipeline** (⭐⭐⭐)
   - Implementa pipeline completo de limpieza
   - Aplica todas las validaciones
   - Documenta las transformaciones

3. **Silver → Gold Aggregations** (⭐⭐⭐)
   - Create business metrics (daily sales, KPIs)
   - Implementa particionamiento inteligente
   - Optimiza con Z-ordering

4. **Time Travel & Audit** (⭐⭐⭐⭐)
   - Implement auditing with Delta Lake history
   - Practica rollback de datos
   - Compara versiones con time travel

5. **Schema Evolution** (⭐⭐⭐⭐)
   - Agrega nuevos campos sin romper pipelines
   - Practica cambios de tipo de datos
   - Implementa estrategias de compatibilidad

6. **Iceberg Comparison** (⭐⭐⭐⭐⭐)
   - Carga mismos datos en Iceberg
   - Compara performance Delta vs Iceberg
   - Practica hidden partitioning

---

## 📈 Dataset Statistics

| Dataset | Records | Size | Nulls | Duplicates | Issues |
|---------------|-----------|----------|-------|------------|--------|
| Transactions  | ~300K     | ~40 MB   | ~10%  | ~3%        | ~12%   |
| Events        | ~200K     | ~35 MB   | ~8%   | ~2%        | ~12%   |
| Logs          | ~100K     | ~25 MB   | ~9%   | ~1.5%      | ~13%   |
| **Total**     | **~500K** | **~100 MB** | **~9%** | **~2.5%** | **~12%** |

---

## 🔧 Troubleshooting

### Problem: Build script fails with "Module not found"

**Solution**: Install the dependencies:

```bash
pip install -r ../requirements.txt
```

### Problem: Out of memory during generation

**Solution**: Reduce the number of records in the constants of each script:

```python
# En generate_transactions.py
NUM_RECORDS = 100000  # Reducir de 300K a 100K
```

### Problema: Archivos JSON muy grandes para procesar

**Solution**:
1. Usa PySpark en lugar de pandas/Python puro
2. Procesa en chunks
3. Usa formato Parquet en lugar de JSON

### Problema: Quiero regenerar datos con diferentes seeds

**Solution**: Change the seeds in each script:

```python
Faker.seed(42)  # Cambia este número
random.seed(42)  # Cambia este número
```

---

## 📚 Referencias

- [Faker Documentation](https://faker.readthedocs.io/)
- [JSON Schema](https://json-schema.org/)
- [Delta Lake - Data Quality](https://docs.delta.io/latest/delta-constraints.html)
- [Great Expectations](https://docs.greatexpectations.io/)

---

## 💡 Tips

1. **Quick Data Inspection**:
   ```bash
   # Primeras 5 líneas
   head -n 5 data/raw/transactions.json | jq .
   
   # Contar registros
   wc -l data/raw/*.json
   ```

2. **JSON Validation**:
   ```bash
   # Verificar si el JSON es válido
   jq empty data/raw/transactions.json
   ```

3. **Search for specific problems**:
   ```bash
   # Buscar nulls
   grep "null" data/raw/transactions.json | head -n 10
   
   # Buscar precios negativos
   grep '"price": -' data/raw/transactions.json | head -n 10
   ```

4. **Uso de Docker para procesamiento**:
   ```bash
   # Levantar infraestructura
   cd ../infrastructure
   docker-compose up -d
   
   # Acceder a Jupyter Lab
   open http://localhost:8888
   ```

---

Enjoy practicing with the datasets! 🚀

If you encounter problems or have suggestions, review the exercises or query the documentation at`theory/`.
