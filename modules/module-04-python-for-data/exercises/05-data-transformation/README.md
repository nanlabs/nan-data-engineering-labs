# Ejercicio 05: Data Transformation

## Objetivos

✅ Implementar pipelines ETL completos  
✅ Flatten datos JSON anidados  
✅ Joins complejos entre datasets  
✅ Data quality validation
✅ Transformaciones avanzadas  

## Conceptos Clave

### ETL pipeline

```python
def etl_pipeline(source, destination):
    # Extract
    df = pd.read_csv(source)
    
    # Transform
    df = df.dropna()
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['total'] = df['precio'] * df['cantidad']
    
    # Load
    df.to_parquet(destination)
```

### Flatten JSON

```python
df = pd.json_normalize(data, sep='_')
```

## Ejercicios

Usa TODOS los datasets en `data/raw/`.

1. **extraer_datos**(rutas) → dict con DataFrames
2. **limpiar_customers**(df) → DataFrame limpio
3. **flatten_orders**(df) → DataFrame con items aplanados
4. **calcular_metricas_orden**(df) → DataFrame con totales
5. **join_customers_orders**(customers, orders) → DataFrame joined
6. **agregar_ventas_por_cliente**(df) → DataFrame agregado
7. **detectar_problemas_calidad**(df) → dict con issues
8. **normalizar_fechas**(df, columns) → DataFrame normalizado
9. **pipeline_etl_completo**(source_dir, dest_dir) → Ejecuta ETL
10. **generate_quality_report**(df) → dict with metrics

## Execution

```bash
pytest exercises/05-data-transformation/tests/ -v
```

➡️ **Siguiente**: Ejercicio 06
