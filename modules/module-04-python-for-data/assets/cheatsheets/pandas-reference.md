# 🐼 Pandas Reference - Operaciones Esenciales

## 📋 Import and Creation

### Importar Pandas
```python
import pandas as pd
import numpy as np

# Verificar versión
pd.__version__
```

### Crear DataFrames
```python
# Desde diccionario
df = pd.DataFrame({
    'nombre': ['Ana', 'Luis', 'María'],
    'edad': [25, 30, 28],
    'ciudad': ['Madrid', 'Barcelona', 'Valencia']
})

# Desde listas
df = pd.DataFrame(
    [['Ana', 25], ['Luis', 30]],
    columns=['nombre', 'edad']
)

# Desde CSV
df = pd.read_csv('datos.csv')
df = pd.read_csv('datos.csv', sep=';', encoding='utf-8')

# Desde JSON
df = pd.read_json('datos.json')
df = pd.read_json('datos.json', orient='records')

# Desde Parquet
df = pd.read_parquet('datos.parquet')
```

## 🔍 Initial Exploration

### Basic Information
```python
# Primeras/últimas filas
df.head()           # 5 primeras filas
df.head(10)         # 10 primeras filas
df.tail()           # 5 últimas filas

# Información del DataFrame
df.info()           # Tipos, nulls, memoria
df.describe()       # Estadísticas numéricas
df.shape            # (filas, columnas)
df.columns          # Nombres de columnas
df.dtypes           # Tipos de datos
df.index            # Índice

# Valores únicos
df['columna'].unique()          # Array de únicos
df['columna'].nunique()         # Cantidad de únicos
df['columna'].value_counts()    # Frecuencia de valores
```

## 🎯 Data Selection

### Column selection
```python
# Una columna (Series)
df['nombre']
df.nombre  # Notación de atributo

# Múltiples columnas (DataFrame)
df[['nombre', 'edad']]

# Reordenar columnas
df[['edad', 'nombre', 'ciudad']]
```

### Row selection

#### By Position (iloc)
```python
# Una fila
df.iloc[0]              # Primera fila

# Múltiples filas
df.iloc[0:5]            # Filas 0 a 4
df.iloc[[0, 2, 4]]      # Filas específicas

# Filas y columnas
df.iloc[0:5, 0:2]       # Filas 0-4, columnas 0-1
df.iloc[:, [0, 2]]      # Todas las filas, columnas 0 y 2
```

#### Por Etiqueta (loc)
```python
# Por índice
df.loc[0]               # Fila con índice 0
df.loc[0:5]             # Filas 0 a 5 (INCLUYE 5)

# Por condición
df.loc[df['edad'] > 25]
df.loc[df['ciudad'] == 'Madrid']

# Filas y columnas
df.loc[df['edad'] > 25, ['nombre', 'edad']]
```

### Filtrado (Boolean Indexing)
```python
# Condición simple
df[df['edad'] > 25]
df[df['nombre'] == 'Ana']

# Múltiples condiciones (AND)
df[(df['edad'] > 25) & (df['ciudad'] == 'Madrid')]

# Múltiples condiciones (OR)
df[(df['edad'] > 30) | (df['ciudad'] == 'Madrid')]

# NOT
df[~(df['edad'] > 25)]

# IN
ciudades = ['Madrid', 'Barcelona']
df[df['ciudad'].isin(ciudades)]

# String contains
df[df['nombre'].str.contains('Ana')]

# Between
df[df['edad'].between(25, 30)]
```

## 🔧 Transformaciones

### Crear/Modificar columns
```python
# Nueva columna
df['edad_doble'] = df['edad'] * 2

# Columna calculada
df['mayor_edad'] = df['edad'] >= 18

# Apply (aplicar función)
df['nombre_upper'] = df['nombre'].apply(lambda x: x.upper())
df['nombre_upper'] = df['nombre'].str.upper()  # Más eficiente

# Map (mapear valores)
mapa = {'Madrid': 'MAD', 'Barcelona': 'BCN'}
df['ciudad_codigo'] = df['ciudad'].map(mapa)

# Renombrar columnas
df.rename(columns={'nombre': 'name', 'edad': 'age'}, inplace=True)
```

