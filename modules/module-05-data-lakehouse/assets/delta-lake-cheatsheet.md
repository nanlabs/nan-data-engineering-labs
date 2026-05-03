# Delta Lake Cheatsheet

## 📝 Commands Esenciales

### Crear table

```python
# Escribir DataFrame como Delta
df.write.format("delta").mode("overwrite").save("/path/to/table")

# with particiones
df.write.format("delta").partitionBy("country", "date").save("/path")

# with opciones
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

# Leer version específica (Time Travel)
df = spark.read.format("delta") \
    .option("versionAsOf", 2) \
    .load("/path")

# Leer by timestamp
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

### Metadatas

```python
# to see historial of versiones
delta_table.history().show()

# to see detalles of table
delta_table.detail().show()

# to see archivos
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
# Permitir agregar columns
df.write.format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .save("/path")

# Permitir changes of schema completos
df.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save("/path")
```

### SQL

```sql
-- Crear table
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

## 🔥 TIPs Pro

1. **Partitioning**: Usar columns with cardinalidad media (country, date)
2. **Z-Ordering**: Aplicar to columns of filters frecuentes
3. **Vacuum**: Be careful, it elimiNATes historical Time Travel
4. **mergeSchema**: only for esquemas compatibles (not breaking changes)
5. **OPTIMIZE**: Run after many small writes

## ⚠️ Warnings

- VACUUM borra archivos necesarios for Time Travel
- overwriteSchema he/she can romper lectores existentes
- Z-Ordering is costoso, usar only when necesario
- Partitions with many unique values ​​cause "small files problem"
