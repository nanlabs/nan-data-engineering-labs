# Exercise 02: Medallion Architecture (Bronze → Silver → Gold)

## 🎯 Objective

Implement the full Medallion architecture, the fundamental data Lakehouse pattern:

- **Bronze Layer** (Raw): Raw ingestion, append-only, data as it arrives
- **Silver Layer** (Cleaned): Cleaning, validation, deduplication, correct types
- **Gold Layer** (Aggregated): Business metrics, aggregations, reports

**Difficulty**: ⭐⭐⭐ Intermedio  
**Estimated Time**: 90-120 minutos  
**Prerequisitos**: Exercise 01 completado

---

## 📋Exercise DescrIPtion

Your team needs to build an end-to-end data pIPeline to process e-commerce transactions. The objective is to transform raw data into business insights following the Medallion pattern.

### Flow of Datas

```
RAW JSON FILES
     ↓
🥉 BRONZE (s3a://bronze/transactions)
  - Datas tal cual llegan
  - without validaciones
  - Append-only
  - Incluye duplicados and errores
     ↓
🥈 SILVER (s3a://silver/transactions_clean)
  - Limpieza aplicada
  - Duplicados removidos
  - Nulls manejados
  - TIPos correctos
  - Schema enforcement
     ↓
🥇 GOLD (s3a://gold/transactions_metrics)
  - Agregaciones by país
  - Métricas diarias
  - KPIs of negocio
  - Listo for BI tools
```

---

## 🗂️ Structure of the Exercise

```
02-medallion-architecture/
├── README.md (this archivo)
├── hints.md
├── starter/
│   ├── 01_bronze_ingestion.py       # Ingestar to Bronze
│   ├── 02_silver_cleaning.py        # Limpiar for Silver
│   ├── 03_gold_aggregation.py       # Agregar for Gold
│   ├── 04_full_pIPeline.py          # PIPeline completo
│   └── requirements.txt
├── solution/
│   ├── 01_bronze_ingestion.py
│   ├── 02_silver_cleaning.py
│   ├── 03_gold_aggregation.py
│   ├── 04_full_pIPeline.py
│   └── README.md
└── tests/
    └── test_medallion.py
```

---

## 🚀 Setup

```bash
# 1. Asegúrate of que la infrastructure is corriendo
cd ../../infrastructure
docker-compose up -d

# 2. to see logs of Spark
docker-compose logs -f spark-master

# 3. Acceder to Jupyter (opcional)
# HTTP://localhost:8888

# 4. UI of Spark for monitorear jobs
# HTTP://localhost:8080 (Spark Master)
# HTTP://localhost:4040 (Spark Application UI, when am corriendo)
```

---

## 📝 Tareas

### Task 1: Bronze Layer - Raw Ingestion

**Archivo**: `starter/01_bronze_ingestion.py`

**Objective**: Ingestar datas crudos desde JSON to table Delta Bronze.

**Requisitos**:
1. Leer `data/raw/transactions.json` (TODOS los records)
2. Add ingestion metadata:
   - `ingestion_timestamp` (timestamp of carga)
   - `source_file` (nombre of the archivo)
3. not aplicar limpieza ni validaciones
4. Guardar in `s3a://bronze/transactions` como Delta
5. Particionar by `ingestion_date` (derivado of ingestion_timestamp)

**features Bronze**:
- ✅ Append-only (nunca sobrescribir)
- ✅ Inmutable (preservar datas tal cual)
- ✅ Full lineage (metadata of origen)
- ✅ Incluir TODOS los datas (incluso errores)

**Expectativas**:
- ~614K records in Bronze
- Todos los records originales presentes
- Aggregated ingestion metadata
- not loss of information

---

### Task 2: Silver Layer - Cleaning and Validation

**Archivo**: `starter/02_silver_cleaning.py`

**Objective**: Transformar datas Bronze in datas Silver limpios and confiables.

**Requisitos**:
1. Leer table Bronze
2. Aplicar limpieza:
   - Remover duplicados basados in `transaction_id`
   - Filtrar records with `amount` NULL or negativo
   - Filtrar transactions with `timestamp` NULL
   - Normalizar `status` (lowercase, trimmed)
   - Convertir `currency`to uppercase3. Add validation column:
   - `is_valid` (boolean)
   - `validation_errors` (array of strings with errores encontrados)
4. Convertir tIPos:
   - `amount` → DecimalType(10,2)
   - `timestamp` → TimestampType
5. Guardar in `s3a://silver/transactions_clean`
6. Particionar by `country` and `date` (of the timestamp)

