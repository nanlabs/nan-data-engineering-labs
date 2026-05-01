# 🧹 Data Cleaning - Data Cleaning and Validation

## 📋 Typical Cleaning pipeline

```python
def clean_data(df):
    """Pipeline completo de limpieza"""
    df = df.copy()
    
    # 1. Eliminar duplicados
    df = df.drop_duplicates()
    
    # 2. Manejar valores nulos
    df = handle_missing_values(df)
    
    # 3. Corregir tipos de datos
    df = fix_data_types(df)
    
    # 4. Normalizar strings
    df = normalize_strings(df)
    
    # 5. Validar rangos
    df = validate_ranges(df)
    
    # 6. Remover outliers
    df = remove_outliers(df)
    
    return df
```

## 🔍 Problem Detection

### Initial Analysis
```python
def data_quality_report(df):
    """Reporte completo de calidad de datos"""
    print("=" * 50)
    print("DATA QUALITY REPORT")
    print("=" * 50)
    
    # Información general
    print(f"\n📊 General Info:")
    print(f"   Total filas: {len(df):,}")
    print(f"   Total columnas: {len(df.columns)}")
    print(f"   Memoria: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    
    # Valores nulos
    print(f"\n🔍 Missing Values:")
    nulls = df.isnull().sum()
    nulls_pct = (nulls / len(df) * 100).round(2)
    for col in df.columns:
        if nulls[col] > 0:
            print(f"   {col}: {nulls[col]:,} ({nulls_pct[col]}%)")
    
    # Duplicados
    duplicates = df.duplicated().sum()
    print(f"\n🔄 Duplicates: {duplicates:,} ({duplicates/len(df)*100:.2f}%)")
    
    # Tipos de datos
    print(f"\n📝 Data Types:")
    for dtype, cols in df.dtypes.groupby(df.dtypes).items():
        print(f"   {dtype}: {len(cols)} columnas")
    
    # Valores únicos
    print(f"\n🎯 Unique Values:")
    for col in df.columns:
        unique = df[col].nunique()
        if unique < 20:  # Solo mostrar si hay pocos únicos
            print(f"   {col}: {unique} únicos")
    
    return {
        'total_rows': len(df),
        'null_percentage': (df.isnull().sum().sum() / df.size * 100),
        'duplicate_percentage': (duplicates / len(df) * 100)
    }
```

### Identificar Outliers
```python
def detect_outliers_iqr(df, column):
    """Detectar outliers usando método IQR"""
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    outliers = df[
        (df[column] < lower_bound) | 
        (df[column] > upper_bound)
    ]
    
    print(f"Outliers en {column}:")
    print(f"  Rango válido: [{lower_bound:.2f}, {upper_bound:.2f}]")
    print(f"  Outliers encontrados: {len(outliers)}")
    
    return outliers

def detect_outliers_zscore(df, column, threshold=3):
    """Detectar outliers usando Z-score"""
    from scipy import stats
    
    z_scores = np.abs(stats.zscore(df[column]))
    outliers = df[z_scores > threshold]
    
    print(f"Outliers en {column} (Z-score > {threshold}):")
    print(f"  Outliers encontrados: {len(outliers)}")
    
    return outliers
```

## 🛠️ Manejo de Valores Nulos

### Imputation Strategies

#### 1. Elimination
```python
# Eliminar filas con cualquier null
df_clean = df.dropna()

# Eliminar solo si columnas críticas tienen null
df_clean = df.dropna(subset=['customer_id', 'transaction_date'])

# Eliminar si más del 50% de la fila es null
threshold = len(df.columns) * 0.5
df_clean = df.dropna(thresh=threshold)

# Eliminar columnas con muchos nulls
null_pct = df.isnull().sum() / len(df)
cols_to_keep = null_pct[null_pct < 0.5].index
df_clean = df[cols_to_keep]
```

#### 2. Numerical Imputation
```python
# Media (sensible a outliers)
df['edad'].fillna(df['edad'].mean(), inplace=True)

# Mediana (robusta a outliers)
df['salario'].fillna(df['salario'].median(), inplace=True)

# Moda (más común)
df['ciudad'].fillna(df['ciudad'].mode()[0], inplace=True)

# Valor fijo
df['descuento'].fillna(0, inplace=True)

# Interpolación (datos temporales)
df['temperatura'] = df['temperatura'].interpolate(method='linear')

# Forward/Backward fill
df['precio'] = df['precio'].fillna(method='ffill')  # Propagar hacia adelante
df['precio'] = df['precio'].fillna(method='bfill')  # Propagar hacia atrás
```

#### 3. Imputation by Groups
```python
# Imputar con media del grupo
df['salario'] = df.groupby('departamento')['salario'].transform(
    lambda x: x.fillna(x.mean())
)

# Imputar con mediana del grupo
df['precio'] = df.groupby('categoria')['precio'].transform(
    lambda x: x.fillna(x.median())
)
```

