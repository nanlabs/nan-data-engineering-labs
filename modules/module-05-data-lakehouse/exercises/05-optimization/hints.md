# 💡 Hints - Ejercicio 05: Optimization

## 🎯 Conceptos Clave

### Optimization in Delta Lake
Delta Lake provides several techniques to optimize performance:
- **OPTIMIZE**: Compact small files (reduce small file problem)
- **Z-ORDERING**: Co-localiza datos relacionados (mejora data skipping)
- **VACUUM**: Limpia archivos antiguos no referenciados
- **Data Skipping**: Automatic based on statistics

### Small File Problem
Many small files → Metadata overhead → Slow queries
**Fix**: OPTIMIZE compacts files into larger files

### Z-Ordering
Co-locates related data based on multiple columns
**Benefit**: Reduce data read in queries with multiple filters

---

## 📝 optimization.py

### 1. Ver estado actual
```python
from delta.tables import DeltaTable

delta_table = DeltaTable.forPath(spark, path)
detail = delta_table.detail()

# Métricas importantes
detail.select(
    "numFiles",           # Número de archivos
    "sizeInBytes",        # Tamaño total
    "partitionColumns"    # Columnas de particionamiento
).show(truncate=False)

# También puedes ver
detail.select(
    "format",             # delta
    "createdAt",          # Cuándo se creó
    "minReaderVersion",   # Versión mínima reader
    "minWriterVersion"    # Versión mínima writer
).show(truncate=False)
```

### 2. OPTIMIZE - Compaction
```python
# Compactar todos los archivos
delta_table.optimize().executeCompaction()

# Ver resultado
metrics = delta_table.optimize().executeCompaction()
print(f"Files compacted: {metrics.metrics}")

# Compactar solo partición específica
delta_table.optimize() \
    .where("date = '2024-01-15'") \
    .executeCompaction()
```

**How ​​it works:**
- Read small files from the same partition
- Combines them into larger files (target: 1GB)
- Create new version (old files removable with VACUUM)

**When to use:**
- After many small appends
- After streaming with micro-batches
- Antes de queries heavy de analytics

### 3. Z-ORDER
```python
# Z-ORDER por una columna
delta_table.optimize().executeZOrderBy("country")

# Z-ORDER por múltiples columnas
delta_table.optimize().executeZOrderBy("country", "date", "customer_id")

# Z-ORDER en partición específica
delta_table.optimize() \
    .where("year = '2024' AND month = '01'") \
    .executeZOrderBy("country", "product_id")
```

**When to use Z-ORDER:**
- columns usadas frecuentemente en WHERE
- columns con alta cardinalidad
- Multiple filter columns in queries
- NO en columns ya particionadas (redundante)

**Ejemplo:**
```python
# Query: SELECT * FROM table WHERE country = 'USA' AND date = '2024-01-15'
# Z-ORDER por: country, date
delta_table.optimize().executeZOrderBy("country", "date")

# Mejora: Z-ordering co-locates USA + 2024-01-15 data
# Result: Data skipping lee menos archivos
```

### 4. Verificar mejoras
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

# Calcular mejora
files_before = detail_before.select("numFiles").collect()[0][0]
files_after = detail_after.select("numFiles").collect()[0][0]
reduction = (1 - files_after/files_before) * 100
print(f"📉 Reducción de archivos: {reduction:.1f}%")
```

### 5. Test de performance
```python
import time

df = spark.read.format("delta").load(path)

# Query 1: Sin optimización
start = time.time()
count1 = df.filter("country = 'USA' AND date = '2024-01-15'").count()
time1 = time.time() - start

# OPTIMIZE + Z-ORDER
delta_table.optimize().executeZOrderBy("country", "date")

# Query 2: Con optimización
df_optimized = spark.read.format("delta").load(path)
start = time.time()
count2 = df_optimized.filter("country = 'USA' AND date = '2024-01-15'").count()
time2 = time.time() - start

# Comparar
speedup = time1 / time2
print(f"⚡ Speedup: {speedup:.2f}x ({time1:.3f}s → {time2:.3f}s)")
```

### 6. VACUUM
```python
from delta.tables import DeltaTable

delta_table = DeltaTable.forPath(spark, path)

# Ver historial de archivos
history = delta_table.history()
print(f"Versiones: {history.count()}")

# VACUUM con retention (default 7 días = 168 horas)
delta_table.vacuum()  # Borra archivos > 7 días no referenciados

# VACUUM más agresivo (30 días)
delta_table.vacuum(24 * 30)  # 30 días en horas

# VACUUM todo (⚠️ SOLO PARA TESTING)
# Deshabilitar check de retention
spark.conf.set("spark.databricks.delta.retentionDurationCheck.enabled", "false")
delta_table.vacuum(0)  # Borra TODO no referenciado en versión actual

# Re-habilitar check
spark.conf.set("spark.databricks.delta.retentionDurationCheck.enabled", "true")
```

**⚠️ CAUTION with VACUUM:**
- Delete physical files → You CANNOT Time Travel vacuumed versions
- Puede romper operaciones concurrentes (usa retention adecuado)
- In production: NEVER use vacuum(0), use 168+ hours

**Ejemplo seguro:**
```python
# Retener 30 días de history
delta_table.vacuum(24 * 30)

