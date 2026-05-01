# 📁 File Formats - Data Formats Guide

## 📊 Quick Comparison

| Format | Type | Size | Speed ​​| Scheme | Compression | Typical Use |
|---------|------|--------|-----------|---------|------------|------------|
| **CSV** | Texto | Grande | Lenta | No | Baja | Intercambio simple |
| **JSON** | Texto | Grande | Media | Flexible | Baja | APIs, configs |
| **Parquet** | Binary | Small | Quick | Yes | High | Data lakes, analytics |
| **Avro** | Binary | Medium | Quick | Yes | Medium | Streaming, Kafka |
| **Excel** | Binario | Grande | Lenta | No | Media | Business users |

## 📄 CSV (Comma-Separated Values)

### features
- ✅ **Pros**: Universal, legible, simple, soportado por todo
- ❌ **Cons**: No data types, no compression, slow with large files
- 📦 **Size**: ~100 MB for 1M rows
- 🎯 **When to use**: Simple data exchange, maximum compatibility

### Lectura
```python
import pandas as pd

# Básico
df = pd.read_csv('datos.csv')

# Con opciones
df = pd.read_csv(
    'datos.csv',
    sep=',',                    # Delimitador (';' en Europa)
    encoding='utf-8',           # Encoding (utf-8, latin1)
    header=0,                   # Fila con nombres de columnas
    names=['col1', 'col2'],     # Nombres personalizados
    dtype={'edad': int},        # Tipos de datos explícitos
    parse_dates=['fecha'],      # Parsear como fecha
    na_values=['N/A', 'null'],  # Valores a considerar como null
    thousands=',',              # Separador de miles
    decimal='.',                # Separador decimal
    usecols=['col1', 'col2'],   # Solo leer columnas específicas
    nrows=1000,                 # Leer solo N filas
    skiprows=5,                 # Saltar primeras N filas
    low_memory=False            # Inferir tipos correctamente
)

# Leer en chunks (archivos grandes)
chunk_size = 10000
for chunk in pd.read_csv('datos_grandes.csv', chunksize=chunk_size):
    process(chunk)
```

### Escritura
```python
# Básico
df.to_csv('output.csv', index=False)

# Con opciones
df.to_csv(
    'output.csv',
    index=False,                # No incluir índice
    sep=',',                    # Delimitador
    encoding='utf-8',           # Encoding
    header=True,                # Incluir nombres de columnas
    columns=['col1', 'col2'],   # Solo columnas específicas
    na_rep='NULL',              # Representación de nulls
    float_format='%.2f',        # Formato de floats
    date_format='%Y-%m-%d',     # Formato de fechas
    quoting=csv.QUOTE_NONNUMERIC,  # Entrecomillar non-numeric
    compression='gzip'          # Comprimir (.csv.gz)
)
```

### Problemas Comunes
```python
# 1. Encoding incorrecto
df = pd.read_csv('datos.csv', encoding='latin1')  # Prueba diferentes encodings

# 2. Delimitador incorrecto
df = pd.read_csv('datos.csv', sep=';')  # Europa usa ';'

# 3. Decimal incorrecto
df = pd.read_csv('datos.csv', decimal=',')  # Europa usa ','

# 4. Tipos inferidos mal
df = pd.read_csv('datos.csv', dtype={'codigo': str})  # '001' sería int sin esto
```

## 📋 JSON (JavaScript Object Notation)

### features
- ✅ **Pros**: Nested structure, readable, web standard, flexible schema
- ❌ **Cons**: Verbose, no compression, slower than binaries
- 📦 **Size**: ~150 MB for 1M rows
- 🎯 **When to use**: APIs, configs, hierarchical data

### Types of Guidance

#### 1. Records (Most common)
```json
[
    {"nombre": "Ana", "edad": 25, "ciudad": "Madrid"},
    {"nombre": "Luis", "edad": 30, "ciudad": "Barcelona"}
]
```

```python
# Leer
df = pd.read_json('datos.json', orient='records')

# Escribir
df.to_json('output.json', orient='records', indent=2)
```

#### 2. Columns
```json
{
    "nombre": ["Ana", "Luis"],
    "edad": [25, 30],
    "ciudad": ["Madrid", "Barcelona"]
}
```

```python
df = pd.read_json('datos.json', orient='columns')
df.to_json('output.json', orient='columns')
```

#### 3. Index
```json
{
    "0": {"nombre": "Ana", "edad": 25},
    "1": {"nombre": "Luis", "edad": 30}
}
```

### Lectura
```python
# Básico
df = pd.read_json('datos.json')

# Con opciones
df = pd.read_json(
    'datos.json',
    orient='records',           # Orientación
    typ='frame',                # 'frame' o 'series'
    encoding='utf-8',
    lines=True,                 # JSON Lines (un objeto por línea)
    compression='gzip'
)

# JSON anidado (normalizar)
from pandas import json_normalize

data = [
    {
        "id": 1,
        "nombre": "Ana",
        "direccion": {"ciudad": "Madrid", "pais": "España"}
    }
]

df = json_normalize(data, sep='_')
# Resultado: id, nombre, direccion_ciudad, direccion_pais
```

