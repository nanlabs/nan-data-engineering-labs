# Conceptos Fundamentales de ETL

## 📚 What is ETL?

**ETL** stands for **Extract, Transform, Load** - the fundamental process in data engineering for moving and transforming data between systems.

### Las Tres Fases

#### 1. Extract
Extraer datos desde fuentes origen:
- **databases**: PostgreSQL, MySQL, Oracle
- **Archivos**: CSV, JSON, Excel, Parquet
- **APIs**: REST, GraphQL, SOAP
- **Logs**: Application logs, system logs
- **Streaming**: Kafka, Kinesis, Pub/Sub
- **Web scraping**: HTML parsing

#### 2. Transform
Procesar y limpiar datos:
- **Limpieza**: Eliminar nulls, duplicados, outliers
- **Validation**: Schema validation, data types
- **Enriquecimiento**: Joins, lookups, APIs externas
- **Aggregation**: Group by, pivots, rollups
- **Normalization**: Consistent format
- **Derivation**: Calculate new fields

#### 3. Load (Carga)
Escribir datos a destino:
- **Data Warehouse**: Snowflake, Redshift, BigQuery
- **Data Lake**: S3, ADLS, GCS
- **Databases**: PostgreSQL, MongoDB
- **Cache**: Redis, Memcached
- **Search**: Elasticsearch, Solr
- **BI Tools**: Tableau, PowerBI

---

## 🆚 ETL vs ELT

### ETL (Extract-Transform-Load)

**Transformation BEFORE loading**

```
Source → Extract → Transform → Load → Warehouse
```

**Ventajas**:
- ✅ Datos ya limpios en warehouse
- ✅ Menos carga en warehouse
- ✅ Schema validado anticipadamente
- ✅ Compliance and security made easier

**Desventajas**:
- ❌ Requiere server ETL potente
- ❌ Rigid schema
- ❌ Transformaciones complejas lentas

**Casos de uso**:
- Data Warehouses tradicionales (Oracle, SQL Server)
- Datos estructurados y schema fijo
- Transformaciones complejas
- Legacy systems

### ELT (Extract-Load-Transform)

**Transformation AFTER loading**

```
Source → Extract → Load → Data Lake → Transform
```

**Ventajas**:
- ✅ Fast loading (raw data)
- ✅ Schema flexible (schema-on-read)
- ✅ Aprovecha poder del warehouse moderno
- ✅ Raw data available for analysis

**Desventajas**:
- ❌ Requiere warehouse potente
- ❌ Higher storage costs
- ❌ Datos raw pueden tener calidad baja

**Casos de uso**:
- Cloud Data Warehouses (Snowflake, BigQuery)
- Data Lakes (S3, Azure Data Lake)
- Big Data y datos no estructurados
- Exploratory analysis

---

## 🔄 Batch vs Streaming ETL

### Batch ETL

**Processes data in periodic batches**

```python
# Ejemplo: ETL diario
while True:
    data = extract_yesterday_data()  # 1 día de datos
    transformed = transform(data)
    load(transformed)
    time.sleep(86400)  # Esperar 24 horas
```

**features**:
- ⏰ **latency**: High (hours/days)
- 📊 **throughput**: Alto (procesa mucho a la vez)
- 💰 **Costo**: Menor (resources bajo demanda)
- 🔧 **Complejidad**: Baja

**Casos de uso**:
- Reportes diarios/semanales
- Data warehouse nightly loads
- Historical analysis
- Machine learning training

### Streaming ETL

**Procesa datos en tiempo real**

```python
# Ejemplo: ETL en tiempo real
def process_event(event):
    transformed = transform(event)
    load(transformed)

consumer.subscribe('events')
for event in consumer:
    process_event(event)  # Procesa cada evento
```

**features**:
- ⏰ **latency**: Baja (segundos/milisegundos)
- 📊 **throughput**: Variable
- 💰 **Costo**: Mayor (resources 24/7)
- 🔧 **Complejidad**: Alta

**Casos de uso**:
- Real-time dashboards
- Fraud detection
- IoT data processing
- Live recommendations

### Mini-Batch (Micro-Batch)

