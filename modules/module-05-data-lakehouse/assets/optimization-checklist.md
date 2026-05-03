# Optimization Checklist

## ✅ Delta Lake Optimization Checklist

### 1. File Size Optimization

- [ ] **Problem**: Too many small files (<128MB)
  - **Yesntoma**: Queries lentos, alto overhead
  - **Solution**:`OPTIMIZE` for compactar
  ```python
  delta_table.optimize().executeCompaction()
  ```

- [ ] **Problem**: Archivos muy grandes (>1GB)
  - **Yesntoma**: Lentitud in operaciones paralelas
  - **Solution**: Repartition before writing
  ```python
  df.repartition(100).write.format("delta").save(path)
  ```

### 2. Partitioning Strategy

- [ ] **Check**: Average cardinality? (100-10,000 unique values)
  - ✅ Bueno: country, date, category
  - ❌ Malo: user_id (millones), is_active (2 valores)

- [ ] **Partition Pruning**: Ensure that queries filter by partition
  ```python
  # ✅ Bueno: Usa partición
  df.filter("date = '2024-01-15' AND country = 'USA'")
  
  # ❌ Malo: not usa partición
  df.filter("amount > 1000")
  ```

- [ ] **Evitar**: > 10,000 particiones by table

### 3. Z-Ordering (data SkIPping)

- [ ] **Aplicar to**: columns of filters frecuentes (not particiones)
  ```python
  delta_table.optimize().executeZOrderBy("user_id", "product_id")
  ```

- [ ] **not aplicar to**: 
  - columns of alta cardinalidad (>100M valores)
  - columns que nunca se filtran

- [ ] **Reexecution**: Every N days or after mass writes

### 4. data SkIPping

- [ ] **Habilitar**: Statistics collection (habilitado by default)
- [ ] **Verificar**: Stats in _delta_log
  ```python
  delta_table.detail().select("numFiles", "sizeInBytes", "numRecords").show()
  ```

### 5. Vacuum

- [ ] **Antes of VACUUM**: Confirmar retention apropiado
  ```python
  # Retener 7 días (168 horas)
  delta_table.vacuum(168)
  ```

- [ ] **Considerar**: Time Travel necesario
  - ⚠️ VACUUM elimina versiones antiguas

### 6. Caching

- [ ] **For small tables**: In-memory cache
  ```python
  df.cache()
  df.count()  # Materialize cache
  ```

- [ ] **Clear cache**: After use
  ```python
  df.unpersist()
  ```

### 7. Schema Optimization

- [ ] **Usar tIPos precisos**:
  - DecimalType in lugar of Double for dinero
  - DateType in lugar of StringType for fechas
  - IntegerType in lugar of LongType when sea suficiente

- [ ] **Normalizar**: columns with muchos nulls in tables separadas

### 8. Write Optimization

- [ ] **Batch size**: 10,000-100,000 records by write ideal
- [ ] **Auto Optimize** (Databricks):
  ```sql
  ALTER TABLE events SET TBLPROPERTIES (
    delta.autoOptimize.optimizeWrite = true,
    delta.autoOptimize.autoCompact = true
  )
  ```

### 9. Query Optimization

- [ ] **Pushdown filters**: Filtrar antes of joins
- [ ] **Select specific columns**: Evitar `SELECT *`
- [ ] **Broadcast small tables**: for joins
  ```python
  from pyspark.sql.functions import broadcast
  large_df.join(broadcast(small_df), "id")
  ```

### 10. Monitoring

- [ ] **Metrics to trackear**:
  - Query execution time
  - data skIPping ratio
  - Number of files per table
  - Average file size
  - Partition count

  ```python
  # to see estadísticas
  delta_table.detail().select(
      "numFiles", 
      "sizeInBytes", 
      "numRecords"
  ).show()
  
  # to see historial of optimization
  delta_table.history().filter("operation = 'OPTIMIZE'").show()
  ```

## 🎯 Performance Targets

| Metric | Target |
|---------|--------|
| File size promedio | 128MB - 512MB |
| Particiones | 100 - 5,000 |
| Files by partition | < 100 |
| Query latency (simple) | < 5s |
| Query latency (complex) | < 30s |
| data skIPping % | > 80% |

## 🔍 Troubleshooting

### Query lento?
1. Check if usa partition pruning
2. Check number of files (ejecutar OPTIMIZE?)
3. Check if Z-ORDER would help
4. Check execution plan with `.explain()`

### Writes lentos?
1. Check batch size (too small?)
2. Check number of write partitions
3. Check if automatic Z-ORDER is active
4. Consider disabling merge schema if not necesario

### Storage growing fast?
1. Ejecutar VACUUM
2. Check retention policy
3. Check if there is duplicate data
4. Consider archiving old partitions
