# Exercise 04: Schema Evolution

## 🎯 Objective
Manejar changes of schema without romper aplicaciones existentes.

**Difficulty**: ⭐⭐⭐⭐ Avanzado | **Tiempo**: 30-45 minutos

## 📋Tareas

1. **Add Column**: Agregar `customer_segment` (VIP/Regular/New)
2. **Change Type**: Cambiar `amount` of Float to Decimal(10,2)
3. **Rename Column**: Renombrar `user_id` to `customer_id`
4. **Drop Column**: Eliminar column obsoleta

## ✅ Commands Key

```python
# Merge schema on write
df.write.format("delta").mode("append").option("mergeSchema", "true").save(path)

# Change column type
delta_table.alterColumn("amount", DecimalType(10, 2))

# Rename column  
spark.sql("ALTER TABLE delta.`path` RENAME COLUMN user_id TO customer_id")
```

## 🎓 Conceptos

- **Schema enforcement**: Delta valida tIPos
- **Schema evolution**: Permite changes compatibles  
- **Backward compatibility**: Lectores antiguos funcionan
