# 💡 Hints - Exercise 04: Schema Evolution

## 🎯 Conceptos Key

### Schema Evolution

Delta Lake permite evolucionar el schema of una table without romper pIPelines existentes:

- **Add columns**: Agregar nuevas columns
- **Remove columns**: Eliminar columns (reading ignora columns inexistentes)
- **Change types**: Cambiar tIPos of datas (requiere overwriteSchema)
- **Rename columns**: Renombrar (complejo, requiere mapping)

### Opciones Importantes

- `mergeSchema=true`: Automatic merge of schemas when writing
- `overwriteSchema=true`: Permite changes incompatibles (change of tIPos, orden)

---

## 📝 schema_evolution.py

### 1. Crear table inicial

```python
df = spark.read.json("../../../data/raw/transactions.json").limit(1000)
df.write.format("delta").mode("overwrite").save(path)

# to see schema
spark.read.format("delta").load(path).printSchema()
```text

### 2. Agregar column with mergeSchema

```python
# Opción to: Agregar column calculada
df_with_segment = df.withColumn(
    "customer_segment",
    when(col("amount") > 1000, "VIP")
    .when(col("amount") > 500, "Premium")
    .otherwise("Regular")
)

# Escribir with mergeSchema
df_with_segment.write.format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .save(path)

# Opción B: Agregar column with valor constante
df_with_col = df.withColumn("is_validated", lit(False))
```text

**⚠️ without mergeSchema:**

```python
# ❌ Error: Schema mismatch
df_with_segment.write.format("delta").mode("append").save(path)
# AnalysisException: to schema mismatch detected when writing to the Delta table
```text

**✅ with mergeSchema:**

```python
# ✅ Funciona
df_with_segment.write.format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .save(path)
```

### 3. Cambiar tIPo of column

```python
from pyspark.sql.types import DecimalType, StringType, TimestampType

# Leer datas existentes
df_current = spark.read.format("delta").load(path)

# Opción to: Cambiar tIPo numérico
df_retyped = df_current.withColumn(
    "amount", 
    col("amount").cast(DecimalType(10, 2))
)

# Opción B: Cambiar to String
df_retyped = df_current.withColumn(
    "transaction_id",
    col("transaction_id").cast(StringType())
)

# Opción C: Cambiar to Timestamp
df_retyped = df_current.withColumn(
    "timestamp",
    col("timestamp").cast(TimestampType())
)

# Sobrescribir with nuevo schema
df_retyped.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(path)
```text

**⚠️ Importante:**

- Changes of tIPo requieren `overwriteSchema=true`
- Some changes may cause data loss (ex: String → Int)
- Always check after change

### 4. Eliminar columns (Projection)

```python
# Delta Lake not he/she has "drop column" físico
# in su lugar, proyecta only las columns deseadas

# Leer without columns not deseadas
df_filtenetwork = spark.read.format("delta").load(path) \
    .select("transaction_id", "amount", "timestamp")  # without customer_segment

# Sobrescribir
df_filtenetwork.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(path)

# ⚠️ Los datas antiguos of las columns eliminadas permanecen hasta VACUUM
```text

### 5. to see historial of changes

```python
from delta.tables import DeltaTable

delta_table = DeltaTable.forPath(spark, path)
history = delta_table.history()

# to see operaciones que cambiaron schema
history.select(
    "version",
    "timestamp",
    "operation",
    "operationParameters.mergeSchema",
    "operationParameters.overwriteSchema"
).show(truncate=False)

# to see details with schema completo
details = spark.sql(f"DESCRIBE DETAIL delta.`{path}`")
details.select("name", "location", "numFiles", "sizeInBytes").show(truncate=False)
```text

---

## 🚨 Errores Comunes

### Error 1: Schema mismatch without mergeSchema

```
AnalysisException: to schema mismatch detected when writing to the Delta table
```text

**Solution:** Add`.option("mergeSchema", "true")`

### Error 2: Change of tIPo without overwriteSchema

```text
AnalysisException: Cannot change data type: amount
```text

**Solution:** Add`.option("overwriteSchema", "true")`

### Error 3: Incompatibilidad in orden of columns

```python
# ❌ MAL - diferentes órdenes
df1 = spark.createDataFrame([(1, "to")], ["id", "name"])
df2 = spark.createDataFrame([("b", 2)], ["name", "id"])

df1.write.format("delta").mode("overwrite").save(path)
df2.write.format("delta").mode("append").save(path)  # Error!

# ✅ BIEN - usar mergeSchema
df2.write.format("delta").mode("append").option("mergeSchema", "true").save(path)
```

