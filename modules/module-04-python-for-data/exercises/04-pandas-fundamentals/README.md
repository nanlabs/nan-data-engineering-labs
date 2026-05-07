# Exercise 04: Pandas Fundamentals

## Objectives

✅ Basic operations with DataFrames
✅ Filtering and selection of data
✅ Cleaning de data (nulls, duplicados)  
✅ Groupby y agregaciones  
✅ Merges y joins  

## Conceptos Clave

### Data Selection

```python
# Por columna
df['nombre']
df[['nombre', 'edad']]

# Por fila (loc/iloc)
df.loc[0]  # Por index
df.iloc[0]  # Por posicion

# Filtrado
df[df['edad'] > 25]
df[(df['edad'] > 25) & (df['pais'] == 'USA')]
```text

### Cleaning

```python
# Nulls
df.isna().sum()
df.dropna()
df.fillna(0)

# Duplicados
df.duplicated().sum()
df.drop_duplicates()
```text

### Groupby

```python
df.groupby('categoria')['precio'].mean()
df.groupby(['pais', 'ciudad']).size()
```text

## Exercises

Usa `data/raw/customers.csv` y `data/raw/transactions.csv`.

1. **load_and_explore**(path) → dict with basic info
2. **filtrar_por_pais**(df, pais) → DataFrame filtrado
3. **limpiar_data**(df) → DataFrame sin nulls ni duplicados
4. **calcular_estadisticas**(df, column) → dict con mean/median/std
5. **agrupar_por_column**(df, column) → DataFrame agrupado
6. **top_n_registros**(df, column, n) → Top N valores
7. **detectar_outliers**(df, column) → DataFrame con outliers
8. **merge_datasets**(df1, df2, on) → DataFrame merged
9. **crear_column_calculada**(df, formula) → DataFrame con nueva column
10. **full_summary**(df) → dict with full analysis

## Execution

```bash
pytest exercises/04-pandas-fundamentals/tests/ -v
```

➡️ **Siguiente**: Exercise 05
