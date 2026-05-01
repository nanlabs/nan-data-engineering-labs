# 💡 Hints - Ejercicio 03: Time Travel

## 🎯 Conceptos Clave

### Time Travel
Time Travel allows access to historical versions of a Delta table:
- **versionAsOf**: Access by version number
- **timestampAsOf**: Acceder por timestamp

### Operaciones que crean versiones
- `INSERT` (append/overwrite)
- `UPDATE` 
- `DELETE`
- `MERGE`

---

## 📝 01_create_versions.py

### Crear table inicial
```python
df = spark.read.json("../../../data/raw/transactions.json").limit(10000)
df.write.format("delta").mode("overwrite").save(path)
```

### Append datos
```python
# Leer 15K y quitar los primeros 10K
df_all = spark.read.json("../../../data/raw/transactions.json").limit(15000)
df_new = df_all.subtract(df)
df_new.write.format("delta").mode("append").save(path)
```

### Update con DeltaTable
```python
from delta.tables import DeltaTable
delta_table = DeltaTable.forPath(spark, path)
delta_table.update(
    condition="status = 'pending'",
    set={"status": "'expired'"}  # Nota las comillas simples internas
)
```

### Delete with condition
```python
delta_table.delete("amount < 0 OR amount IS NULL")
```

### Ver historial
```python
delta_table.history().select(
    "version", 
    "timestamp", 
    "operation", 
    "operationMetrics"
).show(truncate=False)
```

---

## 📊 02_time_travel_queries.py

### Query by version
```python
# Leer versión específica
v0 = spark.read.format("delta") \
    .option("versionAsOf", 0) \
    .load(path)
```

### Query por timestamp
```python
# Obtener timestamp del historial
delta_table = DeltaTable.forPath(spark, path)
history = delta_table.history().collect()
v1_timestamp = history[-2]['timestamp']  # Segunda versión (índice -2)

# Query usando timestamp
df_v1 = spark.read.format("delta") \
    .option("timestampAsOf", str(v1_timestamp)) \
    .load(path)
```

### SQL Time Travel
```python
# Crear vista temporal
spark.read.format("delta").load(path).createOrReplaceTempView("demo")

# Query SQL con VERSION AS OF
spark.sql("SELECT COUNT(*) FROM demo VERSION AS OF 0").show()

# O con timestamp
spark.sql("SELECT * FROM demo TIMESTAMP AS OF '2024-02-01 10:00:00'").show()
```

---

## 🔄 03_audit_rollback.py

### Ver historial completo
```python
delta_table = DeltaTable.forPath(spark, path)
history = delta_table.history()

# Mostrar columnas relevantes
history.select(
    "version",
    "timestamp",
    "operation",
    "operationMetrics",
    "readVersion",
    "isBlindAppend"
).show(truncate=False)
```

### Rollback Pattern
```python
# 1. Leer versión anterior
old_version = spark.read.format("delta") \
    .option("versionAsOf", 1) \
    .load(path)

# 2. Sobrescribir tabla actual
old_version.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(path)

# ⚠️ IMPORTANTE: Esto crea una NUEVA versión (no elimina las intermedias)
```

### Verificar rollback
```python
# Comparar conteos antes y después
before = spark.read.format("delta").load(path).count()
# ...rollback...
after = spark.read.format("delta").load(path).count()

# Ver nuevo historial
delta_table.history().select("version", "operation").show()
```

---

## 🚨 Errores Comunes

### Error 1: Path no existe
```
AnalysisException: Path does not exist: s3a://bronze/time_travel_demo
```
**Solution**: Make sure to run first`01_create_versions.py`

### Error 2: Version no existe
```
AnalysisException: Version 5 does not exist
```
**Solution**: Check the history with`.history()`to see what versions exist

### Error 3: Invalid Timestamp
```
IllegalArgumentException: Invalid timestamp format
```
**Solution**: Use`str(timestamp)` al pasar el timestamp del historial

### Error 4: Update con comillas incorrectas
```python
# ❌ MAL
delta_table.update(condition="status = 'pending'", set={"status": "expired"})

# ✅ BIEN
delta_table.update(condition="status = 'pending'", set={"status": "'expired'"})
```

---

## 📚 Useful Commands

### Ver metadata de table
```python
# Ver descripción de tabla
spark.sql(f"DESCRIBE DETAIL delta.`{path}`").show(truncate=False)

# Ver archivos de datos
spark.sql(f"DESCRIBE EXTENDED delta.`{path}`").show(truncate=False)
```

### Ver transaction log
```python
import os
# El log está en _delta_log/*.json
log_path = f"{path}/_delta_log"
```

### Vacuum (limpiar versiones antiguas)
```python
# ⚠️ PRECAUCIÓN: Elimina archivos de versiones antiguas
delta_table.vacuum(168)  # Retiene 7 días (168 horas)

# Para testing (default retention es 7 días)
spark.conf.set("spark.databricks.delta.retentionDurationCheck.enabled", "false")
delta_table.vacuum(0)  # Elimina todo lo no referenciado
```

---

## 🎓 Conceptos Avanzados

### Snapshot Isolation
Delta Lake usa **Multi-Version Concurrency Control (MVCC)**:
- Each version is a complete snapshot
- Lecturas nunca bloquean escrituras
- Escrituras nunca bloquean lecturas
- Consistency garantizada

### Transaction Log Structure
```
_delta_log/
├── 00000000000000000000.json  # V0
├── 00000000000000000001.json  # V1
├── 00000000000000000002.json  # V2
└── 00000000000000000010.checkpoint.parquet  # Checkpoint cada 10 versiones
```

### Retention Policies
```python
# Configurar retention global (default: 7 días)
spark.conf.set("spark.databricks.delta.logRetentionDuration", "interval 30 days")
spark.conf.set("spark.databricks.delta.deletedFileRetentionDuration", "interval 7 days")

# O por tabla
spark.sql("""
    ALTER TABLE delta.`{path}`
    SET TBLPROPERTIES (
        'delta.logRetentionDuration' = 'interval 30 days',
        'delta.deletedFileRetentionDuration' = 'interval 7 days'
    )
""")
```

---

## ✅ Checklist de Completitud

- [ ] 01_create_versions.py crea 4 versiones (V0-V3)
- [ ] 02_time_travel_queries.py lee correctamente V0 y V3
- [ ] Query por timestamp funciona
- [ ] SQL Time Travel funciona
- [ ] 03_audit_rollback.py muestra historial completo
- [ ] Rollback a V1 funciona correctamente
- [ ] History after rollback shows new version
- [ ] Todos los conteos de registros son correctos
