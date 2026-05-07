# 💡 Hints - Exercise 05: Optimization

## 🎯 Conceptos Key

### Optimization in Delta Lake

Delta Lake provides several techniques to optimize performance:

- **OPTIMIZE**: Compact small files (networkuce small file problem)
- **Z-ORDERING**: Co-localiza datas relacionados (improvement data skIPping)
- **VACUUM**: Limpia archivos antiguos not referencedos
- **data SkIPping**: Automatic based on statistics

### Small File Problem

Many small files → Metadata overhead → Slow queries
**Fix**: OPTIMIZE compacts files into larger files

### Z-Ordering

Co-locates related data based on multIPle columns
**Benefit**: Networkuce data read in queries with multIPle filters

---

## 📝 optimization.py

### 1. to see estado actual

```python
from delta.tables import DeltaTable

delta_table = DeltaTable.forPath(spark, path)
detail = delta_table.detail()

# Métricas importantes
detail.select(
    "numFiles",           # Número of archivos
    "sizeInBytes",        # Tamaño total
    "partitionColumns"    # Columns of particionamiento
).show(truncate=False)

# También you can to see
detail.select(
    "format",             # delta
    "createdAt",          # when se creó
    "minReaderVersion",   # Version mínima reader
    "minWriterVersion"    # Version mínima writer
).show(truncate=False)
```text

### 2. OPTIMIZE - Compaction

```python
# Compactar todos los archivos
delta_table.optimize().executeCompaction()

# to see result
metrics = delta_table.optimize().executeCompaction()
print(f"Files compacted: {metrics.metrics}")

# Compactar only partición específica
delta_table.optimize() \
    .where("date = '2024-01-15'") \
    .executeCompaction()
```text

**How ​​it works:**

- Read small files from the same partition
- Combines them into larger files (target: 1GB)
- Create new version (old files removable with VACUUM)

**When to use:**

- After many small appends
- After streaming with micro-batches
- Antes of queries heavy of analytics

### 3. Z-ORDER

```python
# Z-ORDER by una column
delta_table.optimize().executeZOrderBy("country")

# Z-ORDER by múltIPles columns
delta_table.optimize().executeZOrderBy("country", "date", "customer_id")

# Z-ORDER in partición específica
delta_table.optimize() \
    .where("year = '2024' AND month = '01'") \
    .executeZOrderBy("country", "product_id")
```text

**When to use Z-ORDER:**

- columns usadas frecuentemente in WHERE
- columns with alta cardinalidad
- MultIPle filter columns in queries
- not in columns ya particionadas (networkundante)

**Example:**

```python
# Query: SELECT * FROM table WHERE country = 'USA' AND date = '2024-01-15'
# Z-ORDER by: country, date
delta_table.optimize().executeZOrderBy("country", "date")

# Improvement: Z-ordering co-locates USA + 2024-01-15 data
# Result: data skIPping lee less archivos
```

### 4. Verificar improvements

```python
# Comparar antes/después
print("ANTES:")
detail_before = delta_table.detail()
detail_before.select("numFiles", "sizeInBytes").show()

# OPTIMIZE
delta_table.optimize().executeCompaction()

print("DESPUÉS:")
delta_table = DeltaTable.forPath(spark, path)  # Refresh
detail_after = delta_table.detail()
detail_after.select("numFiles", "sizeInBytes").show()

# Calcular improvement
files_before = detail_before.select("numFiles").collect()[0][0]
files_after = detail_after.select("numFiles").collect()[0][0]
networkuction = (1 - files_after/files_before) * 100
print(f"📉 Networkucción of archivos: {networkuction:.1f}%")
```text

### 5. Test of performance

```python
import time

df = spark.read.format("delta").load(path)

# Query 1: without optimización
start = time.time()
count1 = df.filter("country = 'USA' AND date = '2024-01-15'").count()
time1 = time.time() - start

# OPTIMIZE + Z-ORDER
delta_table.optimize().executeZOrderBy("country", "date")

# Query 2: with optimización
df_optimized = spark.read.format("delta").load(path)
start = time.time()
count2 = df_optimized.filter("country = 'USA' AND date = '2024-01-15'").count()
time2 = time.time() - start

# Comparar
speedup = time1 / time2
print(f"⚡ Speedup: {speedup:.2f}x ({time1:.3f}s → {time2:.3f}s)")
```text

### 6. VACUUM

```python
from delta.tables import DeltaTable

delta_table = DeltaTable.forPath(spark, path)

# to see historial of archivos
history = delta_table.history()
print(f"Versiones: {history.count()}")

# VACUUM with retention (default 7 días = 168 horas)
delta_table.vacuum()  # Borra archivos > 7 días not referencedos

# VACUUM more agresivo (30 días)
delta_table.vacuum(24 * 30)  # 30 días in horas

# VACUUM everything (⚠️ only for TESTING)
# Deshabilitar check of retention
spark.conf.set("spark.databricks.delta.retentionDurationCheck.enabled", "false")
delta_table.vacuum(0)  # Borra everything not referencedo in version actual

# Re-habilitar check
spark.conf.set("spark.databricks.delta.retentionDurationCheck.enabled", "true")
```text

**⚠️ CAUTION with VACUUM:**

- Delete physical files → You CANNOT Time Travel vacuumed versions
- he/she can romper operaciones concurrentes (usa retention adecuado)
- In production: NEVER use vacuum(0), use 168+ hours