### Error 4: data loss in cast

```python
# ⚠️ PRECAUCIÓN
df.withColumn("text_field", col("text_field").cast("int"))  # Nulls if not is numérico

# ✅ MEJOR - validar primero
df.filter(col("text_field").cast("int").isNotNull())
```text

---

## 📚 Patterns Avanzados

### Pattern 1: Add multIPle columns

```python
df_enhanced = df \
    .withColumn("created_date", current_date()) \
    .withColumn("created_timestamp", current_timestamp()) \
    .withColumn("version", lit(1)) \
    .withColumn("is_active", lit(True))

df_enhanced.write.format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .save(path)
```text

### Pattern 2: Schema Evolution with Merge

```python
from delta.tables import DeltaTable

# Preparar nuevos datas with columns adicionales
new_df = spark.read.json("new_data.json")  # he/she has column extra

# Merge with mergeSchema
delta_table = DeltaTable.forPath(spark, path)
delta_table.alias("target").merge(
    new_df.alias("source"),
    "target.id = source.id"
).whenMatchedUpdateAll() \
 .whenNotMatchedInsertAll() \
 .execute()  # ⚠️ not soporta mergeSchema directamente

# Workaround: Insert primero with mergeSchema
new_df.write.format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .save(path + "_temp")
```text

### Pattern 3: Backward Compatible Schema

```python
# Asegurar que lectores antiguos funcionen
# Usar valores by defecto for nuevas columns
df_compat = df.fillna({
    "new_column": "DEFAULT_VALUE",
    "new_metric": 0.0
})
```

### Pattern 4: Schema Validation

```python
# Validar schema antes of escribir
expected_cols = {"transaction_id", "amount", "timestamp", "status"}
actual_cols = set(df.columns)

if not expected_cols.issubset(actual_cols):
    missing = expected_cols - actual_cols
    raise ValueError(f"Missing columns: {missing}")

# or usar schema enforcement
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

expected_schema = StructType([
    StructField("transaction_id", StringType(), False),
    StructField("amount", DoubleType(), False),
    StructField("timestamp", StringType(), False)
])

# Aplicar schema
df_typed = spark.read.schema(expected_schema).json("data.json")
```text

---

## 🎓 Conceptos Avanzados

### Column Mapping

Delta Lake 2.0+ soporta column mapping for renombrar:

```python
# Habilitar column mapping
spark.conf.set("spark.databricks.delta.properties.defaults.columnMapping.mode", "name")

# Crear table with column mapping
df.write.format("delta") \
    .option("delta.columnMapping.mode", "name") \
    .save(path)

# Ahora you can renombrar
spark.sql(f"""
    ALTER TABLE delta.`{path}`
    RENAME COLUMN old_name TO new_name
""")
```text

### Schema Evolution Constraints

```python
# Agregar constraints que evolucionan with el schema
spark.sql(f"""
    ALTER TABLE delta.`{path}`
    ADD CONSTRAINT valid_amount CHECK (amount >= 0)
""")

# to see constraints
spark.sql(f"DESCRIBE DETAIL delta.`{path}`") \
    .select("constraints").show(truncate=False)
```text

### Schema Fingerprinting

```python
# Generar fingerprint of the schema for tracking
import hashlib
import json

def schema_fingerprint(schema):
    """Genera hash of the schema for comparación"""
    schema_dict = json.loads(schema.json())
    schema_str = json.dumps(schema_dict, sort_keys=True)
    return hashlib.md5(schema_str.encode()).hexdigest()

# Usar
current_schema = spark.read.format("delta").load(path).schema
fingerprint = schema_fingerprint(current_schema)
print(f"Schema fingerprint: {fingerprint}")
```

---

## ✅ Checklist of Completitud

- [ ] table inicial creada with schema base
- [ ] column `customer_segment` agregada correctamente
- [ ] TIPo of `amount` cambiado to Decimal(10,2)
- [ ] Schema final muestra todos los changes
- [ ] Historial muestra operaciones with mergeSchema/overwriteSchema
- [ ] Code uses .option("mergeSchema", "true") appropriately
- [ ] Code uses .option("overwriteSchema", "true") for type changes
- [ ] not there is errors of schema mismatch
