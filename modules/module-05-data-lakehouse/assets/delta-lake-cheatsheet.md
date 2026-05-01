# Delta Lake Cheatsheet

## 📝 Comandos Esenciales

### Crear table

```python
# Escribir DataFrame como Delta
df.write.format("delta").mode("overwrite").save("/path/to/table")

# Con particiones
df.write.format("delta").partitionBy("country", "date").save("/path")

# Con opciones
df.write.format("delta") \
    .option("mergeSchema", "true") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("/path")
```

### Leer table

```python
# Leer Delta table
df = spark.read.format("delta").load("/path/to/table")

# Leer versión específica (Time Travel)
df = spark.read.format("delta") \
    .option("versionAsOf", 2) \
    .load("/path")

# Leer por timestamp
df = spark.read.format("delta") \
    .option("timestampAsOf", "2024-01-15 10:00:00") \
    .load("/path")
```

### Operaciones DML

```python
from delta.tables import DeltaTable

delta_table = DeltaTable.forPath(spark, "/path/to/table")

# UPDATE
delta_table.update(
    condition = "status = 'pending'",
    set = {"status": "'completed'"}
)

# DELETE
delta_table.delete("amount < 0")

# MERGE (Upsert)
delta_table.alias("target").merge(
    source_df.alias("source"),
    "target.id = source.id"
).whenMatchedUpdate(set = {
    "amount": "source.amount"
}).whenNotMatchedInsert(values = {
    "id": "source.id",
    "amount": "source.amount"
}).execute()
```

### Metadatos

```python
# Ver historial de versiones
delta_table.history().show()

# Ver detalles de tabla
delta_table.detail().show()

# Ver archivos
delta_table.toDF().show()
```

### Optimization

```python
# Compactar archivos pequeños
delta_table.optimize().executeCompaction()

# Z-Ordering
delta_table.optimize().executeZOrderBy("country", "date")

# Limpiar versiones antiguas (retener 7 días)
delta_table.vacuum(168)  # horas

# Verificar estado
delta_table.detail().select("numFiles", "sizeInBytes").show()
```

### Schema Evolution

```python
# Permitir agregar columnas
df.write.format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .save("/path")

# Permitir cambios de schema completos
df.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save("/path")
```

### SQL

```sql
-- Crear tabla
CREATE TABLE events USING DELTA LOCATION '/path/to/table';

-- Time Travel
SELECT * FROM events VERSION AS OF 2;
SELECT * FROM events TIMESTAMP AS OF '2024-01-15';

-- Optimizar
OPTIMIZE events ZORDER BY (country, date);

-- Vacuum
VACUUM events RETAIN 168 HOURS;

-- Historial
DESCRIBE HISTORY events;
```

## 🔥 Tips Pro

1. **Partitioning**: Usar columns con cardinalidad media (country, date)
2. **Z-Ordering**: Aplicar a columns de filtros frecuentes
3. **Vacuum**: Be careful, it eliminates historical Time Travel
4. **mergeSchema**: Solo para esquemas compatibles (no breaking changes)
5. **OPTIMIZE**: Run after many small writes

## ⚠️ Advertencias

- VACUUM borra archivos necesarios para Time Travel
- overwriteSchema puede romper lectores existentes
- Z-Ordering es costoso, usar solo cuando necesario
- Partitions with many unique values ​​cause "small files problem"
