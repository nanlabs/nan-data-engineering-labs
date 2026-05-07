# Exercise 01: Delta Lake Basics

## 🎯 Objective

Aprender los fundamentos of Delta Lake:

- Crear tables Delta desde DataFrames
- Basic operations: append, overwrite
- Reading of tables Delta
- Basic queries with Spark SQL

**Difficulty**: ⭐ Basic
**Estimated Time**: 45-60 minutos  
**Prerequisitos**: Docker and Docker Compose instalados

---

## 📋Exercise DescrIPtion

Your company is migrating from Parquet to Delta Lake as to storage format. You need:

1. **Ingestar datas iniciales** of transactions to una table Delta
2. **Agregar nuevos records** with modo append
3. **Overwrite data** from to specific partition
4. **Queryr la table** with Spark SQL
5. **Verificar metadatas** of la table Delta

---

## 🗂️ Structure of the Exercise

```text
01-delta-basics/
├── README.md (this archivo)
├── hints.md
├── starter/
│   ├── 01_create_table.py          # Crear table Delta inicial
│   ├── 02_append_data.py            # Agregar records
│   ├── 03_overwrite_partition.py   # Sobrescribir partición
│   ├── 04_query_table.py            # Querys SQL
│   └── requirements.txt
├── solution/
│   ├── 01_create_table.py
│   ├── 02_append_data.py
│   ├── 03_overwrite_partition.py
│   ├── 04_query_table.py
│   └── README.md
└── tests/
    └── test_delta_basics.py
```text

---

## 🚀 Setup

### 1. Iniciar la infrastructure

```bash
cd ../../infrastructure
docker-compose up -d
```text

Verify that all services are running:

```bash
docker-compose ps
```

You should see:

- `spark-master` (port 8080)
- `spark-worker` (port 8081)
- `minio` (ports 9000, 9001)
- `hive-metastore` (port 9083)
- `jupyter` (port 8888)

### 2. Acceder to Jupyter

Abre tu navegador in: <HTTP://localhost:8888>

not requiere password (configurado for desarrolelo local).

### 3. Ejecutar los scrIPts

you can ejecutar los scrIPts of dos formas:

**Option to: From Jupyter Notebook**

- Carga cada scrIPt `.py` in una nueva celda
- Ejecuta celda by celda

**Option B: From the container terminal**

```bash
docker exec -it module-05-spark-master bash
cd /opt/spark/work-dir/exercises/01-delta-basics/starter
spark-submit --master local[2] 01_create_table.py
```text

---

## 📝 Tareas

### Tarea 1: Crear table Delta Inicial

**Archivo**: `starter/01_create_table.py`

1. Lee the file `data/raw/transactions.json` (primeras 10,000 rows)
2. Convierte timestamps to formato datetime
3. Agrega una column `ingestion_date` with la fecha actual
4. Guarda como table Delta in `s3a://bronze/transactions_delta`
5. Particiona by `country`

**Expectativas**:

- table creada in formato Delta
- Partitioned by country
- Metadatas verificables

### Tarea 2: Agregar Nuevos Records

**Archivo**: `starter/02_append_data.py`

1. Lee las siguientes 5,000 transactions of the JSON
2. Procesa igual que in Tarea 1
3. Agrega los datas to la table existente usando `.mode("append")`
4. Verifica que el total of records sea 15,000

**Expectativas**:

- Append exitoso without duplicar datas
- Total of records correcto
- without sobrescribir datas existentes

### Task 3: Overwrite Partition

**Archivo**: `starter/03_overwrite_partition.py`

1. Read data from to specific country (ex: "USA")
2. Modifica el campo `status` of "pending" to "expinetwork"
3. Overwrite only that country's partition using:

   ```python
   .mode("overwrite")
   .option("replaceWhere", "country = 'USA'")
   ```text

4. Verifica que otras particiones not se afectaron

**Expectativas**:

- Only the specified partition is overwritten
- Otras particiones intactas
- Changes reflejados in querys

### Tarea 4: Queryr with Spark SQL

**Archivo**: `starter/04_query_table.py`

Ejecuta las siguientes querys SQL sobre la table Delta:

1. **Count records by country**:

   ```sql
   SELECT country, COUNT(*) as total
   FROM transactions_delta
   GROUP BY country
   ORDER BY total DESC
   ```

