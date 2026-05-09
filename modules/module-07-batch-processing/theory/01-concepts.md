# Conceptos de Batch Processing

## 📚 What is Batch Processing?

**Batch Processing** is the processing of large volumes of data in **discrete batches**, usually in scheduled time windows (daily, weekly, monthly).

### features Clave

✅ **Alto throughput**: Procesa millones de registros eficientemente
✅ **high latency**: Minutes to hours between execution
✅ **Eficiencia de resources**: Optimizado para costos
✅ **Procesamiento offline**: No requiere respuesta inmediata

______________________________________________________________________

## 🆚 Batch vs Stream Processing

### Batch Processing

````text
[1M records] → Process → [Output]
     ↓          (1 hour)      ↓
  Collect                  Results
```text

**features**:

- ⏰ **latency**: High (hours/days)
- 📊 **Volume**: Muy alto (GB-TB)
- 💰 **Costo**: Bajo (resources bajo demanda)
- 🔧 **Complejidad**: Baja/Media

**Casos de uso**:

- Reportes diarios/semanales
- Data warehouse loads
- ML training pipelines
- Historical analysis
- ETL jobs nocturnos

### Stream Processing

```text
[Event] → Process → [Output]
  ↓       (ms)        ↓
Real-time         Immediate
````

**features**:

- ⏰ **latency**: Baja (ms-segundos)
- 📊 **Volume**: Continuo
- 💰 **Costo**: Alto (24/7)
- 🔧 **Complejidad**: Alta

**Casos de uso**:

- Real-time analytics
- Fraud detection
- IoT processing
- Live dashboards

### Micro-Batch (Hybrid)

````text
[100 events] → Process → [Output]
     ↓         (seconds)     ↓
  Every 5s              Results
```text

**Balance entre batch y streaming**:

- latency media (segundos-minutes)
- Usa infraestructura batch
- Simpler than pure streaming
- Usado por Spark Structured Streaming

---

## 🔄 Patrones de Batch Processing

### 1. Full Load (Carga Completa)

Procesar **todos los datos** cada vez:

```python
# Example: Daily full load
def daily_batch():
    # Read all historical data
    df = read_all_data()  # 100M records

    # Process everything
    result = transform(df)

    # Replace existing data
    write(result, mode='overwrite')
```text

**Pros**:

- ✅ Simple de implement
- ✅ Siempre consistente
- ✅ No state management

**Cons**:

- ❌ Lento para datasets grandes
- ❌ Desperdicia resources (reprocesa datos sin cambios)
- ❌ No scalable

**When to use**:

- Small datasets (< 10M records)
- Data que cambia completamente
- Cuando simplicidad > eficiencia

### 2. Incremental Load (Carga Incremental)

Procesar solo **datos nuevos o modificados**:

```python
# Example: Incremental batch
def incremental_batch():
    # Get last processed timestamp
    last_run = get_watermark()  # 2024-03-06 00:00:00

    # Read only new data
    df = read_data_since(last_run)  # 100K new records

    # Process only new data
    result = transform(df)

    # Append to existing data
    write(result, mode='append')

    # Update watermark
    set_watermark(now())
````

**Pros**:

- ✅ Fast (processes less data)
- ✅ Eficiente en resources
- ✅ scalable

**Cons**:

- ❌ Requiere watermark tracking
- ❌ More complex
- ❌ Puede perder deletes

**When to use**:

- Datos con timestamps
- Alto volumen de nuevos registros
- Cuando eficiencia importa

### 3. Change Data Capture (CDC)

Capturar y procesar **cambios** (inserts, updates, deletes):

````python
# Example: CDC batch processing
def cdc_batch():
    # Read change log from the last batch
    changes = read_cdc_log(since=last_run)

    for change in changes:
        if change.operation == 'INSERT':
            insert_record(change.new_values)
        elif change.operation == 'UPDATE':
            update_record(change.key, change.new_values)
        elif change.operation == 'DELETE':
            delete_record(change.key)
```text

**Pros**:

- ✅ Captura todos los cambios
- ✅ Incluye updates y deletes
- ✅ Mantiene historial

**Cons**:

- ❌ Requiere CDC infrastructure
- ❌ More complex to implement
- ❌ Necesita source system support

**Herramientas CDC**:

- Debezium (Kafka Connect)
- AWS DMS (Database Migration Service)
- Airbyte
- Fivetran

---

## 📊 Particionamiento de Datos

### Why Partition?

1. **Performance**: Leer solo particiones necesarias
2. **Parallelization**: Process partitions in parallel
3. **Maintainability**: Delete old partitions easily
4. **Costos**: Reducir data scanned

### Estrategias de Particionamiento

#### 1. Particionamiento por Fecha

```text
data/
  ├── year=2024/
  │   ├── month=01/
  │   │   ├── day=01/
  │   │   │   └── data.parquet
  │   │   ├── day=02/
  │   │   └── day=03/
  │   └── month=02/
  └── year=2025/
```text

```python
# Write partitioned data
df.write.partitionBy('year', 'month', 'day').parquet('data/')

# Read specific partition
df = spark.read.parquet('data/year=2024/month=03/day=07')
````

**Ventajas**:

- ✅ Natural para time-series data
- ✅ Easy to understand
- ✅ Eliminar datos antiguos simple

**Consideraciones**:

- ⚠️ Avoid many small partitions
- ⚠️ Balance entre granularidad y overhead

#### 2. Particionamiento por Rango