**Hybrid: Frequent small batches**

```python
# Ejemplo: Procesar cada 5 minutos
while True:
    data = extract_last_5_minutes()
    transformed = transform(data)
    load(transformed)
    time.sleep(300)  # 5 minutos
```

**features**:
- ⏰ **latency**: Media (minutos)
- 📊 **throughput**: Alto
- 💰 **Costo**: Medio
- 🔧 **Complejidad**: Media

**Casos de uso**:
- Near real-time dashboards
- Data lake ingestion
- Spark Structured Streaming
- Balance entre batch y streaming

---

## 🎯 Tipos de Cargas

### Full Load (Carga Completa)

Cargar **todos los datos** cada vez:

```python
# Full load
df = extract_all_data()  # TODO
load(df, mode='replace')  # Reemplaza todo
```

**Ventajas**:
- ✅ Simple de implementar
- ✅ Siempre consistente
- ✅ No requiere tracking

**Desventajas**:
- ❌ Lento para tables grandes
- ❌ Alto uso de resources
- ❌ No scalable

**When to use**:
- small tables (< 1M rows)
- Datos que cambian completamente
- Static dimension tables

### Incremental Load (Carga Incremental)

Cargar solo **datos nuevos o modificados**:

```python
# Incremental load
last_run = get_last_watermark()  # 2024-03-06
df = extract_data_since(last_run)  # Solo nuevos
load(df, mode='append')
update_watermark(now())
```

**Ventajas**:
- ✅ Fast
- ✅ Eficiente en resources
- ✅ scalable

**Desventajas**:
- ❌ More complex
- ❌ Requiere watermark/timestamp
- ❌ Puede perder deletes

**When to use**:
- tables grandes
- Alto volumen de inserts
- Event logs, transactions

### Change Data Capture (CDC)

Capturar **cambios** (inserts, updates, deletes):

```python
# CDC
changes = extract_changes()  # Log de cambios
for change in changes:
    if change.type == 'INSERT':
        insert(change.data)
    elif change.type == 'UPDATE':
        update(change.data)
    elif change.type == 'DELETE':
        delete(change.key)
```

**Ventajas**:
- ✅ Captura todos los cambios
- ✅ Incluye deletes
- ✅ Near real-time
- ✅ Bajo impacto en source

**Desventajas**:
- ❌ Requiere soporte CDC en source
- ❌ Complejo de implementar
- ❌ Requiere infraestructura adicional

**Herramientas CDC**:
- Debezium (open source)
- AWS DMS
- Fivetran
- Airbyte

---

## 🔑 Conceptos Clave

### Idempotencia

A process is **idempotent** if running it multiple times produces the same result:

```python
# ❌ NO idempotente
df.to_sql('table', con, if_exists='append')
# Segunda ejecución → duplicados

# ✅ Idempotente
df.to_sql('table', con, if_exists='replace')
# Segunda ejecución → mismo resultado
```

**Why it is important**:
- Permite re-runs sin side effects
- Facilita recovery de errores
- Simplifica debugging

**How ​​to achieve idempotence**:
- Usar `replace` en lugar de `append`
- Implementar UPSERT (update or insert)
- Use unique transaction IDs
- Limpiar staging antes de cargar

### Data Lineage (Linaje de Datos)

**Tracking de origen y transformaciones** de los datos:

```
Source DB → Extract → Transform (join) → Load → Warehouse
   ↓           ↓            ↓               ↓         ↓
 Table A    Raw CSV    Enriched CSV     Staging   Final Table
```

**Why it is important**:
- 🔍 Debugging: Rastrear errores a origen
- 📊 Impact analysis: What affects a change
- 🔒 Compliance: Data audit
- 📈 Optimization: Identificar cuellos de botella

**Herramientas**:
- Apache Atlas
- Amundsen
- DataHub
- dbt docs

### Schema Evolution

**Cambios en estructura de datos** sin romper pipelines:

```python
# Schema V1
{'id': int, 'name': str, 'email': str}

# Schema V2 (nuevo campo)
{'id': int, 'name': str, 'email': str, 'phone': str}

# Pipeline debe manejar ambos
df['phone'] = df.get('phone', None)  # Default si no existe
```