### Escritura
```python
# Básico
df.to_json('output.json', orient='records', indent=2)

# JSON Lines (eficiente para streaming)
df.to_json('output.jsonl', orient='records', lines=True)

# Con compresión
df.to_json('output.json.gz', orient='records', compression='gzip')
```

### JSON Anidado Complejo
```python
# Cargar JSON complejo
import json

with open('complejo.json', 'r') as f:
    data = json.load(f)

# Normalizar niveles específicos
df = json_normalize(
    data,
    record_path=['orders'],          # Path a los registros
    meta=['customer_id', 'name'],    # Campos del nivel superior
    meta_prefix='customer_',         # Prefijo para campos meta
    sep='_'
)
```

## 🚀 Parquet (Columnar Storage)

### features
- ✅ **Pros**: Excellent compression, very fast, schema included, data types preserved
- ❌ **Cons**: Not human readable, requires special library
- 📦 **Size**: ~15 MB for 1M rows (85% less than CSV!)
- 🎯 **When to use**: Data lakes, analytics, storage of large datasets

### Why Parquet is Superior

#### 1. Compression
```python
# Comparación de tamaño
df.to_csv('datos.csv', index=False)         # 100 MB
df.to_parquet('datos.parquet')              # 15 MB (85% menos!)
```

#### 2. Velocidad
```python
import time

# CSV
start = time.time()
df = pd.read_csv('datos.csv')
print(f"CSV: {time.time() - start:.2f}s")   # ~10s

# Parquet
start = time.time()
df = pd.read_parquet('datos.parquet')
print(f"Parquet: {time.time() - start:.2f}s")  # ~2s (5x más rápido!)
```

#### 3. Type Preservation
```python
# CSV pierde tipos
df.to_csv('datos.csv', index=False)
df_csv = pd.read_csv('datos.csv')
# fecha: object (string), edad: int64 o float64 (ambiguo)

# Parquet preserva tipos exactos
df.to_parquet('datos.parquet')
df_parquet = pd.read_parquet('datos.parquet')
# fecha: datetime64, edad: int32 (exacto)
```

### Lectura
```python
# Básico
df = pd.read_parquet('datos.parquet')

# Con opciones
df = pd.read_parquet(
    'datos.parquet',
    engine='pyarrow',           # 'pyarrow' (rápido) o 'fastparquet'
    columns=['col1', 'col2'],   # Solo leer columnas específicas (eficiente!)
    filters=[('edad', '>', 25)]  # Filtros pushdown (muy eficiente)
)

# Leer desde S3/Cloud
df = pd.read_parquet('s3://bucket/datos.parquet')
```

### Escritura
```python
# Básico
df.to_parquet('output.parquet', index=False)

# Con opciones
df.to_parquet(
    'output.parquet',
    engine='pyarrow',
    compression='snappy',       # 'snappy' (rápido), 'gzip' (más compacto), 'lz4', 'brotli'
    index=False
)

# Particionado (para datasets muy grandes)
df.to_parquet(
    'output.parquet',
    partition_cols=['año', 'mes']  # Crea estructura: año=2024/mes=01/data.parquet
)
```

### Comparative Compression
```python
# Sin compresión
df.to_parquet('sin_comp.parquet', compression=None)      # 50 MB

# Snappy (default, balanceado)
df.to_parquet('snappy.parquet', compression='snappy')    # 15 MB, rápido

# Gzip (máxima compresión)
df.to_parquet('gzip.parquet', compression='gzip')        # 10 MB, más lento

# LZ4 (muy rápido)
df.to_parquet('lz4.parquet', compression='lz4')          # 18 MB, muy rápido
```

## 📊 Excel (XLS/XLSX)

### features
- ✅ **Pros**: Familiar for business users, multiple sheets, visual format
- ❌ **Cons**: Slow, 1M rows limit, not for production
- 📦 **Size**: ~80 MB for 1M rows
- 🎯 **When to use**: Reports for business users

### Lectura
```python
# Básico
df = pd.read_excel('datos.xlsx')

# Con opciones
df = pd.read_excel(
    'datos.xlsx',
    sheet_name='Hoja1',         # Nombre o índice de la hoja
    header=0,                   # Fila con nombres de columnas
    usecols='A:C',              # Columnas específicas (A:C o [0,1,2])
    skiprows=2,                 # Saltar filas
    nrows=100                   # Leer solo N filas
)

# Leer múltiples sheets
sheets = pd.read_excel('datos.xlsx', sheet_name=None)  # Dict de DataFrames
for sheet_name, df in sheets.items():
    print(f"Sheet: {sheet_name}, Filas: {len(df)}")
```

