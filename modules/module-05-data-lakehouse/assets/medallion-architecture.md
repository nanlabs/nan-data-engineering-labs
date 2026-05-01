# Medallion Architecture

## 📊 Diagrama

```
┌─────────────────────────────────────────────────────────────┐
│                     DATA SOURCES                            │
│   JSON Files │ APIs │ Databases │ Streams │ CSV Files      │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                    BRONZE LAYER                             │
│              (Raw, Append-Only, No Quality)                 │
│                                                             │
│  • Ingesta raw sin transformación                           │
│  • Append-only (nunca delete/update)                        │
│  • Metadata: ingestion_timestamp, source_file               │
│  • Partition: ingestion_date                                │
│  • Formato: Delta Lake                                      │
│                                                             │
│  Path: s3a://bronze/transactions_raw                        │
└──────┬──────────────────────────────────────────────────────┘
       │
       │ Transformations:
       │ • Deduplicación
       │ • Validaciones
       │ • Normalización
       │ • Type casting
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                    SILVER LAYER                             │
│         (Cleaned, Validated, Business-Ready)                │
│                                                             │
│  • Deduplicado por clave primaria                           │
│  • Validado (no nulls, no negativos)                        │
│  • Normalizado (mayúsculas, formatos)                       │
│  • Tipos correctos (Decimal, Date, Timestamp)               │
│  • Columnas derivadas (date, is_valid)                      │
│  • Partition: country, date                                 │
│                                                             │
│  Path: s3a://silver/transactions_clean                      │
└──────┬──────────────────────────────────────────────────────┘
       │
       │ Aggregations:
       │ • Group by dimensions
       │ • Cálculos de métricas
       │ • KPIs de negocio
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                     GOLD LAYER                              │
│           (Aggregated, Business Metrics, BI-Ready)          │
│                                                             │
│  • Agregaciones por date, country                           │
│  • Métricas: total_transactions, total_amount               │
│  • KPIs: avg_amount, completion_rate                        │
│  • Percentiles: p50, p90, p99                               │
│  • Dimensiones de negocio                                   │
│  • Optimizado para BI tools                                 │
│                                                             │
│  Path: s3a://gold/transactions_aggregated                   │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                   CONSUMPTION                               │
│   Tableau │ Power BI │ Jupyter │ Dashboards │ ML Models    │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 features de Cada Layer

### Bronze (Raw Zone)

| Aspecto | feature |
|---------|---------------|
| **Purpose** | Preserve original data |
| **Quality** | No validation |
| **Operaciones** | Solo append |
| **Schema** | Schema original + metadata |
| **Retention** | Long term (years) |
| **Usuarios** | Data Engineers |

### Silver (Curated Zone)

| Aspecto | feature |
|---------|---------------|
| **Purpose** | Clean and validated data |
| **Calidad** | Validaciones aplicadas |
| **Operaciones** | Append + Updates (por dedup) |
| **Schema** | Normalizado y tipado |
| **Retention** | Medio plazo (meses) |
| **Usuarios** | Data Engineers + Analysts |

### Gold (Business Zone)

| Aspecto | feature |
|---------|---------------|
| **Purpose** | Business metrics |
| **Calidad** | Agregaciones precisas |
| **Operaciones** | Overwrite diario/horario |
| **Schema** | Dimensions + Metrics |
| **Retention** | Corto plazo (semanas) |
| **Usuarios** | Business Analysts + BI Tools |

## 💡 Best Practices

1. **Bronze**: Never delete data, use Time Travel if you need auditing
2. **Silver**: Aplica validaciones estrictas, documenta reglas de negocio
3. **Gold**: Optimize with OPTIMIZE and Z-ORDER for fast queries
4. **Partitions**: Bronze por ingestion_date, Silver por business dimensions
5. **Idempotence**: Design pipelines that can be re-executed without duplicates

## 🔄 pipeline Incremental

```python
# Bronze: Incremental append
new_data.write.format("delta").mode("append").save(bronze_path)

# Silver: Merge para deduplicar
from delta.tables import DeltaTable
silver_table = DeltaTable.forPath(spark, silver_path)
silver_table.alias("target").merge(
    new_data_clean.alias("source"),
    "target.transaction_id = source.transaction_id"
).whenNotMatchedInsertAll().execute()

# Gold: Overwrite diario
aggregated_data.write.format("delta") \
    .mode("overwrite") \
    .option("replaceWhere", "date = '2024-01-15'") \
    .save(gold_path)
```

## 📈 Key Metrics

- **Bronze → Silver**: Data Quality Rate (% valid records)
- **Silver → Gold**: Transformation Time (latency)
- **Gold**: Query Performance (tiempo promedio de BI queries)
