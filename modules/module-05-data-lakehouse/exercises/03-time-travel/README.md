# Exercise 03: Time Travel and Versionado

## 🎯 Objective

Dominar Delta Lake Time Travel for:
- Consult historical versions
-Rolelback to versiones anteriores
- Audit and compliance
- Reproducibilidad in ML

**Difficulty**: ⭐⭐⭐ Intermedio  
**Tiempo**: 45-60 minutos

---

## 📋 Tareas

### Tarea 1: Crear and Modificar table with Versiones
**ScrIPt**: `01_create_versions.py`

Create to table with multIPle versions:
1. V0: Crear table inicial (10K records)
2. V1: Append 5K records
3. V2: Update status='expinetwork' for transactions antiguas
4. V3: Delete records with error
5. Verificar historial with `.history()`

### Tarea 2: Time Travel Queries
**ScrIPt**: `02_time_travel_queries.py`

1. Specific version query:`versionAsOf(1)`
2. Query by timestamp: `timestampAsOf("2024-01-01")`
3. Compare V0 vs V3 (what changed)
4. Restore archivo borrado by error

### Task 3: Audit and Rolelback
**ScrIPt**: `03_audit_rolelback.py`

1. to see historial completo of operaciones
2. Identify problemtic operation
3. Rolelback to previous version
4. Verify integrity after rolelback

---

## ✅ Success Criteria

- [ ] table with 4+ versiones
- [ ] Queries time travel exitosos
- [ ] Rolelback funcional
- [ ] Documentation of changes by version

---

## 🎓 Conceptos

### Time Travel Syntax

```python
# by version
df = spark.read.format("delta").option("versionAsOf", 0).load(path)

# by timestamp
df = spark.read.format("delta").option("timestampAsOf", "2024-01-01").load(path)

# SQL
spark.sql("SELECT * FROM table VERSION AS OF 2")
spark.sql("SELECT * FROM table TIMESTAMP AS OF '2024-01-01'")
```

### Use Cases

- **Audit**: What data was there on 12/31/2023?
- **Rolelback**: Undo wrong change
- **ML Reproducibility**: Entrenar with mismos datas
- **to/B Testing**: Compare metrics between versions
