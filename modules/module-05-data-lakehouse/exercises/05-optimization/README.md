# Exercise 05: Optimization (Z-Ordering, Compaction, data SkIPping)

## 🎯 Objective
Optimize performance with advanced optimization techniques.

**Difficulty**: ⭐⭐⭐⭐ Avanzado | **Tiempo**: 45 minutos

## 📋 Tareas

1. **OPTIMIZE**: Compact small files
2. **Z-ORDER**: Colocar datas juntos by columns frecuentes
3. **data SkIPping**: Verificar improvement of performance
4. **VACUUM**: Limpiar archivos antiguos

## ✅ Commands

```python
# Optimize + Z-Order
delta_table.optimize().executeZOrderBy("country", "date")

# Vacuum (retener 7 días)
delta_table.vacuum(168)  # horas

# to see estadísticas
delta_table.detail().select("numFiles", "sizeInBytes").show()
```

## 🎓 Conceptos

- **Small files problem**: Many small files = slow
- **Z-Ordering**: Co-locality for queries frecuentes
- **data SkIPping**: SkIP archivos without datas relevantes
- **Vacuum**: Borra versiones antiguas (cuidado with Time Travel)
