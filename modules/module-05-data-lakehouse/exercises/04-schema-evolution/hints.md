# 💡 Hints - Ejercicio 04: Schema Evolution

## 🎯 Conceptos Clave

### Schema Evolution
Delta Lake permite evolucionar el schema de una table sin romper pipelines existentes:
- **Add columns**: Agregar nuevas columns
- **Remove columns**: Eliminar columns (lectura ignora columns inexistentes)
- **Change types**: Cambiar tipos de datos (requiere overwriteSchema)
- **Rename columns**: Renombrar (complejo, requiere mapping)

### Opciones Importantes
- `mergeSchema=true`: Automatic merge of schemas when writing
- `overwriteSchema=true`: Permite cambios incompatibles (cambio de tipos, orden)

---

## 📝 schema_evolution.py

### 1. Crear table inicial
```python
df = spark.read.json("../../../data/raw/transactions.json").limit(1000)
df.write.format("delta").mode("overwrite").save(path)

# Ver schema
spark.read.format("delta").load(path).printSchema()
```

### 2. Agregar column con mergeSchema
```python
# Opción A: Agregar columna calculada
df_with_segment = df.withColumn(
    "customer_segment",
    when(col("amount") > 1000, "VIP")
    .when(col("amount") > 500, "Premium")
    .otherwise("Regular")
)

# Escribir con mergeSchema
df_with_segment.write.format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .save(path)

# Opción B: Agregar columna con valor constante
df_with_col = df.withColumn("is_validated", lit(False))
```

**⚠️ Sin mergeSchema:**
```python
# ❌ Error: Schema mismatch
df_with_segment.write.format("delta").mode("append").save(path)
# AnalysisException: A schema mismatch detected when writing to the Delta table
```

**✅ Con mergeSchema:**
```python
# ✅ Funciona
df_with_segment.write.format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .save(path)
```

### 3. Cambiar tipo de column
```python
from pyspark.sql.types import DecimalType, StringType, TimestampType

# Leer datos existentes
df_current = spark.read.format("delta").load(path)

# Opción A: Cambiar tipo numérico
df_retyped = df_current.withColumn(
    "amount", 
    col("amount").cast(DecimalType(10, 2))
)

# Opción B: Cambiar a String
df_retyped = df_current.withColumn(
    "transaction_id",
    col("transaction_id").cast(StringType())
)

# Opción C: Cambiar a Timestamp
df_retyped = df_current.withColumn(
    "timestamp",
    col("timestamp").cast(TimestampType())
)

# Sobrescribir con nuevo schema
df_retyped.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(path)
```

**⚠️ Importante:**
- Cambios de tipo requieren `overwriteSchema=true`
- Some changes may cause data loss (ex: String → Int)
- Always check after change

### 4. Eliminar columns (Projection)
```python
# Delta Lake no tiene "drop column" físico
# En su lugar, proyecta solo las columnas deseadas

# Leer sin columnas no deseadas
df_filtered = spark.read.format("delta").load(path) \
    .select("transaction_id", "amount", "timestamp")  # Sin customer_segment

# Sobrescribir
df_filtered.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(path)

# ⚠️ Los datos antiguos de las columnas eliminadas permanecen hasta VACUUM
```

### 5. Ver historial de cambios
```python
from delta.tables import DeltaTable

delta_table = DeltaTable.forPath(spark, path)
history = delta_table.history()

# Ver operaciones que cambiaron schema
history.select(
    "version",
    "timestamp",
    "operation",
    "operationParameters.mergeSchema",
    "operationParameters.overwriteSchema"
).show(truncate=False)

# Ver details con schema completo
details = spark.sql(f"DESCRIBE DETAIL delta.`{path}`")
details.select("name", "location", "numFiles", "sizeInBytes").show(truncate=False)
```

---

## 🚨 Errores Comunes

### Error 1: Schema mismatch sin mergeSchema
```
AnalysisException: A schema mismatch detected when writing to the Delta table
```
**Solution:** Add`.option("mergeSchema", "true")`

### Error 2: Cambio de tipo sin overwriteSchema
```
AnalysisException: Cannot change data type: amount
```
**Solution:** Add`.option("overwriteSchema", "true")`

