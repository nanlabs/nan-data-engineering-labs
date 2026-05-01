# ✅ Solution - Exercise 01: Delta Basics

Esta carpeta contiene las soluciones completas para el Ejercicio 01.

## 📁 Archivos

- `01_create_table.py` - Crear table Delta particionada
- `02_append_data.py` - Agregar datos con modo append
- `03_overwrite_partition.py`- Overwrite specific partition
- `04_query_table.py` - queries SQL sobre table Delta

## 🚀 How to Run

### Option 1: From Jupyter

1. Abre Jupyter Lab: http://localhost:8888
2. Navega a `exercises/01-delta-basics/solution/`
3. Abre cada archivo `.py`
4. Run the code

### Option 2: From Container Terminal

```bash
# Acceder al contenedor de Spark
docker exec -it module-05-spark-master bash

# Navegar al directorio
cd /opt/spark/work-dir/exercises/01-delta-basics/solution

# Ejecutar scripts en orden
spark-submit --master local[2] 01_create_table.py
spark-submit --master local[2] 02_append_data.py
spark-submit --master local[2] 03_overwrite_partition.py
spark-submit --master local[2] 04_query_table.py
```

### Option 3: Everything in Sequence

```bash
docker exec -it module-05-spark-master bash -c "
  cd /opt/spark/work-dir/exercises/01-delta-basics/solution && \
  for script in 01_*.py 02_*.py 03_*.py 04_*.py; do
    echo '======================================' && \
    echo \"Ejecutando \$script\" && \
    echo '======================================' && \
    spark-submit --master local[2] \$script && \
    echo
  done
"
```

## 📚 Conceptos Clave Implementados

### Script 01: Create Table

**Conceptos**:
- Delta Lake setup with Spark
- Lectura de JSON con PySpark
- Basic transformations (to_timestamp, currentdate)
- Escritura Delta con particionamiento

**Key code**:
```python
df.write \
    .format("delta") \
    .mode("overwrite") \
    .partitionBy("country") \
    .save("s3a://bronze/transactions_delta")
```

### Script 02: Append Data

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

### Script 03: Overwrite Partition

**Conceptos**:
- replaceWhere para sobrescritura selectiva
- Transformaciones condicionales con when()
- Data integrity verification
- Partition pruning

**Key code**:
```python
df.write \
    .format("delta") \
    .mode("overwrite") \
    .option("replaceWhere", "country = 'USA'") \
    .save(path)
```

### Script 04: Query Table

**Conceptos**:
- Registro de tables Delta como SQL tables
- Spark SQL queries (GROUP BY, agregaciones, window functions)
- Performance analysis with partitioning
- DESCRIBE y metadata

**Key code**:
```python
df.createOrReplaceTempView("transactions_delta")
result = spark.sql("SELECT country, COUNT(*) FROM transactions_delta GROUP BY country")
```

## 🎯 Resultados Esperados

### After running all the scripts:

1. **table Delta creada** en `s3a://bronze/transactions_delta`
   - 15,000 registros totales
   - Partitioned by country
   - 3+ versiones en transaction log

2. **Estructura de archivos**:
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
   - Total de registros: 15,000
   - Countries with partitions: 10-20
   - Status "pending" en USA: 0 (todos cambiados a "expired")
   - Other countries: intact

## 🔍 Manual Verification

Puedes verificar los resultados manualmente con:

```python
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip
from delta.tables import DeltaTable

builder = SparkSession.builder.appName("Verify")
spark = configure_spark_with_delta_pip(builder).getOrCreate()

# Leer tabla
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

- **Query con partition pruning** (country='USA'): ~0.5-1s
- **Query sin partition pruning** (status='completed'): ~1-2s
- **Speedup**: ~2x faster with partitioning

In production with millions of records, the speedup can be **10-100x**.

## 🎓 Lo que Aprendiste

✅ Crear y configurar tables Delta Lake  
✅ Operaciones ACID (append, overwrite)  
✅ Particionamiento para performance  
✅ replaceWhere para updates selectivos  
✅ Spark SQL sobre tables Delta  
✅ Transaction log y versionado  
✅ Window functions and advanced analysis

## 🚀 Next Steps

Congratulations! You have completed the first exercise.

Ahora puedes:
1. Experimentar con tus propias queries
2. Try different partition sizes
3. Continuar con **Ejercicio 02: Medallion Architecture**
4. Explore Time Travel (next exercise)

---

**Questions?** Check the [README principal](../README.md) or query the [hints](../hints.md).
