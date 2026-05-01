# Ejercicio 01: Delta Lake Basics

## 🎯 Objetivo

Aprender los fundamentos de Delta Lake:
- Crear tables Delta desde DataFrames
- Basic operations: append, overwrite
- Lectura de tables Delta
- Basic queries with Spark SQL

**Difficulty**: ⭐ Basic
**Tiempo Estimado**: 45-60 minutos  
**Prerequisitos**: Docker y Docker Compose instalados

---

## 📋Exercise Description

Your company is migrating from Parquet to Delta Lake as a storage format. You need:

1. **Ingestar datos iniciales** de transactions a una table Delta
2. **Agregar nuevos registros** con modo append
3. **Overwrite data** from a specific partition
4. **Consultar la table** con Spark SQL
5. **Verificar metadatos** de la table Delta

---

## 🗂️ Estructura del Ejercicio

```
01-delta-basics/
├── README.md (este archivo)
├── hints.md
├── starter/
│   ├── 01_create_table.py          # Crear tabla Delta inicial
│   ├── 02_append_data.py            # Agregar registros
│   ├── 03_overwrite_partition.py   # Sobrescribir partición
│   ├── 04_query_table.py            # Consultas SQL
│   └── requirements.txt
├── solution/
│   ├── 01_create_table.py
│   ├── 02_append_data.py
│   ├── 03_overwrite_partition.py
│   ├── 04_query_table.py
│   └── README.md
└── tests/
    └── test_delta_basics.py
```

---

## 🚀 Setup

### 1. Iniciar la infraestructura

```bash
cd ../../infrastructure
docker-compose up -d
```

Verify that all services are running:
```bash
docker-compose ps
```

You should see:
- `spark-master` (puerto 8080)
- `spark-worker` (puerto 8081)
- `minio` (puertos 9000, 9001)
- `hive-metastore` (puerto 9083)
- `jupyter` (puerto 8888)

### 2. Acceder a Jupyter

Abre tu navegador en: http://localhost:8888

No requiere password (configurado para desarrollo local).

### 3. Ejecutar los scripts

Puedes ejecutar los scripts de dos formas:

**Option A: From Jupyter Notebook**
- Carga cada script `.py` en una nueva celda
- Ejecuta celda por celda

**Option B: From the container terminal**
```bash
docker exec -it module-05-spark-master bash
cd /opt/spark/work-dir/exercises/01-delta-basics/starter
spark-submit --master local[2] 01_create_table.py
```

---

## 📝 Tareas

### Tarea 1: Crear table Delta Inicial

**Archivo**: `starter/01_create_table.py`

1. Lee el archivo `data/raw/transactions.json` (primeras 10,000 rows)
2. Convierte timestamps a formato datetime
3. Agrega una column `ingestion_date` con la fecha actual
4. Guarda como table Delta en `s3a://bronze/transactions_delta`
5. Particiona por `country`

**Expectativas**:
- table creada en formato Delta
- Partitioned by country
- Metadatos verificables

### Tarea 2: Agregar Nuevos Registros

**Archivo**: `starter/02_append_data.py`

1. Lee las siguientes 5,000 transactions del JSON
2. Procesa igual que en Tarea 1
3. Agrega los datos a la table existente usando `.mode("append")`
4. Verifica que el total de registros sea 15,000

**Expectativas**:
- Append exitoso sin duplicar datos
- Total de registros correcto
- Sin sobrescribir datos existentes

### Task 3: Overwrite Partition

**Archivo**: `starter/03_overwrite_partition.py`

1. Read data from a specific country (ex: "USA")
2. Modifica el campo `status` de "pending" a "expired"
3. Overwrite only that country's partition using:
   ```python
   .mode("overwrite")
   .option("replaceWhere", "country = 'USA'")
   ```
4. Verifica que otras particiones no se afectaron

**Expectativas**:
- Only the specified partition is overwritten
- Otras particiones intactas
- Cambios reflejados en querys

### Tarea 4: Consultar con Spark SQL

**Archivo**: `starter/04_query_table.py`

Ejecuta las siguientes querys SQL sobre la table Delta:

1. **Count records by country**:
   ```sql
   SELECT country, COUNT(*) as total
   FROM transactions_delta
   GROUP BY country
   ORDER BY total DESC
   ```

2. **transactions por status**:
   ```sql
   SELECT status, COUNT(*) as count, 
          AVG(amount) as avg_amount
   FROM transactions_delta
   GROUP BY status
   ```

