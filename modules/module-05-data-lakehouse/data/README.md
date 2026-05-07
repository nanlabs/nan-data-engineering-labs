# 📊 Datasets - Module 05: data Lakehouse

This directory contains **synthetic datasets** generated to practice data Lakehouse concepts with **Apache Spark**, **Delta Lake** and **Iceberg**.

## 📁 Structure of Directorios

```text
data/
├── raw/                    # Datas brutos generados (Bronze layer)
│   ├── transactions.json   # Transacciones e-commerce (300K records)
│   ├── events.json         # Events of users (200K records)
│   └── logs.jsonl          # Logs of aplicaciones (100K records)
├── schemas/                # Esquemas JSON of los datas
│   ├── transactions.json   # Schema for transacciones
│   ├── events.json         # Schema for events
│   └── logs.json           # Schema for logs
├── scrIPts/                # ScrIPts of generación of datas
│   ├── generate_transactions.py
│   ├── generate_events.py
│   ├── generate_logs.py
│   └── generate_all_datasets.py  # ScrIPt maestro
└── README.md              # this archivo
```text

## 🎯 Datasets Disponibles

### 1. 💳 E-Commerce Transactions (`transactions.json`)

**DescrIPtion**: e-commerce transactions with product, user, payment and location information.

**Size**: ~300,000 records (~40 MB)

**Campos PrincIPales**:

- `transaction_id`(UUID): Unique transaction identifier
- `user_id` (U0000123456): Identificador of user
- `product_id` (P00012345): Identificador of producto
- `product_name`: Nombre of the producto
- `category`: Product Category (Electronics, Clothing, etc.)
- `price`: Precio unitario in USD
- `quantity`: Cantidad comprada
- `total_amount`: Monto total (price × quantity)
- `payment_method`: Payment method (cnetworkit_card, paypal, etc.)
- `status`: Estado (completed, pending, cancelled, refunded, failed)
- `timestamp`: Fecha and hora of la transaction (ISO 8601)
- `country`: Country code (ISO 3166-1 alpha-2)
- `city`: Ciudad
- `IP_address`: Client IP address
- `device_type`: TIPo of dispositivo (desktop, mobile, tablet)
- `browser`: Navegador utilizado

**Casos of Uso**:

- Sales analysis by category
- Fraud detection
- Customer segmentation
- Purchasing behavior analysis
- Inventory optimization

---

### 2. 🌐 User Events (`events.json`)

**DescrIPtion**: Clickstream events of users browsing an e-commerce platform.

**Size**: ~200,000 records (~35 MB)

**Campos PrincIPales**:

- `event_id`(UUID): Unique event identifier
- `user_id` (U0000123456): Identificador of user
- `session_id`(UUID): Session identifier
- `event_type`: TIPo of event (page_view, click, search, add_to_cart, checkout, purchase, etc.)
- `page_url`: URL of the page where the event occurnetwork
- `referrer_url`: URL of reference (opcional)
- `timestamp`: Fecha and hora of the event (ISO 8601 with microsegundos)
- `user_agent`: User agent string completo
- `IP_address`: Client IP address
- `country`: Country code
- `device_type`: TIPo of dispositivo
- `os`: Sistopic operativo (Windows, macOS, Linux, iOS, Android)
- `browser`: Navegador
- `screen_width`, `screen_height`: Screen resolution
- `event_data`: Additional event-specific data (JSON)

**Casos of Uso**:

- Conversion funnel analysis
- User segmentation by behavior
- to/B testing and UX optimization
- Cart abandonment analysis
- Navigation patterns

---

### 3. 📝 Application Logs (`logs.jsonl`)

**DescrIPtion**: Microservices application logs with different levels of severity.

**Size**: ~100,000 records (~25 MB)

**Format**: JSON Lines (one line per log entry)

**Campos PrincIPales**:

