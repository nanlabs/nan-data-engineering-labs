# Ejercicio 02: Medallion Architecture (Bronze → Silver → Gold)

## 🎯 Objetivo

Implement the full Medallion architecture, the fundamental Data Lakehouse pattern:

- **Bronze Layer** (Raw): Raw ingestion, append-only, data as it arrives
- **Silver Layer** (Cleaned): Cleaning, validation, deduplication, correct types
- **Gold Layer** (Aggregated): Business metrics, aggregations, reports

**Dificultad**: ⭐⭐⭐ Intermedio  
**Tiempo Estimado**: 90-120 minutos  
**Prerequisitos**: Ejercicio 01 completado

---

## 📋Exercise Description

Your team needs to build an end-to-end data pipeline to process e-commerce transactions. The objective is to transform raw data into business insights following the Medallion pattern.

### Flujo de Datos

```
RAW JSON FILES
     ↓
🥉 BRONZE (s3a://bronze/transactions)
  - Datos tal cual llegan
  - Sin validaciones
  - Append-only
  - Incluye duplicados y errores
     ↓
🥈 SILVER (s3a://silver/transactions_clean)
  - Limpieza aplicada
  - Duplicados removidos
  - Nulls manejados
  - Tipos correctos
  - Schema enforcement
     ↓
🥇 GOLD (s3a://gold/transactions_metrics)
  - Agregaciones por país
  - Métricas diarias
  - KPIs de negocio
  - Listo para BI tools
```

---

## 🗂️ Estructura del Ejercicio

```
02-medallion-architecture/
├── README.md (este archivo)
├── hints.md
├── starter/
│   ├── 01_bronze_ingestion.py       # Ingestar a Bronze
│   ├── 02_silver_cleaning.py        # Limpiar para Silver
│   ├── 03_gold_aggregation.py       # Agregar para Gold
│   ├── 04_full_pipeline.py          # Pipeline completo
│   └── requirements.txt
├── solution/
│   ├── 01_bronze_ingestion.py
│   ├── 02_silver_cleaning.py
│   ├── 03_gold_aggregation.py
│   ├── 04_full_pipeline.py
│   └── README.md
└── tests/
    └── test_medallion.py
```

---

## 🚀 Setup

```bash
# 1. Asegúrate de que la infraestructura está corriendo
cd ../../infrastructure
docker-compose up -d

# 2. Ver logs de Spark
docker-compose logs -f spark-master

# 3. Acceder a Jupyter (opcional)
# http://localhost:8888

# 4. UI de Spark para monitorear jobs
# http://localhost:8080 (Spark Master)
# http://localhost:4040 (Spark Application UI, cuando esté corriendo)
```

---

## 📝 Tareas

### Task 1: Bronze Layer - Raw Ingestion

**Archivo**: `starter/01_bronze_ingestion.py`

**Objetivo**: Ingestar datos crudos desde JSON a table Delta Bronze.

**Requisitos**:
1. Leer `data/raw/transactions.json` (TODOS los registros)
2. Add ingestion metadata:
   - `ingestion_timestamp` (timestamp de carga)
   - `source_file` (nombre del archivo)
3. NO aplicar limpieza ni validaciones
4. Guardar en `s3a://bronze/transactions` como Delta
5. Particionar por `ingestion_date` (derivado de ingestion_timestamp)

**features Bronze**:
- ✅ Append-only (nunca sobrescribir)
- ✅ Inmutable (preservar datos tal cual)
- ✅ Full lineage (metadata de origen)
- ✅ Incluir TODOS los datos (incluso errores)

**Expectativas**:
- ~614K registros en Bronze
- Todos los registros originales presentes
- Aggregated ingestion metadata
- No loss of information

---

### Task 2: Silver Layer - Cleaning and Validation

**Archivo**: `starter/02_silver_cleaning.py`

**Objetivo**: Transformar datos Bronze en datos Silver limpios y confiables.

**Requisitos**:
1. Leer table Bronze
2. Aplicar limpieza:
   - Remover duplicados basados en `transaction_id`
   - Filtrar registros con `amount` NULL o negativo
   - Filtrar transactions con `timestamp` NULL
   - Normalizar `status` (lowercase, trimmed)
   - Convertir `currency`to uppercase3. Add validation column:
   - `is_valid` (boolean)
   - `validation_errors` (array de strings con errores encontrados)
4. Convertir tipos:
   - `amount` → DecimalType(10,2)
   - `timestamp` → TimestampType
5. Guardar en `s3a://silver/transactions_clean`
6. Particionar por `country` y `date` (del timestamp)

**features Silver**:
- ✅ Deduplicated
- ✅ Validated
- ✅ Strongly typed
- ✅ Quality flags
- ✅ Suitable for analytics

**Expectativas**:
- ~540K records in Silver (after filtering out ~12% with issues)
- Sin duplicados
- No nulls in critical fields
- Tipos de datos correctos

---

### Tarea 3: Gold Layer - Agregaciones de Negocio

**Archivo**: `starter/03_gold_aggregation.py`

**Goal**: Create aggregated business metrics for dashboards.

**Requisitos**:
1. Leer table Silver
2. Add daily metrics by country:
   ```python
   - date
   - country
   - total_transactions
   - total_amount
   - avg_amount
   - num_completed
   - num_failed
   - num_pending
   - completion_rate (%)
   - unique_users
   - unique_products
   ```
