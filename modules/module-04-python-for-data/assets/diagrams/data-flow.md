# 🔄 Data Flow - Flujos de Datos y Pipelines ETL

## 📊 pipeline ETL Completo

```mermaid
flowchart TD
    A[📥 Fuentes de Datos] --> B[Extract]
    B --> C{Validación Inicial}
    C -->|✅ Válido| D[Transform]
    C -->|❌ Inválido| E[Error Log]
    E --> F[Notificación]
    
    D --> G[Limpieza]
    G --> H[Normalización]
    H --> I[Enriquecimiento]
    I --> J{Validación Calidad}
    
    J -->|✅ Pasa QA| K[Load]
    J -->|❌ Falla QA| L[Cuarentena]
    L --> M[Revisión Manual]
    M --> D
    
    K --> N[Data Warehouse]
    K --> O[Data Lake]
    K --> P[Analytics]
    
    style A fill:#e1f5ff
    style D fill:#fff4e1
    style K fill:#e8f5e9
    style E fill:#ffebee
    style L fill:#fff3e0
```

## 🎯 Module pipeline (Exercises 01-06)

```mermaid
flowchart LR
    A[Ejercicio 01<br/>Python Basics] --> B[Ejercicio 02<br/>Data Structures]
    B --> C[Ejercicio 03<br/>File Operations]
    C --> D[Ejercicio 04<br/>Pandas Fundamentals]
    D --> E[Ejercicio 05<br/>Data Transformation]
    E --> F[Ejercicio 06<br/>Error Handling]
    
    C --> G[(Raw Data<br/>CSV/JSON)]
    G --> D
    D --> H[(Clean Data<br/>DataFrame)]
    H --> E
    E --> I[(Transformed<br/>Parquet)]
    I --> F
    F --> J[(Production<br/>Ready Data)]
    
    style A fill:#e3f2fd
    style B fill:#e3f2fd
    style C fill:#fff9c4
    style D fill:#fff9c4
    style E fill:#f1f8e9
    style F fill:#f1f8e9
    style G fill:#ffebee
    style H fill:#fff3e0
    style I fill:#e8f5e9
    style J fill:#c8e6c9
```

## 📁 Flujo de Archivos

### De Archivos Crudos a Datos Procesados

```mermaid
flowchart TD
    A[📁 customers.csv<br/>10K registros] --> B[🔍 Pandas read_csv]
    C[📁 transactions.csv<br/>100K registros] --> B
    D[📁 products.csv<br/>500 registros] --> B
    E[📁 orders.json<br/>50K registros] --> F[🔍 Pandas read_json]
    G[📁 user_activity.json<br/>20K registros] --> F
    
    B --> H{Explorar<br/>df.info<br/>df.describe}
    F --> H
    
    H --> I[🧹 Limpieza]
    I --> J[Eliminar Nulls]
    I --> K[Eliminar Duplicados]
    I --> L[Corregir Tipos]
    
    J --> M[🔄 Transformación]
    K --> M
    L --> M
    
    M --> N[Normalizar Strings]
    M --> O[Crear Columnas]
    M --> P[Filtrar Datos]
    
    N --> Q[🔗 Combinación]
    O --> Q
    P --> Q
    
    Q --> R[Merge Customers<br/>+ Transactions]
    Q --> S[Join Products]
    
    R --> T[📊 Agregación]
    S --> T
    
    T --> U[GroupBy]
    T --> V[Pivot Tables]
    
    U --> W[💾 Almacenamiento]
    V --> W
    
    W --> X[📁 output.csv]
    W --> Y[📁 output.parquet]
    W --> Z[📁 output.json]
    
    style A fill:#ffebee
    style C fill:#ffebee
    style D fill:#ffebee
    style E fill:#ffebee
    style G fill:#ffebee
    style I fill:#fff9c4
    style M fill:#fff3e0
    style Q fill:#e1f5fe
    style T fill:#f3e5f5
    style W fill:#e8f5e9
    style X fill:#c8e6c9
    style Y fill:#c8e6c9
    style Z fill:#c8e6c9
```

## 🔄 Detailed Transformation pipeline

### Extract → Transform → Load (ETL)

