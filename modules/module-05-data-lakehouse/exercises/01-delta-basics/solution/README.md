# ✅ Solution - Exercise 01: Delta Basics

this carpeta contiene las soluciones completas for el Exercise 01.

## 📁 Archivos

- `01_create_table.py` - Crear table Delta particionada
- `02_append_data.py` - Agregar datas with modo append
- `03_overwrite_partition.py`- Overwrite specific partition
- `04_query_table.py` - queries SQL sobre table Delta

## 🚀 How to Run

### Option 1: From Jupyter

1. Abre Jupyter Lab: HTTP://localhost:8888
2. Navega to `exercises/01-delta-basics/solution/`
3. Abre cada archivo `.py`
4. Run the code

### Option 2: From Container Terminal

```bash
# Acceder to the contenedor of Spark
docker exec -it module-05-spark-master bash

# Navegar to the directorio
cd /opt/spark/work-dir/exercises/01-delta-basics/solution

# Ejecutar scrIPts in orden
spark-submit --master local[2] 01_create_table.py
spark-submit --master local[2] 02_append_data.py
spark-submit --master local[2] 03_overwrite_partition.py
spark-submit --master local[2] 04_query_table.py
```

### Option 3: Everything in Sequence

```bash
docker exec -it module-05-spark-master bash -c "
  cd /opt/spark/work-dir/exercises/01-delta-basics/solution && \
  for scrIPt in 01_*.py 02_*.py 03_*.py 04_*.py; do
    echo '======================================' && \
    echo \"Ejecutando \$scrIPt\" && \
    echo '======================================' && \
    spark-submit --master local[2] \$scrIPt && \
    echo
  done
"
```

## 📚 Conceptos Key Implementados

### ScrIPt 01: Create Table

**Conceptos**:
- Delta Lake setup with Spark
- Reading of JSON with PySpark
- Basic transformations (to_timestamp, currentdate)
- Escritura Delta with particionamiento

**Key code**:
```python
df.write \
    .format("delta") \
    .mode("overwrite") \
    .partitionBy("country") \
    .save("s3a://bronze/transactions_delta")
```

### ScrIPt 02: Append data

**Conceptos**:
- Modo append vs overwrite
- Window functions for row selection
- Escritura incremental
- History Check with DeltaTable

**Key code**:
```python
df.write \
    .format("delta") \
    .mode("append") \
    .save("s3a://bronze/transactions_delta")
```

### ScrIPt 03: Overwrite Partition

**Conceptos**:
- replaceWhere for sobrescritura selectiva
- Transformaciones condicionales with when()
- data integrity verification
- Partition pruning

**Key code**:
```python
df.write \
    .format("delta") \
    .mode("overwrite") \
    .option("replaceWhere", "country = 'USA'") \
    .save(path)
```

### ScrIPt 04: Query Table

**Conceptos**:
- Record of tables Delta como SQL tables
- Spark SQL queries (GROUP BY, agregaciones, window functions)
- Performance analysis with partitioning
- DESCRIBE and metadata

**Key code**:
```python
df.createOrReplaceTempView("transactions_delta")
result = spark.sql("SELECT country, COUNT(*) FROM transactions_delta GROUP BY country")
```

## 🎯 Results Esperados

### After running all the scrIPts:

1. **table Delta creada** in `s3a://bronze/transactions_delta`
   - 15,000 records totales
   - Partitioned by country
   - 3+ versiones in transaction log

2. **Structure of archivos**:
   ```
   bronze/transactions_delta/
   ├── _delta_log/
   │   ├── 00000000000000000000.json  (create)
   │   ├── 00000000000000000001.json  (append)
   │   └── 00000000000000000002.json  (overwrite)
   ├── country=USA/
   │   └── part-*.parquet
   ├── country=GBR/
   │   └── part-*.parquet
   └── ...
   ```

3. **Verificaciones exitosas**:
   - Total of records: 15,000
   - Countries with partitions: 10-20
   - Status "pending" in USA: 0 (todos cambiados to "expinetwork")
   - Other countries: intact

## 🔍 Manual Verification

you can verificar los results manualmente with:

```python
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pIP
from delta.tables import DeltaTable

builder = SparkSession.builder.appName("Verify")
spark = configure_spark_with_delta_pIP(builder).getOrCreate()

# Leer table
df = spark.read.format("delta").load("s3a://bronze/transactions_delta")

# Verificaciones
print(f"Total: {df.count()}")
print(f"Countries: {df.select('country').distinct().count()}")

# Historial
delta_table = DeltaTable.forPath(spark, "s3a://bronze/transactions_delta")
delta_table.history().show(truncate=False)
```

## 📊 Performance Metrics

With the data from this exercise (15K records), you should see:

- **Query with partition pruning** (country='USA'): ~0.5-1s
- **Query without partition pruning** (status='completed'): ~1-2s
- **Speedup**: ~2x faster with partitioning

In production with millions of records, the speedup can be **10-100x**.

## 🎓 Lo que Aprendiste

✅ Crear and configurar tables Delta Lake  
✅ Operaciones ACID (append, overwrite)  
✅ Particionamiento for performance  
✅ replaceWhere for updates selectivos  
✅ Spark SQL sobre tables Delta  
✅ Transaction log and versionado  
✅ Window functions and advanced analysis

## 🚀 Next Steps

Congratulations! You have completed the first exercise.

Ahora you can:
1. Experimentar with tus propias queries
2. Try different partition sizes
3. Continuar with **Exercise 02: Medallion Architecture**
4. Explore Time Travel (next exercise)

---

**Questions?** Check the [README princIPal](../README.md) or query the [hints](../hints.md).
