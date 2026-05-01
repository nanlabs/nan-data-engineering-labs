# Ejercicio 06: Apache Iceberg Comparison

## 🎯 Objetivo
Compare Delta Lake vs Apache Iceberg with practical examples.

**Dificultad**: ⭐⭐⭐⭐ Avanzado | **Tiempo**: 45 minutos

## 📋 Tareas

1. Crear misma table en Delta y Iceberg
2. Comparar operaciones: append, update, time travel
3. Comparar performance
4. Comparar metadata storage

## ✅ Comandos Iceberg

```python
# Write Iceberg
df.writeTo("catalog.db.table").using("iceberg").create()

# Read Iceberg
spark.read.format("iceberg").load("catalog.db.table")

# Time Travel Iceberg
spark.read.format("iceberg") \
    .option("snapshot-id", snapshot_id) \
    .load("catalog.db.table")
```

## 🎓 Comparison

| Feature | Delta Lake | Apache Iceberg |
|---------|-----------|----------------|
| ACID | ✅ | ✅ |
| Time Travel | ✅ versionAsOf | ✅ snapshot-id |
| Schema Evolution | ✅ mergeSchema | ✅ schema evolution |
| Z-Ordering | ✅ OPTIMIZE | ❌ (usa sorting) |
| Partition Evolution | ⚠️ limitado | ✅ hidden partitioning |
| Ecosystem| Databricks, Spark | Spark, Trino, Presto, Flink |
| Metadata | Transaction log (_delta_log) | Metadata JSON |

## 💡 When to Use Each One

**Delta Lake**:
- Ecosystem Databricks
- Optimize write habilitado
- Critical Z-Ordering
- Strong Spark/Python integration

**Apache Iceberg**:
- Multi-engine (Trino, Presto, Flink)
- Partition evolution frecuente  
- Open governance (Apache Foundation)
- Cross-platform analysis