````python
# Partition por rangos de valores
def range_partition(value):
    if value < 1000:
        return 'small'
    elif value < 10000:
        return 'medium'
    else:
        return 'large'

df['partition'] = df['amount'].apply(range_partition)
```text

**Casos de uso**:

- Montos de transactions
- Edades de usuarios
- Scores de productos

#### 3. Particionamiento por Hash

```python
# Partition by hash for uniform distribution
df['partition'] = df['user_id'] % 10  # 10 partitions
```text

**Ventajas**:

- ✅ Uniform distribution
- ✅ Evita data skew
- ✅ Bueno para joins

#### 4. Category Partitioning

```text
data/
  ├── country=USA/
  ├── country=UK/
  └── country=Canada/
````

**Casos de uso**:

- By geographic region
- Por tipo de cliente
- By product category

______________________________________________________________________

## 🎯 Batch Processing Patterns

### Pattern 1: Batch Window

Process data in specific time windows:

````python
def process_daily_batch(date):
    """Process one day of data."""
    start = datetime(date.year, date.month, date.day)
    end = start + timedelta(days=1)

    df = read_data(start_date=start, end_date=end)
    transformed = transform(df)
    write_output(transformed, date=date)
```text

**Uso**: Daily/hourly batch jobs

### Pattern 2: Backfill

Reprocess historical data:

```python
def backfill(start_date, end_date):
    """Reprocess historical data."""
    date = start_date
    while date <= end_date:
        process_daily_batch(date)
        date += timedelta(days=1)
```text

**Uso**: Fix bugs, apply new logic to historical data

### Pattern 3: Idempotent Batch

Safe batch for re-execution:

```python
def idempotent_batch(date):
    """Safe to run multiple times."""
    # Delete existing output for this date
    delete_output(date)

    # Process and write
    df = read_data(date)
    transformed = transform(df)
    write_output(transformed, date=date)
```text

**Guarantee**: Multiple runs = same result

### Pattern 4: Checkpoint

Save progress for recovery:

```python
def batch_with_checkpoint():
    checkpoint = load_checkpoint()

    for partition in partitions[checkpoint:]:
        process(partition)
        checkpoint += 1
        save_checkpoint(checkpoint)
````

**Uso**: Batch jobs largos que pueden fallar

______________________________________________________________________

## 💾 Formatos de Archivo para Batch

### CSV

````python
df.to_csv('output.csv', index=False)
```text

**Pros**: Simple, human-readable
**Cons**: Lento, sin tipos, grande
**Use**: Small datasets, exports

### JSON

```python
df.to_json('output.json', orient='records', lines=True)
```text

**Pros**: Flexible schema, nested data
**Cons**: Lento, verboso
**Uso**: APIs, semi-structured data

### Parquet ⭐

```python
df.to_parquet('output.parquet', compression='snappy')
```text

**Pros**:

- ✅ Columnar (fast queries)
- ✅ Compressed
- ✅ Schema embedded
- ✅ Predicate pushdown

**Cons**: Requires library
**Uso**: Data lakes, analytics ⭐ RECOMENDADO

### Avro

```python
df.to_avro('output.avro')
````

**Pros**: Schema evolution, compact
**Cons**: Menos adoption
**Uso**: Streaming, Kafka

______________________________________________________________________

## 🔧 Chunking & Memory Management

### Problem: Dataset No Cabe en Memoria

````python
# ❌ Malo: Read todo en memoria
df = pd.read_csv('huge_file.csv')  # 50GB - OOM!
```text

### Solution: Chunking

```python
# ✅ Bueno: Procesa en chunks
chunk_size = 100000

for chunk in pd.read_csv('huge_file.csv', chunksize=chunk_size):
    # Procesa chunk (100K records cada vez)
    processed = transform(chunk)
    write_output(processed, mode='append')
```text

### Memory-Efficient Operations

```python
# Use specific dtypes
dtypes = {
    'user_id': 'int32',  # en lugar de int64
    'amount': 'float32',  # en lugar de float64
    'status': 'category'  # en lugar de object
}

df = pd.read_csv('file.csv', dtype=dtypes)
```text

---

## 📈 Best Practices

### 1. Particiona Inteligentemente

```python
# ✅ Bueno: Particiones balanceadas
df.write.partitionBy('year', 'month').parquet('data/')

# ❌ Bad: Too many small partitions
df.write.partitionBy('year', 'month', 'day', 'hour').parquet('data/')
````

**Regla**: 100MB - 1GB por partition file

### 2. Usa Formatos Columnar

````python
# ✅ Parquet para analytics
df.to_parquet('data.parquet', compression='snappy')

# ❌ CSV for large volumes
df.to_csv('data.csv')  # Lento y grande
```text

### 3. Procesa Incrementalmente

```python
# ✅ Solo datos nuevos
df = read_data_since(last_run)

# ❌ Reprocessa todo
df = read_all_data()
```text

### 4. Implement Idempotencia

```python
# ✅ Safe para re-runs
write(data, mode='overwrite', partition_key=date)

# ❌ Create duplicados
write(data, mode='append')
```text

### 5. Monitorea Performance

```python
import time

start = time.time()
result = process_batch(df)
duration = time.time() - start

logger.info(f"Batch completed in {duration:.2f}s")
logger.info(f"Records processed: {len(result)}")
logger.info(f"Throughput: {len(result)/duration:.2f} records/sec")
````

______________________________________________________________________

Continue with [02-architecture.md](./02-architecture.md) for batch architectures in the cloud.
