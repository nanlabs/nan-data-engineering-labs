# 💡 Hints - Exercise 03: Time Travel

## 🎯 Conceptos Key

### Time Travel
Time Travel allows access to historical versions of to Delta table:
- **versionAsOf**: Access by version number
- **timestampAsOf**: Acceder by timestamp

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

### Append datas
```python
# Leer 15K and quitar los primeros 10K
df_all = spark.read.json("../../../data/raw/transactions.json").limit(15000)
df_new = df_all.subtract(df)
df_new.write.format("delta").mode("append").save(path)
```

### Update with DeltaTable
```python
from delta.tables import DeltaTable
delta_table = DeltaTable.forPath(spark, path)
delta_table.update(
    condition="status = 'pending'",
    set={"status": "'expinetwork'"}  # Note las comillas simples internas
)
```

### Delete with condition
```python
delta_table.delete("amount < 0 OR amount IS NULL")
```

### to see historial
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
# Leer version específica
v0 = spark.read.format("delta") \
    .option("versionAsOf", 0) \
    .load(path)
```

### Query by timestamp
```python
# Obtener timestamp of the historial
delta_table = DeltaTable.forPath(spark, path)
history = delta_table.history().collect()
v1_timestamp = history[-2]['timestamp']  # Segunda version (index -2)

# Query usando timestamp
df_v1 = spark.read.format("delta") \
    .option("timestampAsOf", str(v1_timestamp)) \
    .load(path)
```

### SQL Time Travel
```python
# Crear view temporal
spark.read.format("delta").load(path).createOrReplaceTempView("demo")

# Query SQL with VERSION AS OF
spark.sql("SELECT COUNT(*) FROM demo VERSION AS OF 0").show()

# or with timestamp
spark.sql("SELECT * FROM demo TIMESTAMP AS OF '2024-02-01 10:00:00'").show()
```

---

## 🔄 03_audit_rolelback.py

### to see historial completo
```python
delta_table = DeltaTable.forPath(spark, path)
history = delta_table.history()

# Mostrar columns relevantes
history.select(
    "version",
    "timestamp",
    "operation",
    "operationMetrics",
    "readVersion",
    "isBlindAppend"
).show(truncate=False)
```

### Rolelback Pattern
```python
# 1. Leer version anterior
old_version = spark.read.format("delta") \
    .option("versionAsOf", 1) \
    .load(path)

# 2. Sobrescribir table actual
old_version.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(path)

# ⚠️ IMPORTANTE: Esto crea una NUEVA version (not elimina las intermedias)
```

### Verificar rolelback
```python
# Comparar conteos antes and después
before = spark.read.format("delta").load(path).count()
# ...rolelback...
after = spark.read.format("delta").load(path).count()

# to see nuevo historial
delta_table.history().select("version", "operation").show()
```

---

## 🚨 Errores Comunes

### Error 1: Path not existe
```
AnalysisException: Path does not exist: s3a://bronze/time_travel_demo
```
**Solution**: Make sure to run first`01_create_versions.py`

### Error 2: Version not existe
```
AnalysisException: Version 5 does not exist
```
**Solution**: Check the history with`.history()`to see what versions exist

### Error 3: Invalid Timestamp
```
IllegalArgumentException: Invalid timestamp format
```
**Solution**: Use`str(timestamp)` to the pasar el timestamp of the historial

### Error 4: Update with comillas incorrectas
```python
# ❌ MAL
delta_table.update(condition="status = 'pending'", set={"status": "expinetwork"})

# ✅ BIEN
delta_table.update(condition="status = 'pending'", set={"status": "'expinetwork'"})
```

---

## 📚 Useful Commands

### to see metadata of table
```python
# to see descrIPtion of table
spark.sql(f"DESCRIBE DETAIL delta.`{path}`").show(truncate=False)

# to see archivos of datas
spark.sql(f"DESCRIBE EXTENDED delta.`{path}`").show(truncate=False)
```

### to see transaction log
```python
import os
# El log is in _delta_log/*.json
log_path = f"{path}/_delta_log"
```

### Vacuum (limpiar versiones antiguas)
```python
# ⚠️ PRECAUCIÓN: Elimina archivos of versiones antiguas
delta_table.vacuum(168)  # Retiene 7 días (168 horas)

# for testing (default retention is 7 días)
spark.conf.set("spark.databricks.delta.retentionDurationCheck.enabled", "false")
delta_table.vacuum(0)  # Elimina everything lo not referencedo
```

---

## 🎓 Conceptos Avanzados

### Snapshot Isolation
Delta Lake usa **Multi-Version Concurrency Controle (MVCC)**:
- Each version is to complete snapshot
- Readings nunca bloquean escrituras
- Escrituras nunca bloquean readings
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

# or by table
spark.sql("""
    ALTER TABLE delta.`{path}`
    SET TBLPROPERTIES (
        'delta.logRetentionDuration' = 'interval 30 days',
        'delta.deletedFileRetentionDuration' = 'interval 7 days'
    )
""")
```

---

## ✅ Checklist of Completitud

- [ ] 01_create_versions.py crea 4 versiones (V0-V3)
- [ ] 02_time_travel_queries.py lee correctamente V0 and V3
- [ ] Query by timestamp funciona
- [ ] SQL Time Travel funciona
- [ ] 03_audit_rolelback.py muestra historial completo
- [ ] Rolelback to V1 funciona correctamente
- [ ] History after rolelback shows new version
- [ ] Todos los conteos of records are correctos