3. Calcular percentiles:
   - `p50_amount` (mediana)
   - `p90_amount`
   - `p99_amount`
4. Guardar en `s3a://gold/transactions_metrics`
5. Particionar por `country`

**features Gold**:
- ✅ Business-friendly (columns con nombres claros)
- ✅ Denormalized (todo en una table)
- ✅ Pre-aggregated (quick queries)
- ✅ BI-ready (conectar directamente a Tableau, PowerBI, etc.)

**Expectativas**:
- rows reduced to ~100-500 (per country-day)
- Instant queries
- Ready for viewing

---

### Tarea 4: pipeline Completo

**Archivo**: `starter/04_full_pipeline.py`

**Objetivo**: Orquestar el pipeline completo Bronze → Silver → Gold.

**Requisitos**:
1. Run Bronze ingestion
2. Ejecutar limpieza Silver
3. Run Gold Aggregation
4. Implementar checkpoints entre stages
5. Manejar errores y logging
6. Generar reporte de resumen:
   ```
   📊 PIPELINE EXECUTION SUMMARY
   =============================
   Bronze: 614,500 records ingested
   Silver: 540,000 records cleaned (88% valid)
   Gold: 480 metrics generated
   
   Quality Report:
   - Duplicates removed: 74,500 (12%)
   - Invalid amounts: 18,000 (3%)
   - Null timestamps: 5,000 (0.8%)
   
   Execution Time: 124.5s
   Status: ✅ SUCCESS
   ```

**features pipeline**:
- ✅ Idempotent (can run multiple times)
- ✅ Incremental (procesar solo nuevos datos)
- ✅ Monitored (metrics and logs)
- ✅ Error-tolerant (manejo de fallos)

---

## ✅ Success Criteria

### Bronze Layer
- [ ] ~614K registros en `s3a://bronze/transactions`
- [ ] Ingestion metadata (`ingestion_timestamp`, `source_file`)
- [ ] Particionado por `ingestion_date`
- [ ] Todos los datos originales preservados

### Silver Layer
- [ ] ~540K registros en `s3a://silver/transactions_clean` (88% del original)
- [ ] Sin duplicados
- [ ] No nulls in critical fields
- [ ] Tipos correctos (DecimalType, TimestampType)
- [ ] validation columns (`is_valid`, `validation_errors`)

### Gold Layer
- [ ] ~300-500 rows en `s3a://gold/transactions_metrics`
- [ ] Metrics aggregated by country-day
- [ ] Percentiles calculados
- [ ] Conversion/completion rates

### pipeline Completo
- [ ] Ejecuta end-to-end sin errores
- [ ] Genera reporte de resumen
- [ ] Execution time < 3 minutes
- [ ] Logs informativos en cada stage

---

## 🎓 Conceptos Clave

### Medallion Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ 🥉 BRONZE - "Keep Everything"                               │
│                                                              │
│ Purpose: Long-term audit trail, reprocessing capability     │
│ Format: Raw, append-only, immutable                         │
│ Retention: Years (cheap object storage)                     │
│ Quality: As-is, no filtering                                  │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 🥈 SILVER - "Clean and Conformed"                           │
│                                                              │
│ Purpose: Trusted source for analytics, ML feature store     │
│ Format: Deduplicated, validated, typed                      │
│ Retention: Months to years                                  │
│ Quality: Enterprise-grade, SLA-backed                       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 🥇 GOLD - "Business-Ready"                                  │
│                                                              │
│ Purpose: Dashboards, reports, KPIs                          │
│ Format: Aggregated, denormalized, optimized                 │
│ Retention: Weeks to months                                  │
│ Quality: Business-validated, domain-specific                │
└─────────────────────────────────────────────────────────────┘
```

### When to Use Each Layer

**Bronze**:
- Data sources variadas (APIs, archivos, streams)
- Audit and compliance
- Reprocessing after changes in logic
- ML feature engineering sobre datos crudos

**Silver**:
- Analytics ad-hoc
- ML training datasets
- Join between multiple sources
- Exploratory data analysis

**Gold**:
- Dashboards de C-level
- Reportes operacionales
- Alertas y monitoring
- Product metrics

---

## 📚 resources

- [Medallion Architecture - Databricks](https://www.databricks.com/glossary/medallion-architecture)
- [Delta Lake Best Practices](https://docs.delta.io/latest/best-practices.html)
- [PySpark Data Quality](https://spark.apache.org/docs/latest/sql-ref-functions.html)

---

## 🔍 Troubleshooting

### "Table already exists" en Bronze

Bronze es append-only. Usa `.mode("append")` siempre:
```python
df.write.format("delta").mode("append").save(path)
```

### pipeline muy lento

1. **Aumenta paralelismo**: `.repartition(200)` antes de escribir
2. **Filtra temprano**: Aplica filtros antes de joins
3. **Cachea**: Si reutilizas un DataFrame, usa `.cache()`

### Incorrect metrics in Gold

Verify that Silver is properly clean:
```python
silver_df = spark.read.format("delta").load("s3a://silver/transactions_clean")
silver_df.groupBy("is_valid").count().show()  # Debe ser 100% valid
```

---

## 🎯 Next Steps

Una vez completado:
1. ✅ Continuar con **Ejercicio 03: Time Travel**
2. Explorar MERGE para updates incrementales
3. Implementar SCD Type 2 para slowly changing dimensions
4. Agregar Great Expectations para data quality

Good luck! 🚀