**Tipos de cambios**:
- ✅ **Additive**: Agregar columns (safe)
- ⚠️ **Modification**: Cambiar tipos (risky)
- ❌ **Removal**: Eliminar columns (breaking)

**Best practices**:
- Siempre agregar, nunca remover
- Usar valores por defecto
- Versionar schemas
- Validar en runtime

### Data Quality

**Ensure that data is correct and useful**:

**Dimensiones de calidad**:
1. **Completeness**: Sin nulls donde no deben estar
2. **Accuracy**: Correct values ​​(valid email)
3. **Consistency**: Formato consistente
4. **Timeliness**: Datos frescos y actuales
5. **Uniqueness**: Sin duplicados
6. **Validity**: Cumple reglas de negocio

```python
# Data quality checks
assert df['email'].notnull().all(), "Nulls in email"
assert df['age'].between(0, 120).all(), "Invalid age"
assert ~df.duplicated('id').any(), "Duplicate IDs"
```

---

## 🏗️ Arquitectura de pipeline ETL

### Componentes

```
┌─────────────────────────────────────────────────────┐
│                 ETL ARCHITECTURE                     │
│                                                       │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│  │ SOURCES  │ → │  STAGED  │ → │  TARGET  │     │
│  └──────────┘    └──────────┘    └──────────┘     │
│       ↓               ↓               ↓             │
│                                                       │
│  ┌──────────────────────────────────────────────┐  │
│  │         CROSS-CUTTING CONCERNS                │  │
│  ├──────────────────────────────────────────────┤  │
│  │ • Logging & Monitoring                        │  │
│  │ • Error Handling & Retry                      │  │
│  │ • Data Quality Checks                         │  │
│  │ • Metadata Management                         │  │
│  │ • Security & Compliance                       │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Layers

1. **Staging Layer**:
   - Datos raw sin transformar
   - Temporal (puede borrarse)
   - Para debugging y reprocessing

2. **Processing Layer**:
   - Transformaciones aplicadas
   - Business logic
   - Data quality checks

3. **Serving Layer**:
   - Datos listos para consumo
   - Optimizados para queries
   - High availability

---

## 📊 ETL Metrics

### Performance Metrics

- **throughput**: Registros/segundo procesados
- **Latency**: Tiempo desde extract hasta load
- **Duration**: Tiempo total del pipeline
- **Resource Usage**: CPU, memory, network

### Quality Metrics

- **Success Rate**: % de runs exitosos
- **Data Freshness**: Edad de los datos
- **Completeness**: % de campos poblados
- **Accuracy**: % of valid records

### Business Metrics

- **SLA Compliance**: % de deadlines cumplidos
- **Cost per Record**: $ por registro procesado
- **Time to Insight**: Tiempo desde evento hasta dashboard

---

## ✅ Best Practices

### 1. Design for Failure

```python
try:
    data = extract()
    transformed = transform(data)
    load(transformed)
except Exception as e:
    log_error(e)
    alert_team()
    raise  # Re-raise para que orchestrator lo maneje
```

### 2. Make it Idempotent

```python
# Usar upsert en lugar de insert
def upsert(df, table):
    # Delete existing
    conn.execute(f"DELETE FROM {table} WHERE id IN ({df['id']})")
    # Insert new
    df.to_sql(table, conn, if_exists='append')
```

### 3. Log Everything

```python
import logging

logger.info(f"Extracting from {source}")
logger.info(f"Extracted {len(df)} records")
logger.info(f"Transformed {len(transformed)} records")
logger.info(f"Loaded to {destination}")
```

### 4. Validate Early

```python
# Validate después de extract
assert len(df) > 0, "No data extracted"
assert df['key'].notnull().all(), "Nulls in key column"
```

### 5. Monitor Actively

```python
# Enviar métricas
metrics.gauge('etl.records_processed', len(df))
metrics.timing('etl.duration', duration)
metrics.increment('etl.success')
```

---

This document covers the fundamental concepts. Continue with [02-patterns.md](./02-patterns.md) for implementation patterns.