### Ordenamiento
```python
# Ordenar por columna
df.sort_values('edad')                    # Ascendente
df.sort_values('edad', ascending=False)   # Descendente

# Ordenar por múltiples columnas
df.sort_values(['ciudad', 'edad'], ascending=[True, False])

# Ordenar índice
df.sort_index()
```

### Limpieza de Datos

#### Valores Nulos
```python
# Detectar nulls
df.isnull()                 # DataFrame de booleanos
df.isnull().sum()           # Cuenta por columna
df.isna()                   # Alias de isnull()

# Eliminar nulls
df.dropna()                 # Eliminar filas con cualquier null
df.dropna(subset=['edad'])  # Eliminar si 'edad' es null
df.dropna(axis=1)           # Eliminar columnas con nulls

# Rellenar nulls
df.fillna(0)                        # Con valor fijo
df.fillna({'edad': 0, 'ciudad': 'N/A'})  # Por columna
df.fillna(method='ffill')           # Forward fill
df.fillna(method='bfill')           # Backward fill
df['edad'].fillna(df['edad'].mean())  # Con media
```

#### Duplicados
```python
# Detectar duplicados
df.duplicated()                     # Boolean Series
df.duplicated().sum()               # Cantidad
df[df.duplicated()]                 # Ver duplicados

# Eliminar duplicados
df.drop_duplicates()                # Eliminar todas
df.drop_duplicates(subset=['nombre'])  # Por columna
df.drop_duplicates(keep='first')    # Mantener primera ocurrencia
df.drop_duplicates(keep='last')     # Mantener última
```

### Type Conversion
```python
# Convertir tipo
df['edad'] = df['edad'].astype(int)
df['precio'] = df['precio'].astype(float)
df['fecha'] = pd.to_datetime(df['fecha'])

# Categorías (ahorro de memoria)
df['ciudad'] = df['ciudad'].astype('category')
```

## 📊 Aggregation and Grouping

### Basic Statistics
```python
# Por columna
df['edad'].mean()       # Media
df['edad'].median()     # Mediana
df['edad'].std()        # Desviación estándar
df['edad'].min()        # Mínimo
df['edad'].max()        # Máximo
df['edad'].sum()        # Suma
df['edad'].count()      # Conteo (no-null)

# Percentiles
df['edad'].quantile(0.25)   # Q1
df['edad'].quantile(0.75)   # Q3
```

### GroupBy (Agrupar)
```python
# Agrupar y agregar
df.groupby('ciudad')['edad'].mean()
df.groupby('ciudad')['edad'].sum()

# Múltiples agregaciones
df.groupby('ciudad')['edad'].agg(['mean', 'min', 'max', 'count'])

# Agrupar por múltiples columnas
df.groupby(['ciudad', 'genero'])['edad'].mean()

# Agregar con nombres personalizados
df.groupby('ciudad').agg(
    edad_promedio=('edad', 'mean'),
    edad_max=('edad', 'max'),
    total_personas=('nombre', 'count')
)

# Reset index después de groupby
df.groupby('ciudad')['edad'].mean().reset_index()
```

### Pivot Tables
```python
# Tabla pivote básica
pd.pivot_table(
    df,
    values='edad',
    index='ciudad',
    columns='genero',
    aggfunc='mean'
)

# Con múltiples agregaciones
pd.pivot_table(
    df,
    values='edad',
    index='ciudad',
    aggfunc=['mean', 'count']
)
```

## 🔗 Combination of DataFrames

### Concat (Concatenar)
```python
# Concatenar verticalmente (apilar)
df_total = pd.concat([df1, df2], ignore_index=True)

# Concatenar horizontalmente
df_total = pd.concat([df1, df2], axis=1)
```