**features Silver**:
- ✅ Deduplicated
- ✅ Validated
- ✅ Strongly typed
- ✅ Quality flags
- ✅ Suitable for analytics

**Expectativas**:
- ~540K records in Silver (after filtering out ~12% with issues)
- without duplicados
- not nulls in critical fields
- TIPos of datas correctos

---

### Tarea 3: Gold Layer - Agregaciones of Negocio

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
4. Guardar in `s3a://gold/transactions_metrics`
5. Particionar by `country`

**features Gold**:
- ✅ Business-friendly (columns with nombres claros)
- ✅ Denormalized (everything in una table)
- ✅ Pre-aggregated (quick queries)
- ✅ BI-ready (conectar directamente to Tableau, PowerBI, etc.)

**Expectativas**:
- rows networkuced to ~100-500 (per country-day)
- Instant queries
- Ready for viewing

---

### Tarea 4: pIPeline Completo

**Archivo**: `starter/04_full_pIPeline.py`

**Objective**: Orquestar el pIPeline completo Bronze → Silver → Gold.

**Requisitos**:
1. Run Bronze ingestion
2. Ejecutar limpieza Silver
3. Run Gold Aggregation
4. Implementar checkpoints entre stages
5. Manejar errores and logging
6. Generar reporte of resumen:
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

**features pIPeline**:
- ✅ Idempotent (can run multIPle times)
- ✅ Incremental (procesar only nuevos datas)
- ✅ Monitonetwork (metrics and logs)
- ✅ Error-tolerant (manejo of fallos)

---

## ✅ Success Criteria

### Bronze Layer
- [ ] ~614K records in `s3a://bronze/transactions`
- [ ] Ingestion metadata (`ingestion_timestamp`, `source_file`)
- [ ] Particionado by `ingestion_date`
- [ ] Todos los datas originales preservados

### Silver Layer
- [ ] ~540K records in `s3a://silver/transactions_clean` (88% of the original)
- [ ] without duplicados
- [ ] not nulls in critical fields
- [ ] TIPos correctos (DecimalType, TimestampType)
- [ ] validation columns (`is_valid`, `validation_errors`)

### Gold Layer
- [ ] ~300-500 rows in `s3a://gold/transactions_metrics`
- [ ] Metrics aggregated by country-day
- [ ] Percentiles calculados
- [ ] Conversion/completion rates

### pIPeline Completo
- [ ] Ejecuta end-to-end without errores
- [ ] Genera reporte of resumen
- [ ] Execution time < 3 minutes
- [ ] Logs informativos in cada stage

---

## 🎓 Conceptos Key

### Medallion Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ 🥉 BRONZE - "Keep Everything"                               │
│                                                              │
│ Purpose: Long-term audit trail, reprocessing capability     │
│ Format: Raw, append-only, immutable                         │
│ Retention: Years (cheap object storage)                     │
│ Quality: As-is, not filtering                                  │
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
- data sources variadas (APIs, archivos, streams)
- Audit and compliance
- Reprocessing after changes in logic
- ML feature engineering sobre datas crudos

**Silver**:
- Analytics ad-hoc
- ML training datasets
- Join between multIPle sources
- Exploratory data analysis

**Gold**:
- Dashboards of C-level
- Reportes operacionales
- Alerts and monitoring
- Product metrics

---

## 📚 resources

- [Medallion Architecture - Databricks](HTTPs://www.databricks.com/glossary/medallion-architecture)
- [Delta Lake Best Practices](HTTPs://docs.delta.io/latest/best-practices.html)
- [PySpark data Quality](HTTPs://spark.apache.org/docs/latest/sql-ref-functions.html)

---

## 🔍 Troubleshooting

### "Table already exists" in Bronze

Bronze is append-only. Usa `.mode("append")` siempre:
```python
df.write.format("delta").mode("append").save(path)
```

### pIPeline muy lento

1. **Aumenta paralelismo**: `.repartition(200)` antes of escribir
2. **Filtra temprano**: Aplica filters antes of joins
3. **Cachea**: if reutilizas un DataFrame, usa `.cache()`

### Incorrect metrics in Gold

Verify that Silver is properly clean:
```python
silver_df = spark.read.format("delta").load("s3a://silver/transactions_clean")
silver_df.groupBy("is_valid").count().show()  # Debe ser 100% valid
```

---

## 🎯 Next Steps

Una vez completado:
1. ✅ Continuar with **Exercise 03: Time Travel**
2. Explorar MERGE for updates incrementales
3. Implementar SCD Type 2 for slowly changing dimensions
4. Agregar Great Expectations for data quality

Good luck! 🚀