### Error 3: Incompatibilidad en orden de columns
```python
# ❌ MAL - diferentes órdenes
df1 = spark.createDataFrame([(1, "a")], ["id", "name"])
df2 = spark.createDataFrame([("b", 2)], ["name", "id"])

df1.write.format("delta").mode("overwrite").save(path)
df2.write.format("delta").mode("append").save(path)  # Error!

# ✅ BIEN - usar mergeSchema
df2.write.format("delta").mode("append").option("mergeSchema", "true").save(path)
```

### Error 4: Data loss in cast
```python
# ⚠️ PRECAUCIÓN
df.withColumn("text_field", col("text_field").cast("int"))  # Nulls si no es numérico

# ✅ MEJOR - validar primero
df.filter(col("text_field").cast("int").isNotNull())
```

---

## 📚 Patterns Avanzados

### Pattern 1: Add multiple columns
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
```

### Pattern 2: Schema Evolution con Merge
```python
from delta.tables import DeltaTable

# Preparar nuevos datos con columnas adicionales
new_df = spark.read.json("new_data.json")  # Tiene columna extra

# Merge con mergeSchema
delta_table = DeltaTable.forPath(spark, path)
delta_table.alias("target").merge(
    new_df.alias("source"),
    "target.id = source.id"
).whenMatchedUpdateAll() \
 .whenNotMatchedInsertAll() \
 .execute()  # ⚠️ No soporta mergeSchema directamente

# Workaround: Insert primero con mergeSchema
new_df.write.format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .save(path + "_temp")
```

### Pattern 3: Backward Compatible Schema
```python
# Asegurar que lectores antiguos funcionen
# Usar valores por defecto para nuevas columnas
df_compat = df.fillna({
    "new_column": "DEFAULT_VALUE",
    "new_metric": 0.0
})
```

### Pattern 4: Schema Validation
```python
# Validar schema antes de escribir
expected_cols = {"transaction_id", "amount", "timestamp", "status"}
actual_cols = set(df.columns)

if not expected_cols.issubset(actual_cols):
    missing = expected_cols - actual_cols
    raise ValueError(f"Missing columns: {missing}")

# O usar schema enforcement
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

expected_schema = StructType([
    StructField("transaction_id", StringType(), False),
    StructField("amount", DoubleType(), False),
    StructField("timestamp", StringType(), False)
])

# Aplicar schema
df_typed = spark.read.schema(expected_schema).json("data.json")
```

---

## 🎓 Conceptos Avanzados

### Column Mapping
Delta Lake 2.0+ soporta column mapping para renombrar:

```python
# Habilitar column mapping
spark.conf.set("spark.databricks.delta.properties.defaults.columnMapping.mode", "name")

# Crear tabla con column mapping
df.write.format("delta") \
    .option("delta.columnMapping.mode", "name") \
    .save(path)

# Ahora puedes renombrar
spark.sql(f"""
    ALTER TABLE delta.`{path}`
    RENAME COLUMN old_name TO new_name
""")
```

### Schema Evolution Constraints
```python
# Agregar constraints que evolucionan con el schema
spark.sql(f"""
    ALTER TABLE delta.`{path}`
    ADD CONSTRAINT valid_amount CHECK (amount >= 0)
""")

# Ver constraints
spark.sql(f"DESCRIBE DETAIL delta.`{path}`") \
    .select("constraints").show(truncate=False)
```

### Schema Fingerprinting
```python
# Generar fingerprint del schema para tracking
import hashlib
import json

def schema_fingerprint(schema):
    """Genera hash del schema para comparación"""
    schema_dict = json.loads(schema.json())
    schema_str = json.dumps(schema_dict, sort_keys=True)
    return hashlib.md5(schema_str.encode()).hexdigest()

# Usar
current_schema = spark.read.format("delta").load(path).schema
fingerprint = schema_fingerprint(current_schema)
print(f"Schema fingerprint: {fingerprint}")
```

---

## ✅ Checklist de Completitud

- [ ] table inicial creada con schema base
- [ ] column `customer_segment` agregada correctamente
- [ ] Tipo de `amount` cambiado a Decimal(10,2)
- [ ] Schema final muestra todos los cambios
- [ ] Historial muestra operaciones con mergeSchema/overwriteSchema
- [ ] Code uses .option("mergeSchema", "true") appropriately
- [ ] Code uses .option("overwriteSchema", "true") for type changes
- [ ] No hay errors de schema mismatch