3. **Top 10 largest transactions**:
   ```sql
   SELECT transaction_id, user_id, amount, currency, country
   FROM transactions_delta
   ORDER BY amount DESC
   LIMIT 10
   ```

4. **transactions por mes**:
   ```sql
   SELECT DATE_TRUNC('month', timestamp) as month,
          COUNT(*) as transactions,
          SUM(amount) as total_amount
   FROM transactions_delta
   GROUP BY month
   ORDER BY month
   ```

**Expectativas**:
- Todas las queries ejecutan correctamente
- Resultados guardados en DataFrames
- Reasonable execution times (<5 seconds)

---

## ✅ Success Criteria

Your implementation must:

1. **Crear table Delta** con particionamiento correcto
2. **Append funcionando** sin duplicados
3. **Partition overwrite** without affecting others
4. **Queries SQL** devolviendo resultados correctos
5. **Verificaciones**:
   - `_delta_log/` directory existe
   - Parquet files in subdirectories by country
   - Transaction log has multiple versions

### Quick Verification

Run this script to validate your implementation:

```python
from delta.tables import DeltaTable

# Verificar que la tabla existe
delta_table = DeltaTable.forPath(spark, "s3a://bronze/transactions_delta")

# Ver historial de versiones
history = delta_table.history()
print(f"Versiones: {history.count()}")

# Debe tener al menos 3 versiones (create, append, overwrite)
assert history.count() >= 3, "Faltan operaciones"

# Verificar registros
total = spark.read.format("delta").load("s3a://bronze/transactions_delta").count()
print(f"Total registros: {total}")

# Verificar particiones
partitions = spark.read.format("delta") \
    .load("s3a://bronze/transactions_delta") \
    .select("country").distinct().count()
print(f"Países (particiones): {partitions}")

print("✅ Validación exitosa!")
```

---

## 🎓 Conceptos Clave

### Formato Delta Lake

Delta Lake almacena datos en Parquet + transaction log:

```
bronze/transactions_delta/
├── _delta_log/
│   ├── 00000000000000000000.json  # Versión 0 (create)
│   ├── 00000000000000000001.json  # Versión 1 (append)
│   ├── 00000000000000000002.json  # Versión 2 (overwrite)
│   └── _last_checkpoint
├── country=USA/
│   ├── part-00000-xxx.snappy.parquet
│   └── part-00001-xxx.snappy.parquet
├── country=GBR/
│   └── part-00000-xxx.snappy.parquet
└── country=DEU/
    └── part-00000-xxx.snappy.parquet
```

### Transaction Log

Each operation creates a new entry in`_delta_log/`:

```json
{
  "commitInfo": {
    "timestamp": 1709022000000,
    "operation": "WRITE",
    "operationMetrics": {
      "numFiles": "10",
      "numOutputRows": "10000"
    }
  }
}
```

### Modos de Escritura

| Modo | Comportamiento |
|------|----------------|
| `append` | Agrega datos sin tocar existentes |
| `overwrite` | Reemplaza TODA la table |
| `overwrite` + `replaceWhere`| Replace only partitions that meet the condition |
| `ignore` | No escribe si la table ya existe |
| `error` | Falla si la table ya existe (default) |

---

## 📚 resources

- [Delta Lake Documentation](https://docs.delta.io/)
- [PySpark Delta API](https://docs.delta.io/latest/api/python/index.html)
- [Delta Lake Quickstart](https://docs.delta.io/latest/quick-start.html)
- [Transaction Log Protocol](https://github.com/delta-io/delta/blob/master/PROTOCOL.md)

---

## 🔍 Troubleshooting

### Error: "Table not found"

Verify that MinIO is running and accessible:
```bash
docker exec -it module-05-minio mc ls local/bronze
```

### Error: "Java heap space"

Aumenta memoria del Spark worker en `docker-compose.yml`:
```yaml
SPARK_WORKER_MEMORY: 4g  # Aumentar a 8g
```

### Slow queries

Verify that the data is partitioned correctly:
```python
# Ver distribución de particiones
spark.read.format("delta") \
    .load("s3a://bronze/transactions_delta") \
    .groupBy("country").count().show()
```

---

## 🎯 Next Steps

Una vez completado este ejercicio:
1. ✅ Continuar con **Ejercicio 02: Medallion Architecture**
2. Explorar el transaction log con `delta_table.history()`
3. Experimentar con `df.repartition()` antes de escribir

Good luck! 🚀
