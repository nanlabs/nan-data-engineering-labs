# Ejercicio 03: Time Travel y Versionado

## 🎯 Objetivo

Dominar Delta Lake Time Travel para:
- Consult historical versions
-Rollback a versiones anteriores
- Audit and compliance
- Reproducibilidad en ML

**Dificultad**: ⭐⭐⭐ Intermedio  
**Tiempo**: 45-60 minutos

---

## 📋 Tareas

### Tarea 1: Crear y Modificar table con Versiones
**Script**: `01_create_versions.py`

Create a table with multiple versions:
1. V0: Crear table inicial (10K registros)
2. V1: Append 5K registros
3. V2: Update status='expired' para transactions antiguas
4. V3: Delete registros con error
5. Verificar historial con `.history()`

### Tarea 2: Time Travel Queries
**Script**: `02_time_travel_queries.py`

1. Specific version query:`versionAsOf(1)`
2. Query por timestamp: `timestampAsOf("2024-01-01")`
3. Compare V0 vs V3 (what changed)
4. Restaurar archivo borrado por error

### Task 3: Audit and Rollback
**Script**: `03_audit_rollback.py`

1. Ver historial completo de operaciones
2. Identify problematic operation
3. Rollback to previous version
4. Verify integrity after rollback

---

## ✅ Success Criteria

- [ ] table con 4+ versiones
- [ ] Queries time travel exitosos
- [ ] Rollback funcional
- [ ] Documentation of changes by version

---

## 🎓 Conceptos

### Time Travel Syntax

```python
# Por versión
df = spark.read.format("delta").option("versionAsOf", 0).load(path)

# Por timestamp
df = spark.read.format("delta").option("timestampAsOf", "2024-01-01").load(path)

# SQL
spark.sql("SELECT * FROM table VERSION AS OF 2")
spark.sql("SELECT * FROM table TIMESTAMP AS OF '2024-01-01'")
```

### Use Cases

- **Audit**: What data was there on 12/31/2023?
- **Rollback**: Undo wrong change
- **ML Reproducibility**: Entrenar con mismos datos
- **A/B Testing**: Compare metrics between versions
