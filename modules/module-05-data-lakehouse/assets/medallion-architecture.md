# Medallion Architecture

## 📊 Diagrama

```
┌─────────────────────────────────────────────────────────────┐
│                     data SOURCES                            │
│   JSON Files │ APIs │ Databases │ Streams │ CSV Files      │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                    BRONZE LAYER                             │
│              (Raw, Append-Only, not Quality)                 │
│                                                             │
│  • Ingesta raw without transformación                           │
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
│  • Deduplicado by key primaria                           │
│  • Validado (not nulls, not negativos)                        │
│  • Normalizado (mayúsculas, formatos)                       │
│  • TIPos correctos (Decimal, Date, Timestamp)               │
│  • Columns derivadas (date, is_valid)                      │
│  • Partition: country, date                                 │
│                                                             │
│  Path: s3a://silver/transactions_clean                      │
└──────┬──────────────────────────────────────────────────────┘
       │
       │ Aggregations:
       │ • Group by dimensions
       │ • Cálculos of métricas
       │ • KPIs of negocio
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                     GOLD LAYER                              │
│           (Aggregated, Business Metrics, BI-Ready)          │
│                                                             │
│  • Agregaciones by date, country                           │
│  • Métricas: total_transactions, total_amount               │
│  • KPIs: avg_amount, completion_rate                        │
│  • Percentiles: p50, p90, p99                               │
│  • Dimensiones of negocio                                   │
│  • Optimizado for BI tools                                 │
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

## 🎯 features of Cada Layer

### Bronze (Raw Zone)

| Aspecto | feature |
|---------|---------------|
| **Purpose** | Preserve original data |
| **Quality** | not validation |
| **Operaciones** | only append |
| **Schema** | Schema original + metadata |
| **Retention** | Long term (years) |
| **Users** | data Engineers |

### Silver (Curated Zone)

| Aspecto | feature |
|---------|---------------|
| **Purpose** | Clean and validated data |
| **Calidad** | Validaciones aplicadas |
| **Operaciones** | Append + Updates (by dedup) |
| **Schema** | Normalizado and tIPado |
| **Retention** | Medio plazo (meses) |
| **Users** | data Engineers + Analysts |

### Gold (Business Zone)

| Aspecto | feature |
|---------|---------------|
| **Purpose** | Business metrics |
| **Calidad** | Agregaciones precisas |
| **Operaciones** | Overwrite diario/horario |
| **Schema** | Dimensions + Metrics |
| **Retention** | Corto plazo (semanas) |
| **Users** | Business Analysts + BI Tools |

## 💡 Best Practices

1. **Bronze**: Never delete data, use Time Travel if you need auditing
2. **Silver**: Aplica validaciones estrictas, documenta reglas of negocio
3. **Gold**: Optimize with OPTIMIZE and Z-ORDER for fast queries
4. **Partitions**: Bronze by ingestion_date, Silver by business dimensions
5. **Idempotence**: Design pIPelines that can be re-executed without duplicates

## 🔄 pIPeline Incremental

```python
# Bronze: Incremental append
new_data.write.format("delta").mode("append").save(bronze_path)

# Silver: Merge for deduplicar
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

- **Bronze → Silver**: data Quality Rate (% valid records)
- **Silver → Gold**: Transformation Time (latency)
- **Gold**: Query Performance (tiempo promedio of BI queries)