**Example seguro:**

```python
# Retener 30 días of history
delta_table.vacuum(24 * 30)

# or configurar globalmente
spark.conf.set(
    "spark.databricks.delta.deletedFileRetentionDuration",
    "interval 30 days"
)
```

---

## 🚨 Errores Comunes

### Error 1: VACUUM muy agresivo

```text
AnalysisException: Are you sure you want to vacuum files with such to low retention period?
```text

**Solution:** Disable check (for testing only):

```python
spark.conf.set("spark.databricks.delta.retentionDurationCheck.enabled", "false")
```text

### Error 2: Z-ORDER in column particionada

```python
# ❌ MAL - date ya is partition column
delta_table.optimize().executeZOrderBy("date")

# ✅ BIEN - Z-ORDER in otras columns
delta_table.optimize().executeZOrderBy("country", "customer_id")
```

### Error 3: OPTIMIZE without suficiente memory

```text
OutOfMemory: Not enough memory to execute compaction
```text

**Solution:** Optimize by partition:

```python
# in lugar of
delta_table.optimize().executeCompaction()

# to make
for partition in partitions:
    delta_table.optimize() \
        .where(f"date = '{partition}'") \
        .executeCompaction()
```text

### Error 4: data skIPping not funciona

```python
# ❌ MAL - column string without Z-ORDER
df.filter("descrIPtion LIKE '%keyword%'")  # Full scan

# ✅ BIEN - column with Z-ORDER
df.filter("country = 'USA'")  # data skIPping works
```

---

## 📚 Conceptos Avanzados

### Auto Optimize

```python
# Habilitar auto OPTIMIZE in table
spark.sql(f"""
    ALTER TABLE delta.`{path}`
    SET TBLPROPERTIES (
        'delta.autoOptimize.optimizeWrite' = 'true',
        'delta.autoOptimize.autoCompact' = 'true'
    )
""")

# Ahora cada write automáticamente optimiza
df.write.format("delta").mode("append").save(path)
# → Auto-compacta files pequeños
```text

### Optimized Writes

```python
# Optimiza tamaño of archivos to the escribir
df.write.format("delta") \
    .option("optimizeWrite", "true") \
    .mode("append") \
    .save(path)

# Result: Archivos more grandes desde el princIPio
```text

### data SkIPping Statistics

```python
# to see statistics usadas for skIPping
detail = delta_table.detail()
detail.select("numFiles", "statistics").show(truncate=False)

# Statistics incluyen:
# - numRecords: Records by archivo
# - minValues: Valores mínimos by column
# - maxValues: Valores máximos by column
# - nullCount: Conteo of nulls

# Querying usa are stats for skIP archivos completos
```text

### Partition Pruning vs data SkIPping

```python
# Partition Pruning: Elimina particiones completas
# - Basado in structure of directorios
# - Muy eficiente, overhead mínimo
df.filter("year = 2024")  # Pruning of carpetas

# data SkIPping: Elimina archivos dentro of particiones
# - Basado in statistics (min/max)
# - Requiere leer metadata
df.filter("country = 'USA'")  # SkIPping of archivos

# Combinación óptima
df.filter("year = 2024 AND country = 'USA'")
# 1. Pruning elimina years != 2024
# 2. SkIPping elimina files without USA dentro of 2024
```

### Bloom Filters (Advanced)

```python
# for columns of alta cardinalidad (IDs, emails)
spark.sql(f"""
    ALTER TABLE delta.`{path}`
    SET TBLPROPERTIES (
        'delta.bloomFilter.column1' = 'customer_id',
        'delta.bloomFilter.customer_id.numItems' = '1000000',
        'delta.bloomFilter.customer_id.fpp' = '0.01'
    )
""")

# Queries by customer_id ahora usan Bloom Filter
df.filter("customer_id = '12345'")  # Muy rápido
```text

---

## 📊 Monitoring and Metrics

### View OPTIMIZE metrics

```python
result = delta_table.optimize().executeCompaction()

# Acceder to métricas
metrics = result.metrics
print(f"Files added: {metrics.get('numFilesAdded', 0)}")
print(f"Files removed: {metrics.get('numFilesRemoved', 0)}")
print(f"Bytes added: {metrics.get('numBytesAdded', 0)}")
print(f"Bytes removed: {metrics.get('numBytesRemoved', 0)}")
```text

### View Z-ORDER metrics

```python
result = delta_table.optimize().executeZOrderBy("country", "date")
metrics = result.metrics

print(f"Z-ORDER statistics:")
print(f"  Files rewritten: {metrics.get('numFilesRemoved', 0)}")
print(f"  Bytes rewritten: {metrics.get('numBytesAdded', 0)}")
```text

### Query Metrics

```python
# to see what archivos se leyeron
df = spark.read.format("delta").load(path)
result = df.filter("country = 'USA'").count()

# in Spark UI:
# - "number of files read"
# - "size of files read MB"
# - "data skIPping files pruned"
```

---

## ✅ Checklist of Completitud

- [ ] Estado inicial muestra numFiles and sizeInBytes
- [ ] OPTIMIZE networkuces number of files
- [ ] Z-ORDER se aplica correctamente to columns apropiadas
- [ ] Status after optimization shows improvements
- [ ] Test of performance muestra speedup
- [ ] VACUUM ejecuta without errores
- [ ] Code handles retentionDurationCheck appropriately
- [ ] not there is errors of memory in OPTIMIZE