- `log_id`(UUID): Unique log identifier
- `timestamp`: Fecha and hora of the log (ISO 8601 with microsegundos)
- `level`: Nivel of severidad (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `service`: Nombre of the service (api-gateway, auth-service, payment-service, etc.)
- `host`: Hostname or IP of the server
- `process_id`: ID of the process
- `thread_id`: ID of the thread
- `message`: Mensaje of the log
- `error_code`: Error code (optional, format: ERR5001, WRN2003)
- `stack_trace`: Stack trace completo (opcional, for errores)
- `user_id`: ID of user asociado (opcional)
- `request_id` (UUID): ID of request for tracing (opcional)
- `duration_ms`: Duration of the operation in milliseconds (optional)
- `HTTP_status`: HTTP status code (optional)
- `endpoint`: API endpoint (opcional)
- `method`: HTTP method (GET, POST, etc.)
- `IP_address`: IP of the client (opcional)
- `environment`: Entorno (development, staging, production)

**Casos of Uso**:

- Monitoring of errores and alerts
- Performance analysis (duration of requests)
- Troubleshooting and debugging
- Analysis of API usage patterns
- Anomaly detection

---

## ⚠️ Problems of Calidad of Datas (Intencionales)

The datasets contain **~12% of records with quality problems** to practice cleaning techniques on the Medallion architecture (Bronze → Silver → Gold).

### Problems Comunes in Todos los Datasets

1. **Valores Nulos** (Missing Requinetwork Fields)
   - Campos obligatorios with valores `null`
   - Example: `user_id: null`, `timestamp: null`

2. **Duplicados**
   - IDs duplicados (2-3% of records)
   - Example: Mismo `transaction_id` aparece 2+ veces

3. **Invalid Formats**
   - IDs malformados: `"INVALID1234"` in lugar of `"U0000123456"`
   - Invalid timestamps:`"2024-13-45T25:99:99Z"`
   - URLs malformadas: `"not-to-valid-url"`

4. **Valores Fuera of Rango**
   - Fechas futuras (clock drift simulado)
   - Negative values ​​where they should not exist
   - Outliers extremos

5. **Logical Inconsistencies**
   - `total_amount ≠ price × quantity`
   - Sesiones inconsistentes (mismo user, event logout with misma session_id)
   - Service name not coincide with host

6. **Empty Strings**
   - Campos with `""`instead of valid values
   - Mensajes truncados or incompletos

### Dataset Specific Problems

#### Transactions

- ✗ Precios negativos
- ✗ Cantidades irrealistas (>1000)
- ✗ Total amount inconsistente with price × quantity
- ✗ IDs of producto/user malformados

#### Events

- ✗ Invalid or empty event types
- ✗ URLs malformadas
- ✗ Resoluciones of pantalla irrealistas (>50000px)
- ✗ Dimensiones negativas

#### Logs

- ✗ Invalid log levels (`"debug"`, `"err"`, `"UNKNOWN"`)
- ✗ Invalid HTTP status codes (0, 999, -200)
- ✗ Duraciones negativas
- ✗ Empty messages
- ✗ ERROR/CRITICAL without stack trace

---

## 🚀 data Generation

### Prerrequisitos

Instala las dependencias of Python:

```bash
pIP install faker mimesis
```text

### Generar Todos los Datasets

```bash
cd data/scrIPts
python generate_all_datasets.py
```

This master scrIPt will run all 3 generators in sequence.

### Generar Datasets Individuales

```bash
# only transacciones (300K records, ~2-3 minutos)
python generate_transactions.py

# only events (200K records, ~2 minutos)
python generate_events.py

# only logs (100K records, ~1 minuto)
python generate_logs.py
```text

---

## 📖 Uso in Exercises

### 1️⃣ Bronze Layer (Raw data Ingestion)

Load the data as is, without transformations:

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("BronzeLayer") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

# Leer datas crudos
transactions_df = spark.read.json("data/raw/transactions.json")

# Escribir to Bronze layer (Delta Lake)
transactions_df.write \
    .format("delta") \
    .mode("append") \
    .save("s3a://bronze/transactions")
```text

### 2️⃣ Silver Layer (data Cleaning & Validation)

Limpia los datas and aplica validaciones:

```python
from pyspark.sql import functions as F

# Leer desde Bronze
bronze_df = spark.read.format("delta").load("s3a://bronze/transactions")

# Limpieza of datas
silver_df = bronze_df \
    .filter(F.col("transaction_id").isNotNull()) \
    .filter(F.col("user_id").rlike("^U[0-9]{10}$")) \
    .filter(F.col("price") > 0) \
    .filter(F.col("quantity") > 0) \
    .filter(F.col("timestamp").cast("timestamp").isNotNull()) \
    .withColumn("total_amount", F.col("price") * F.col("quantity")) \
    .dropDuplicates(["transaction_id"])

# Escribir to Silver layer
silver_df.write \
    .format("delta") \
    .mode("overwrite") \
    .save("s3a://silver/transactions")
```text

### 3️⃣ Gold Layer (Business Aggregations)

Create aggregate metrics for analysis:

```python
# Leer desde Silver
silver_df = spark.read.format("delta").load("s3a://silver/transactions")

# Agregación diaria of ventas
gold_df = silver_df \
    .withColumn("date", F.to_date(F.col("timestamp"))) \
    .groupBy("date", "category") \
    .agg(
        F.count("*").alias("num_transactions"),
        F.sum("total_amount").alias("total_sales"),
        F.avg("total_amount").alias("avg_transaction_value"),
        F.countDistinct("user_id").alias("unique_customers")
    )

# Escribir to Gold layer
gold_df.write \
    .format("delta") \
    .mode("overwrite") \
    .partitionBy("date") \
    .save("s3a://gold/daily_sales_by_category")
```

---

## 📊 Esquemas JSON

Los esquemas JSON in `schemas/` definen la structure esperada of cada dataset usando **JSON Schema Draft 7**:

- **transactions.json**: Schema for transactions e-commerce
- **events.json**: Schema for events of users
- **logs.json**: Schema for logs of aplicaciones

These schemes are useful for:

- data validation with Great Expectations
- Documentation generation
- Schema evolution
- Testing of compatibilidad

### Use of Schemas for Validation

```python
import json
from pyspark.sql import types as T

# Cargar schema
with open("data/schemas/transactions.json") as f:
    schema_def = json.load(f)

# Convertir to PySpark schema
spark_schema = T.StructType([
    T.StructField("transaction_id", T.StringType(), False),
    T.StructField("user_id", T.StringType(), False),
    T.StructField("product_id", T.StringType(), False),
    # ... more campos
])

# Leer with schema enforcement
df = spark.read.schema(spark_schema).json("data/raw/transactions.json")
```text

---

## 🎓 Exercises Recomendados

1. **data Quality Assessment** (⭐)
   - Identifica todos los tIPos of problems of calidad
   - Calcula porcentajes of records with cada tIPo of problem
   - Crea un reporte of calidad

2. **Bronze → Silver pIPeline** (⭐⭐⭐)
   - Implementa pIPeline completo of limpieza
   - Aplica todas las validaciones
   - Documenta las transformaciones

3. **Silver → Gold Aggregations** (⭐⭐⭐)
   - Create business metrics (daily sales, KPIs)
   - Implementa particionamiento inteligente
   - Optimiza with Z-ordering

4. **Time Travel & Audit** (⭐⭐⭐⭐)
   - Implement auditing with Delta Lake history
   - Practica rolelback of datas
   - Compara versiones with time travel

5. **Schema Evolution** (⭐⭐⭐⭐)
   - Agrega nuevos campos without romper pIPelines
   - Practica changes of tIPo of datas
   - Implementa estrategias of compatibilidad

6. **Iceberg Comparison** (⭐⭐⭐⭐⭐)
   - Carga mismos datas in Iceberg
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

### Problem: Build scrIPt fails with "Module not found"

**Solution**: Install the dependencies:

```bash
pIP install -r ../requirements.txt
```text

### Problem: Out of memory during generation

**Solution**: Networkuce the number of records in the constants of each scrIPt:

```python
# in generate_transactions.py
NUM_RECORDS = 100000  # Networkucir of 300K to 100K
```text

### Problem: Archivos JSON muy grandes for procesar

**Solution**:

1. Usa PySpark in lugar of pandas/Python puro
2. Procesa in chunks
3. Usa formato Parquet in lugar of JSON

### Problem: I want regenerar datas with diferentes seeds

**Solution**: Change the seeds in each scrIPt:

```python
Faker.seed(42)  # Cambia this número
random.seed(42)  # Cambia this número
```

---

## 📚 References

- [Faker Documentation](HTTPs://faker.readthedocs.io/)
- [JSON Schema](HTTPs://json-schema.org/)
- [Delta Lake - data Quality](HTTPs://docs.delta.io/latest/delta-constraints.html)
- [Great Expectations](HTTPs://docs.greatexpectations.io/)

---

## 💡 TIPs

1. **Quick data Inspection**:

   ```bash
   # Primeras 5 líneas
   head -n 5 data/raw/transactions.json | jq .
   
   # Contar records
   wc -l data/raw/*.json
   ```text

2. **JSON Validation**:

   ```bash
   # Verificar if el JSON is válido
   jq empty data/raw/transactions.json
   ```

3. **Search for specific problems**:

   ```bash
   # Buscar nulls
   grep "null" data/raw/transactions.json | head -n 10
   
   # Buscar precios negativos
   grep '"price": -' data/raw/transactions.json | head -n 10
   ```text

4. **Uso of Docker for procesamiento**:

   ```bash
   # Levantar infrastructure
   cd ../infrastructure
   docker-compose up -d
   
   # Acceder to Jupyter Lab
   open HTTP://localhost:8888
   ```

---

Enjoy practicing with the datasets! 🚀

If you encounter problems or have suggestions, review the exercises or query the documentation at`theory/`.