### Escritura
```python
# Básico
df.to_excel('output.xlsx', index=False, sheet_name='Datos')

# Múltiples sheets
with pd.ExcelWriter('output.xlsx', engine='openpyxl') as writer:
    df1.to_excel(writer, sheet_name='Ventas', index=False)
    df2.to_excel(writer, sheet_name='Productos', index=False)
    df3.to_excel(writer, sheet_name='Clientes', index=False)

# Con formato (requiere openpyxl o xlsxwriter)
writer = pd.ExcelWriter('formatted.xlsx', engine='xlsxwriter')
df.to_excel(writer, sheet_name='Datos', index=False)

workbook = writer.book
worksheet = writer.sheets['Datos']
format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BD'})
worksheet.set_row(0, None, format)  # Formatear header

writer.close()
```

## 🔄 Conversion Between Formats

### CSV → Parquet
```python
# Simple
df = pd.read_csv('datos.csv')
df.to_parquet('datos.parquet', index=False)

# En chunks (archivos muy grandes)
writer = None
for chunk in pd.read_csv('datos_grandes.csv', chunksize=100000):
    if writer is None:
        writer = pq.ParquetWriter('datos.parquet', chunk.to_arrow().schema)
    writer.write_table(chunk.to_arrow())
writer.close()
```

### JSON → Parquet
```python
df = pd.read_json('datos.json', orient='records')
df.to_parquet('datos.parquet', index=False)
```

### Parquet → CSV (para reportes)
```python
df = pd.read_parquet('datos.parquet')
df.to_csv('reporte.csv', index=False)
```

## 📐 Decision Guide

### Decision Flow
```
¿Necesitas compatibilidad universal?
├─ SÍ → CSV
└─ NO
    ├─ ¿Datos anidados/jerárquicos?
    │   ├─ SÍ → JSON
    │   └─ NO
    │       ├─ ¿Dataset grande (>1 GB)?
    │       │   ├─ SÍ → PARQUET
    │       │   └─ NO
    │       │       ├─ ¿Para usuario de negocio?
    │       │       │   ├─ SÍ → EXCEL
    │       │       │   └─ NO → CSV o PARQUET
```

### Specific Use Cases

#### 1. Data Engineering pipeline
```python
# Extract: CSV/JSON de fuentes externas
raw_df = pd.read_csv('fuente_externa.csv')

# Transform: Trabajar en memoria
clean_df = transform(raw_df)

# Load: Guardar como Parquet para analytics
clean_df.to_parquet('data_lake/clean_data.parquet', compression='snappy')
```

#### 2. Reporte para Negocio
```python
# Leer desde data warehouse (Parquet)
df = pd.read_parquet('data_warehouse/ventas.parquet')

# Filtrar y agregar
report = df.groupby('region').agg({'ventas': 'sum', 'unidades': 'sum'})

# Exportar a Excel con formato
report.to_excel('reporte_mensual.xlsx', sheet_name='Resumen')
```

#### 3. API Response
```python
# Leer desde almacenamiento eficiente
df = pd.read_parquet('datos.parquet', columns=['id', 'nombre', 'valor'])

# Filtrar
df = df[df['valor'] > 100]

# Retornar como JSON
return df.to_json(orient='records')
```

## 💾 storage en la cloud

### S3 (AWS)
```python
# Leer
df = pd.read_parquet('s3://my-bucket/datos.parquet')
df = pd.read_csv('s3://my-bucket/datos.csv')

# Escribir
df.to_parquet('s3://my-bucket/output.parquet')
```

### Google Cloud Storage
```python
# Leer
df = pd.read_parquet('gs://my-bucket/datos.parquet')

# Escribir
df.to_parquet('gs://my-bucket/output.parquet')
```

## 📊 Benchmark Comparativo

### Dataset: 1 million rows, 10 columns

| Operation | CSV | JSON | Parquet | Excel |
|-----------|-----|------|---------|-------|
| **Size** | 100MB | 150MB | 15MB | 80MB |
| **Escribir** | 10s | 15s | 2s | 45s |
| **Leer** | 8s | 12s | 1.5s | 60s |
| **Leer 2 cols** | 8s | 12s | 0.3s | 55s |
| **Compression** | ❌ | ❌ | ✅ Excellent | ⚠️ Average |
| **Tipos** | ❌ Se pierden | ⚠️ Parcial | ✅ Preserva | ⚠️ Parcial |

## 💡 Best Practices

1. **storage interno**: Usa **Parquet**
2. **Intercambio externo**: Usa **CSV** (universal)
3. **APIs**: Use **JSON** (web standard)
4. **Reportes**: Usa **Excel** (usuarios de negocio)
5. **Datos anidados**: Usa **JSON** o **Parquet**
6. **Archivos grandes**: Usa **Parquet** con particionado
7. **Compression**:
   - Parquet: `snappy` (balanceado)
   - CSV: `.csv.gz` si es necesario
8. **Siempre especifica**: `index=False` al escribir

---

**Siguiente**: Ver [diagramas](../diagrams/) para visualizar flujos de datos