# O configurar globalmente
spark.conf.set(
    "spark.databricks.delta.deletedFileRetentionDuration",
    "interval 30 days"
)
```

---

## 🚨 Errores Comunes

### Error 1: VACUUM muy agresivo
```
AnalysisException: Are you sure you want to vacuum files with such a low retention period?
```
**Solution:** Disable check (for testing only):
```python
spark.conf.set("spark.databricks.delta.retentionDurationCheck.enabled", "false")
```

### Error 2: Z-ORDER en column particionada
```python
# ❌ MAL - date ya es partition column
delta_table.optimize().executeZOrderBy("date")

# ✅ BIEN - Z-ORDER en otras columnas
delta_table.optimize().executeZOrderBy("country", "customer_id")
```

### Error 3: OPTIMIZE sin suficiente memoria
```
OutOfMemory: Not enough memory to execute compaction
```
**Solution:** Optimize by partition:
```python
# En lugar de
delta_table.optimize().executeCompaction()

# Hacer
for partition in partitions:
    delta_table.optimize() \
        .where(f"date = '{partition}'") \
        .executeCompaction()
```

### Error 4: Data skipping no funciona
```python
# ❌ MAL - columna string sin Z-ORDER
df.filter("description LIKE '%keyword%'")  # Full scan

# ✅ BIEN - columna con Z-ORDER
df.filter("country = 'USA'")  # Data skipping works
```

---

## 📚 Conceptos Avanzados

### Auto Optimize
```python
# Habilitar auto OPTIMIZE en tabla
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
```

### Optimized Writes
```python
# Optimiza tamaño de archivos al escribir
df.write.format("delta") \
    .option("optimizeWrite", "true") \
    .mode("append") \
    .save(path)

# Resultado: Archivos más grandes desde el principio
```

### Data Skipping Statistics
```python
# Ver statistics usadas para skipping
detail = delta_table.detail()
detail.select("numFiles", "statistics").show(truncate=False)

# Statistics incluyen:
# - numRecords: Registros por archivo
# - minValues: Valores mínimos por columna
# - maxValues: Valores máximos por columna
# - nullCount: Conteo de nulls

# Querying usa estas stats para skip archivos completos
```

### Partition Pruning vs Data Skipping
```python
# Partition Pruning: Elimina particiones completas
# - Basado en estructura de directorios
# - Muy eficiente, overhead mínimo
df.filter("year = 2024")  # Pruning de carpetas

# Data Skipping: Elimina archivos dentro de particiones
# - Basado en statistics (min/max)
# - Requiere leer metadata
df.filter("country = 'USA'")  # Skipping de archivos

# Combinación óptima
df.filter("year = 2024 AND country = 'USA'")
# 1. Pruning elimina years != 2024
# 2. Skipping elimina files sin USA dentro de 2024
```

### Bloom Filters (Advanced)
```python
# Para columnas de alta cardinalidad (IDs, emails)
spark.sql(f"""
    ALTER TABLE delta.`{path}`
    SET TBLPROPERTIES (
        'delta.bloomFilter.column1' = 'customer_id',
        'delta.bloomFilter.customer_id.numItems' = '1000000',
        'delta.bloomFilter.customer_id.fpp' = '0.01'
    )
""")

# Queries por customer_id ahora usan Bloom Filter
df.filter("customer_id = '12345'")  # Muy rápido
```

---

## 📊 Monitoring y Metrics

### View OPTIMIZE metrics
```python
result = delta_table.optimize().executeCompaction()

# Acceder a métricas
metrics = result.metrics
print(f"Files added: {metrics.get('numFilesAdded', 0)}")
print(f"Files removed: {metrics.get('numFilesRemoved', 0)}")
print(f"Bytes added: {metrics.get('numBytesAdded', 0)}")
print(f"Bytes removed: {metrics.get('numBytesRemoved', 0)}")
```

### View Z-ORDER metrics
```python
result = delta_table.optimize().executeZOrderBy("country", "date")
metrics = result.metrics

print(f"Z-ORDER statistics:")
print(f"  Files rewritten: {metrics.get('numFilesRemoved', 0)}")
print(f"  Bytes rewritten: {metrics.get('numBytesAdded', 0)}")
```

### Query Metrics
```python
# Ver qué archivos se leyeron
df = spark.read.format("delta").load(path)
result = df.filter("country = 'USA'").count()

# En Spark UI:
# - "number of files read"
# - "size of files read MB"
# - "data skipping files pruned"
```

---

## ✅ Checklist de Completitud

- [ ] Estado inicial muestra numFiles y sizeInBytes
- [ ] OPTIMIZE reduces number of files
- [ ] Z-ORDER se aplica correctamente a columns apropiadas
- [ ] Status after optimization shows improvements
- [ ] Test de performance muestra speedup
- [ ] VACUUM ejecuta sin errores
- [ ] Code handles retentionDurationCheck appropriately
- [ ] No hay errors de memoria en OPTIMIZE