```mermaid
flowchart TB
    subgraph EXTRACT[" 🔍 EXTRACT - Extracción"]
        A1[CSV Files] --> A2[Read CSV]
        A3[JSON Files] --> A4[Read JSON]
        A5[API Endpoints] --> A6[HTTP Request]
        A7[Databases] --> A8[SQL Query]
    end
    
    subgraph VALIDATE[" ✅ VALIDATE - Validación"]
        V1[Schema Check]
        V2[Data Types]
        V3[Required Fields]
        V4[Business Rules]
    end
    
    subgraph TRANSFORM[" 🔄 TRANSFORM - Transformación"]
        subgraph CLEAN[" 🧹 Limpieza"]
            T1[Handle Nulls]
            T2[Remove Duplicates]
            T3[Fix Data Types]
            T4[Normalize Strings]
        end
        
        subgraph ENRICH[" 🎨 Enriquecimiento"]
            T5[Create Columns]
            T6[Apply Functions]
            T7[Categorize]
            T8[Aggregate]
        end
        
        subgraph JOIN[" 🔗 Combinación"]
            T9[Merge Datasets]
            T10[Lookup Values]
            T11[Flatten JSON]
        end
    end
    
    subgraph QUALITY[" 🎯 QUALITY - Calidad"]
        Q1[Data Quality Report]
        Q2[Null Percentage]
        Q3[Duplicate Check]
        Q4[Outlier Detection]
    end
    
    subgraph LOAD[" 💾 LOAD - Carga"]
        L1[Data Warehouse]
        L2[Data Lake]
        L3[Analytics DB]
        L4[Cache/Redis]
    end
    
    EXTRACT --> VALIDATE
    VALIDATE -->|✅ Pass| TRANSFORM
    VALIDATE -->|❌ Fail| ERROR[Error Handler]
    
    TRANSFORM --> CLEAN
    CLEAN --> ENRICH
    ENRICH --> JOIN
    
    JOIN --> QUALITY
    QUALITY -->|✅ Pass| LOAD
    QUALITY -->|❌ Fail| QUARANTINE[Cuarentena]
    
    ERROR --> NOTIFY[Notificación]
    QUARANTINE --> REVIEW[Revisión Manual]
    
    style EXTRACT fill:#e3f2fd
    style VALIDATE fill:#fff9c4
    style TRANSFORM fill:#fff3e0
    style CLEAN fill:#ffecb3
    style ENRICH fill:#ffecb3
    style JOIN fill:#ffecb3
    style QUALITY fill:#f3e5f5
    style LOAD fill:#e8f5e9
    style ERROR fill:#ffcdd2
    style QUARANTINE fill:#ffe0b2
```

## 📊 Flujo de Procesamiento Batch

```mermaid
flowchart TD
    A[⏰ Scheduler<br/>Airflow/Cron] --> B{Trigger}
    B --> C[Check Data Availability]
    
    C -->|✅ Ready| D[Start Pipeline]
    C -->|❌ Not Ready| E[Wait/Retry]
    E --> C
    
    D --> F[Extract Phase]
    F --> G[Transform Phase]
    G --> H[Load Phase]
    
    H --> I{Success?}
    I -->|✅ Yes| J[Update Metadata]
    I -->|❌ No| K[Rollback]
    
    J --> L[Data Quality Report]
    L --> M[Send Notification]
    
    K --> N[Log Error]
    N --> M
    
    M --> O[End]
    
    style A fill:#e1f5fe
    style D fill:#fff9c4
    style F fill:#fff3e0
    style G fill:#ffe0b2
    style H fill:#c8e6c9
    style I fill:#f3e5f5
    style J fill:#c8e6c9
    style K fill:#ffcdd2
```

## 🎭 Procesamiento con Checkpoints

```mermaid
flowchart LR
    A[📥 Input Data] --> B[Checkpoint 1<br/>Raw Data]
    B --> C[Cleaning]
    C --> D[Checkpoint 2<br/>Clean Data]
    D --> E[Transformation]
    E --> F[Checkpoint 3<br/>Transformed]
    F --> G[Validation]
    G --> H{Valid?}
    H -->|✅ Yes| I[Checkpoint 4<br/>Validated]
    H -->|❌ No| J[Restore CP3]
    J --> E
    I --> K[Load]
    K --> L[Checkpoint 5<br/>Final]
    
    style B fill:#e3f2fd
    style D fill:#fff9c4
    style F fill:#fff3e0
    style I fill:#e8f5e9
    style L fill:#c8e6c9
    style J fill:#ffcdd2
```