### Merge (Join)
```python
# Inner join (solo coincidencias)
pd.merge(df1, df2, on='id', how='inner')

# Left join (todas de df1)
pd.merge(df1, df2, on='id', how='left')

# Right join (todas de df2)
pd.merge(df1, df2, on='id', how='right')

# Outer join (todas)
pd.merge(df1, df2, on='id', how='outer')

# Join con diferentes nombres de columna
pd.merge(df1, df2, left_on='customer_id', right_on='id')

# Join con múltiples columnas
pd.merge(df1, df2, on=['id', 'fecha'])

# Sufijos para columnas duplicadas
pd.merge(df1, df2, on='id', suffixes=('_left', '_right'))
```

## 📅 Manejo de Fechas

### Crear y Convertir
```python
# Convertir a datetime
df['fecha'] = pd.to_datetime(df['fecha'])
df['fecha'] = pd.to_datetime(df['fecha'], format='%Y-%m-%d')

# Crear columna de fecha
df['fecha'] = pd.date_range('2024-01-01', periods=100, freq='D')
```

### Extraer Componentes
```python
df['año'] = df['fecha'].dt.year
df['mes'] = df['fecha'].dt.month
df['dia'] = df['fecha'].dt.day
df['dia_semana'] = df['fecha'].dt.dayofweek  # 0=Lunes
df['nombre_dia'] = df['fecha'].dt.day_name()
df['trimestre'] = df['fecha'].dt.quarter
```

### Operaciones con Fechas
```python
# Diferencia de fechas
df['dias_transcurridos'] = (df['fecha_fin'] - df['fecha_inicio']).dt.days

# Filtrar por rango
df[df['fecha'].between('2024-01-01', '2024-12-31')]

# Resample (reagrupar por tiempo)
df.set_index('fecha').resample('M').sum()  # Por mes
df.set_index('fecha').resample('W').mean()  # Por semana
```

## 💾 Guardar Datos

### Exportar
```python
# CSV
df.to_csv('datos.csv', index=False)
df.to_csv('datos.csv', sep=';', encoding='utf-8', index=False)

# JSON
df.to_json('datos.json', orient='records')

# Parquet
df.to_parquet('datos.parquet', compression='gzip')

# Excel
df.to_excel('datos.xlsx', sheet_name='Hoja1', index=False)
```

## ⚡ Optimization and Performance

### Memory Optimization
```python
# Ver uso de memoria
df.memory_usage(deep=True)

# Optimizar tipos numéricos
df['id'] = df['id'].astype('int32')  # En lugar de int64

# Usar categorías para strings repetitivos
df['ciudad'] = df['ciudad'].astype('category')

# Leer solo columnas necesarias
df = pd.read_csv('datos.csv', usecols=['nombre', 'edad'])

# Leer en chunks para archivos grandes
for chunk in pd.read_csv('datos.csv', chunksize=10000):
    process(chunk)
```

## ⚠️ Errores Comunes

### 1. SettingWithCopyWarning
```python
# ❌ Incorrecto
subset = df[df['edad'] > 25]
subset['nueva_col'] = 0  # Warning!

# ✅ Correcto
subset = df[df['edad'] > 25].copy()
subset['nueva_col'] = 0
```

### 2. Modify During Iteration
```python
# ❌ Lento e ineficiente
for i in range(len(df)):
    df.loc[i, 'nueva'] = df.loc[i, 'edad'] * 2

# ✅ Vectorizado
df['nueva'] = df['edad'] * 2
```

### 3. Olvidar inplace
```python
# ❌ No modifica df
df.dropna()

# ✅ Modifica df
df.dropna(inplace=True)

# ✅ O reasignar
df = df.dropna()
```

## 💡 Tips and Best Practices

1. **Operaciones vectorizadas**: Usar operaciones de Pandas en lugar de loops
2. **Chaining**: Chain operations for cleaner code
3. **copy()**: Usar cuando necesites trabajar con un subset independiente
4. **query()**: For more readable complex filters:`df.query('edad > 25 and ciudad == "Madrid"')`
5. **eval()**: For fast arithmetic operations:`df.eval('total = precio * cantidad')`
6. **Categories**: For columns with repeated values ​​(saves memory)
7. **reset_index()**: After operations that modify the index
8. **inplace=True**: Modifica el DataFrame original (ahorra memoria)

---

**Next**: See [data-cleaning.md](data-cleaning.md) for advanced cleaning techniques
