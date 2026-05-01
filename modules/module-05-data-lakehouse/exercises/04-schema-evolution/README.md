# Ejercicio 04: Schema Evolution

## 🎯 Objetivo
Manejar cambios de schema sin romper aplicaciones existentes.

**Dificultad**: ⭐⭐⭐⭐ Avanzado | **Tiempo**: 30-45 minutos

## 📋Tareas

1. **Add Column**: Agregar `customer_segment` (VIP/Regular/New)
2. **Change Type**: Cambiar `amount` de Float a Decimal(10,2)
3. **Rename Column**: Renombrar `user_id` a `customer_id`
4. **Drop Column**: Eliminar column obsoleta

## ✅ Comandos Clave

```python
# Merge schema on write
df.write.format("delta").mode("append").option("mergeSchema", "true").save(path)

# Change column type
delta_table.alterColumn("amount", DecimalType(10, 2))

# Rename column  
spark.sql("ALTER TABLE delta.`path` RENAME COLUMN user_id TO customer_id")
```

## 🎓 Conceptos

- **Schema enforcement**: Delta valida tipos
- **Schema evolution**: Permite cambios compatibles  
- **Backward compatibility**: Lectores antiguos funcionan