## 🔁 pipeline con Error Handling

```mermaid
flowchart TD
    A[Start Pipeline] --> B[Read Data]
    B --> C{File Exists?}
    
    C -->|✅ Yes| D[Parse Data]
    C -->|❌ No| E1[FileNotFoundError]
    E1 --> F1[Log Error]
    F1 --> G1[Notify Team]
    G1 --> END1[Fail Gracefully]
    
    D --> E{Valid Format?}
    E -->|✅ Yes| F[Process Data]
    E -->|❌ No| E2[ValueError]
    E2 --> F2[Log Error]
    F2 --> G2[Save to Quarantine]
    G2 --> END2[Partial Success]
    
    F --> G{Transform OK?}
    G -->|✅ Yes| H[Write Output]
    G -->|❌ No| E3[TransformError]
    E3 --> F3[Log Error]
    F3 --> G3[Rollback Changes]
    G3 --> END3[Fail Safe]
    
    H --> I{Write Success?}
    I -->|✅ Yes| J[Update Stats]
    I -->|❌ No| E4[IOError]
    E4 --> F4[Log Error]
    F4 --> G4[Retry Write]
    
    J --> K[Success]
    G4 --> I
    
    style A fill:#e3f2fd
    style F fill:#fff3e0
    style H fill:#ffe0b2
    style K fill:#c8e6c9
    style E1 fill:#ffcdd2
    style E2 fill:#ffcdd2
    style E3 fill:#ffcdd2
    style E4 fill:#ffcdd2
    style G2 fill:#ffe0b2
```

## 📈 Aggregation Flow

```mermaid
flowchart TD
    A[📊 DataFrame] --> B{Tipo de<br/>Agregación}
    
    B -->|Simple| C[df.sum]
    B -->|Simple| D[df.mean]
    B -->|Simple| E[df.count]
    
    B -->|Agrupada| F[GroupBy]
    F --> G[df.groupby col]
    G --> H{Operación}
    H --> I[.agg funcs]
    H --> J[.apply custom]
    
    B -->|Pivot| K[Pivot Table]
    K --> L[pd.pivot_table]
    L --> M[index + columns]
    
    B -->|Ventana| N[Rolling Window]
    N --> O[df.rolling]
    O --> P[window size]
    
    C --> Q[📈 Resultado]
    D --> Q
    E --> Q
    I --> Q
    J --> Q
    M --> Q
    P --> Q
    
    style A fill:#e3f2fd
    style F fill:#fff9c4
    style K fill:#fff3e0
    style N fill:#f3e5f5
    style Q fill:#c8e6c9
```

## 💡 Best Practices

### 1. Separation of Responsibilities
```python
def extract(source):
    """Solo extracción"""
    return pd.read_csv(source)

def transform(df):
    """Solo transformación"""
    df = df.dropna()
    df = df.drop_duplicates()
    return df

def load(df, destination):
    """Solo carga"""
    df.to_parquet(destination)

# Pipeline claro
df = extract('input.csv')
df = transform(df)
load(df, 'output.parquet')
```

### 2. Checkpoints
```python
def pipeline_with_checkpoints(input_file):
    # Checkpoint 1: Raw
    df = pd.read_csv(input_file)
    df.to_parquet('checkpoints/01_raw.parquet')
    
    # Checkpoint 2: Clean
    df = clean(df)
    df.to_parquet('checkpoints/02_clean.parquet')
    
    # Checkpoint 3: Transformed
    df = transform(df)
    df.to_parquet('checkpoints/03_transformed.parquet')
    
    return df
```

### 3. Logging
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_data(df):
    logger.info(f"Processing {len(df)} records")
    
    initial_count = len(df)
    df = df.dropna()
    logger.info(f"Removed {initial_count - len(df)} null rows")
    
    return df
```

### 4. Validation at Every Step
```python
def validate_and_transform(df):
    # Validar antes
    assert len(df) > 0, "DataFrame vacío"
    assert 'id' in df.columns, "Columna 'id' faltante"
    
    # Transformar
    df = transform(df)
    
    # Validar después
    assert df['id'].nunique() == len(df), "IDs duplicados"
    assert df['precio'].min() >= 0, "Precios negativos"
    
    return df
```

---

**Siguiente**: Ver [pandas-operations.md](pandas-operations.md) para operaciones detalladas