#### 4. Advanced Imputation
```python
from sklearn.impute import SimpleImputer, KNNImputer

# SimpleImputer (sklearn)
imputer = SimpleImputer(strategy='mean')
df[['edad', 'salario']] = imputer.fit_transform(df[['edad', 'salario']])

# KNN Imputer (usa vecinos más cercanos)
imputer = KNNImputer(n_neighbors=5)
df[['edad', 'salario']] = imputer.fit_transform(df[['edad', 'salario']])
```

### Crear Indicadores de Nulls
```python
# Flag para indicar si había null (puede ser importante para ML)
df['edad_was_null'] = df['edad'].isnull().astype(int)
df['edad'].fillna(df['edad'].median(), inplace=True)
```

## 🔄 Manejo de Duplicados

### Intelligent Detection
```python
# Duplicados exactos
duplicates = df[df.duplicated(keep=False)]

# Duplicados por columnas específicas
duplicates = df[df.duplicated(subset=['customer_id', 'fecha'], keep=False)]

# Ver grupos de duplicados
for group_id, group in df.groupby(['customer_id', 'fecha']):
    if len(group) > 1:
        print(f"\nGrupo duplicado: {group_id}")
        print(group)
```

### Strategic Elimination
```python
# Mantener primera ocurrencia
df_clean = df.drop_duplicates(keep='first')

# Mantener última ocurrencia (más reciente)
df_clean = df.drop_duplicates(keep='last')

# Eliminar todas las ocurrencias
df_clean = df.drop_duplicates(keep=False)

# Por columnas específicas, mantener fila con valor max
df_clean = df.sort_values('fecha').drop_duplicates(
    subset=['customer_id'], 
    keep='last'
)
```

### Aggregation instead of Deletion
```python
# Si duplicados son válidos, agregar
df_agg = df.groupby(['customer_id', 'fecha']).agg({
    'monto': 'sum',
    'cantidad': 'sum',
    'transaccion_id': 'count'  # Contar transacciones
}).reset_index()
```

## 🔧 Correction of Data Types

### Conversiones Comunes
```python
# Numéricos
df['edad'] = pd.to_numeric(df['edad'], errors='coerce')  # NaN si falla
df['precio'] = df['precio'].astype(float)

# Fechas
df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
df['fecha'] = pd.to_datetime(df['fecha'], format='%Y-%m-%d')

# Booleanos
df['activo'] = df['activo'].map({'Yes': True, 'No': False})
df['activo'] = df['activo'].astype(bool)

# Categorías (ahorra memoria)
df['ciudad'] = df['ciudad'].astype('category')
df['estado'] = pd.Categorical(df['estado'], categories=['bajo', 'medio', 'alto'], ordered=True)
```

### Cleaning Before Conversion
```python
# Limpiar strings antes de convertir a número
df['precio'] = df['precio'].str.replace('$', '').str.replace(',', '')
df['precio'] = pd.to_numeric(df['precio'], errors='coerce')

# Limpiar espacios
df['nombre'] = df['nombre'].str.strip()

# Normalizar texto
df['email'] = df['email'].str.lower().str.strip()
```

## 📝 String Normalization

### Basic Cleaning
```python
def normalize_strings(df):
    """Normalizar todas las columnas string"""
    df = df.copy()
    
    for col in df.select_dtypes(include=['object']).columns:
        # Eliminar espacios en blanco
        df[col] = df[col].str.strip()
        
        # Minúsculas (opcional, depende del caso)
        if col in ['email', 'username']:
            df[col] = df[col].str.lower()
        
        # Reemplazar múltiples espacios
        df[col] = df[col].str.replace(r'\s+', ' ', regex=True)
        
        # Remover caracteres especiales (si aplica)
        # df[col] = df[col].str.replace(r'[^\w\s]', '', regex=True)
    
    return df
```

### Specific Cases
```python
# Teléfonos (formato uniforme)
df['telefono'] = df['telefono'].str.replace(r'\D', '', regex=True)  # Solo dígitos

# Emails (lowercase, trim)
df['email'] = df['email'].str.lower().str.strip()

# Nombres (Title Case)
df['nombre'] = df['nombre'].str.title()

# Códigos postales (padding con ceros)
df['codigo_postal'] = df['codigo_postal'].astype(str).str.zfill(5)
```

## ✅ Range Validation

### Numerical Validation
```python
def validate_numeric_ranges(df, rules):
    """
    Validar rangos numéricos
    
    rules = {
        'edad': {'min': 0, 'max': 120},
        'precio': {'min': 0, 'max': None},
        'descuento': {'min': 0, 'max': 100}
    }
    """
    issues = []
    
    for col, bounds in rules.items():
        if col not in df.columns:
            continue
        
        # Validar mínimo
        if bounds.get('min') is not None:
            invalid = df[df[col] < bounds['min']]
            if len(invalid) > 0:
                issues.append(f"{col}: {len(invalid)} valores < {bounds['min']}")
        
        # Validar máximo
        if bounds.get('max') is not None:
            invalid = df[df[col] > bounds['max']]
            if len(invalid) > 0:
                issues.append(f"{col}: {len(invalid)} valores > {bounds['max']}")
    
    if issues:
        print("⚠️ Valores fuera de rango:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ Todos los valores dentro de rangos válidos")
    
    return issues

# Corregir valores fuera de rango
def fix_ranges(df, column, min_val=None, max_val=None):
    """Clip valores a rangos válidos"""
    if min_val is not None and max_val is not None:
        df[column] = df[column].clip(min_val, max_val)
    elif min_val is not None:
        df[column] = df[column].clip(lower=min_val)
    elif max_val is not None:
        df[column] = df[column].clip(upper=max_val)
    
    return df
```