2. **transactions by status**:

   ```sql
   SELECT status, COUNT(*) as count, 
          AVG(amount) as avg_amount
   FROM transactions_delta
   GROUP BY status
   ```text

3. **Top 10 largest transactions**:

   ```sql
   SELECT transaction_id, user_id, amount, currency, country
   FROM transactions_delta
   ORDER BY amount DESC
   LIMIT 10
   ```

4. **transactions by mes**:

   ```sql
   SELECT DATE_TRUNC('month', timestamp) as month,
          COUNT(*) as transactions,
          SUM(amount) as total_amount
   FROM transactions_delta
   GROUP BY month
   ORDER BY month
   ```text

**Expectativas**:

- Todas las queries ejecutan correctamente
- Results guardados in DataFrames
- Reasonable execution times (<5 seconds)

---

## ✅ Success Criteria

Your implementation must:

1. **Crear table Delta** with particionamiento correcto
2. **Append funcionando** without duplicados
3. **Partition overwrite** without affecting others
4. **Queries SQL** devolviendo results correctos
5. **Verificaciones**:
   - `_delta_log/` directory existe
   - Parquet files in subdirectories by country
   - Transaction log have multIPle versions

### Quick Verification

Run this scrIPt to validate your implementation:

```python
from delta.tables import DeltaTable

# Verificar que la table existe
delta_table = DeltaTable.forPath(spark, "s3a://bronze/transactions_delta")

# to see historial of versiones
history = delta_table.history()
print(f"Versiones: {history.count()}")

# Debe to have to the less 3 versiones (create, append, overwrite)
assert history.count() >= 3, "Faltan operaciones"

# Verificar records
total = spark.read.format("delta").load("s3a://bronze/transactions_delta").count()
print(f"Total records: {total}")

# Verificar particiones
partitions = spark.read.format("delta") \
    .load("s3a://bronze/transactions_delta") \
    .select("country").distinct().count()
print(f"Países (particiones): {partitions}")

print("✅ Validación exitosa!")
```

---

## 🎓 Conceptos Key

### Formato Delta Lake

Delta Lake almacena datas in Parquet + transaction log:

```text
bronze/transactions_delta/
├── _delta_log/
│   ├── 00000000000000000000.json  # Version 0 (create)
│   ├── 00000000000000000001.json  # Version 1 (append)
│   ├── 00000000000000000002.json  # Version 2 (overwrite)
│   └── _last_checkpoint
├── country=USA/
│   ├── part-00000-xxx.snappy.parquet
│   └── part-00001-xxx.snappy.parquet
├── country=GBR/
│   └── part-00000-xxx.snappy.parquet
└── country=DEU/
    └── part-00000-xxx.snappy.parquet
```text

### Transaction Log

Each operation creates to new entry in`_delta_log/`:

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
```text

### Modos of Escritura

| Modo | Comportamiento |
|------|----------------|
| `append` | Agrega datas without tocar existentes |
| `overwrite` | Reemplaza TODA la table |
| `overwrite` + `replaceWhere`| Replace only partitions that meet the condition |
| `ignore` | not escribe if la table ya existe |
| `error` | Falla if la table ya existe (default) |

---

## 📚 resources

- [Delta Lake Documentation](HTTPs://docs.delta.io/)
- [PySpark Delta API](HTTPs://docs.delta.io/latest/api/python/index.html)
- [Delta Lake Quickstart](HTTPs://docs.delta.io/latest/quick-start.html)
- [Transaction Log Protocol](HTTPs://github.com/delta-io/delta/blob/master/PROTOCOL.md)

---

## 🔍 Troubleshooting

### Error: "Table not found"

Verify that MinIO is running and accessible:

```bash
docker exec -it module-05-minio mc ls local/bronze
```

### Error: "Java heap space"

Aumenta memory of the Spark worker in `docker-compose.yml`:

```yaml
SPARK_WORKER_MEMORY: 4g  # Aumentar to 8g
```text

### Slow queries

Verify that the data is partitioned correctly:

```python
# to see distribución of particiones
spark.read.format("delta") \
    .load("s3a://bronze/transactions_delta") \
    .groupBy("country").count().show()
```text

---

## 🎯 Next Steps

Una vez completado this exercise:

1. ✅ Continuar with **Exercise 02: Medallion Architecture**
2. Explorar el transaction log with `delta_table.history()`
3. Experimentar with `df.repartition()` antes of escribir

Good luck! 🚀