### Relationship Validation
```python
def validate_relationships(df):
    """Validar relaciones lógicas entre columnas"""
    issues = []
    
    # Fecha inicio < Fecha fin
    if 'fecha_inicio' in df.columns and 'fecha_fin' in df.columns:
        invalid = df[df['fecha_inicio'] > df['fecha_fin']]
        if len(invalid) > 0:
            issues.append(f"Fecha inicio > Fecha fin: {len(invalid)} casos")
    
    # Precio * Cantidad = Total (con tolerancia)
    if all(c in df.columns for c in ['precio', 'cantidad', 'total']):
        df['total_calculado'] = df['precio'] * df['cantidad']
        tolerance = 0.01
        invalid = df[abs(df['total'] - df['total_calculado']) > tolerance]
        if len(invalid) > 0:
            issues.append(f"Total inconsistente: {len(invalid)} casos")
    
    return issues
```

## 🎯 Remover Outliers

### Removal Methods
```python
def remove_outliers_iqr(df, column):
    """Remover outliers usando IQR"""
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    df_clean = df[
        (df[column] >= lower_bound) & 
        (df[column] <= upper_bound)
    ]
    
    removed = len(df) - len(df_clean)
    print(f"Removidos {removed} outliers de {column}")
    
    return df_clean

def cap_outliers(df, column, lower_percentile=0.01, upper_percentile=0.99):
    """Cap outliers en percentiles (no eliminar, ajustar)"""
    lower_bound = df[column].quantile(lower_percentile)
    upper_bound = df[column].quantile(upper_percentile)
    
    df[column] = df[column].clip(lower=lower_bound, upper=upper_bound)
    
    return df
```

## 💡 pipeline Completo

### Ejemplo Integrado
```python
def comprehensive_cleaning_pipeline(df):
    """Pipeline completo de limpieza"""
    
    print("🔍 Análisis inicial...")
    initial_report = data_quality_report(df)
    
    # 1. Crear copia
    df_clean = df.copy()
    initial_rows = len(df_clean)
    
    # 2. Eliminar duplicados completos
    print("\n🔄 Eliminando duplicados...")
    df_clean = df_clean.drop_duplicates()
    print(f"   Removidas {initial_rows - len(df_clean)} filas duplicadas")
    
    # 3. Normalizar strings
    print("\n📝 Normalizando strings...")
    df_clean = normalize_strings(df_clean)
    
    # 4. Corregir tipos
    print("\n🔧 Corrigiendo tipos de datos...")
    if 'fecha' in df_clean.columns:
        df_clean['fecha'] = pd.to_datetime(df_clean['fecha'], errors='coerce')
    
    numeric_cols = ['edad', 'precio', 'cantidad']
    for col in numeric_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    
    # 5. Manejar nulls
    print("\n🔍 Manejando valores nulos...")
    # Estrategia por columna
    if 'edad' in df_clean.columns:
        df_clean['edad'].fillna(df_clean['edad'].median(), inplace=True)
    if 'ciudad' in df_clean.columns:
        df_clean['ciudad'].fillna('Desconocido', inplace=True)
    
    # 6. Validar rangos
    print("\n✅ Validando rangos...")
    validate_numeric_ranges(df_clean, {
        'edad': {'min': 0, 'max': 120},
        'precio': {'min': 0, 'max': None}
    })
    
    # 7. Remover outliers en columnas numéricas
    print("\n🎯 Removiendo outliers...")
    for col in ['precio', 'cantidad']:
        if col in df_clean.columns:
            before = len(df_clean)
            df_clean = remove_outliers_iqr(df_clean, col)
            print(f"   {col}: {before - len(df_clean)} filas removidas")
    
    # 8. Reporte final
    print("\n📊 Análisis final...")
    final_report = data_quality_report(df_clean)
    
    print(f"\n✨ Limpieza completada:")
    print(f"   Filas iniciales: {initial_rows:,}")
    print(f"   Filas finales: {len(df_clean):,}")
    print(f"   Filas removidas: {initial_rows - len(df_clean):,} ({(1 - len(df_clean)/initial_rows)*100:.1f}%)")
    
    return df_clean, initial_report, final_report
```

## ⚠️ Best Practices

1. **Siempre trabaja con copias**: `df_clean = df.copy()`
2. **Documents decisions**: Why did you impute with mean vs median
3. **Validates after cleaning**: Run quality reports
4. **Preserve original data**: Save raw version before cleaning
5. **Automate but review**: The scripts detect, you decide
6. **Consider the context**: A null in "discount" can be 0, but in "email" it is critical
7. **Logging**: Records what was changed and why

---

**Siguiente**: Ver [file-formats.md](file-formats.md) para estrategias de storage
