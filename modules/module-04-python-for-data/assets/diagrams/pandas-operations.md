# 🐼 Pandas Operations - Operaciones Visualizadas

## 📊 Anatomy of a DataFrame

```mermaid
flowchart LR
    A[DataFrame] --> B[Index<br/>Filas]
    A --> C[Columns<br/>Nombres]
    A --> D[Values<br/>Datos]
    A --> E[dtypes<br/>Tipos]
    
    B --> F["0, 1, 2, ..."]
    C --> G["col1, col2, ..."]
    D --> H["2D Array"]
    E --> I["int64, object, ..."]
    
    style A fill:#e3f2fd
    style B fill:#fff9c4
    style C fill:#fff3e0
    style D fill:#f3e5f5
    style E fill:#e8f5e9
```

## 🎯 Data Selection

### loc vs iloc

```mermaid
flowchart TD
    A[Selección de Datos] --> B{Método}
    
    B -->|loc| C[Por Etiquetas]
    C --> D["df.loc[0]<br/>df.loc[0:5]"]
    C --> E["df.loc[df['edad'] > 25]"]
    C --> F["df.loc[:, ['col1', 'col2']]"]
    
    B -->|iloc| G[Por Posición]
    G --> H["df.iloc[0]<br/>df.iloc[0:5]"]
    G --> I["df.iloc[[0, 2, 4]]"]
    G --> J["df.iloc[:, [0, 2]]"]
    
    B -->|Boolean| K[Máscaras]
    K --> L["df[df['edad'] > 25]"]
    K --> M["df[df['ciudad'] == 'Madrid']"]
    
    style A fill:#e3f2fd
    style C fill:#fff9c4
    style G fill:#fff3e0
    style K fill:#f3e5f5
```

## 🔄 Transformation pipeline

```mermaid
flowchart LR
    A[📊 DataFrame<br/>Original] --> B[Filtrar]
    B --> C[Seleccionar<br/>Columnas]
    C --> D[Transformar<br/>Valores]
    D --> E[Crear<br/>Columnas]
    E --> F[Ordenar]
    F --> G[📊 DataFrame<br/>Final]
    
    B -.-> B1["df[df['edad'] > 25]"]
    C -.-> C1["df[['nombre', 'edad']]"]
    D -.-> D1["df['nombre'].upper()"]
    E -.-> E1["df['total'] = df['precio'] * df['qty']"]
    F -.-> F1["df.sort_values('edad')"]
    
    style A fill:#ffebee
    style B fill:#fff9c4
    style C fill:#fff3e0
    style D fill:#e1f5fe
    style E fill:#f3e5f5
    style F fill:#ffe0b2
    style G fill:#c8e6c9
```

## 🔗 Tipos de Joins

### Inner Join
```mermaid
flowchart TD
    A[DataFrame 1<br/>ID: 1,2,3] --> C[Inner Join]
    B[DataFrame 2<br/>ID: 2,3,4] --> C
    C --> D[Resultado<br/>ID: 2,3]
    
    style C fill:#e8f5e9
    style D fill:#c8e6c9
```

### Left Join
```mermaid
flowchart TD
    A[DataFrame 1<br/>ID: 1,2,3] --> C[Left Join]
    B[DataFrame 2<br/>ID: 2,3,4] --> C
    C --> D[Resultado<br/>ID: 1,2,3<br/>4 con NaN]
    
    style C fill:#e3f2fd
    style D fill:#bbdefb
```

### Right Join
```mermaid
flowchart TD
    A[DataFrame 1<br/>ID: 1,2,3] --> C[Right Join]
    B[DataFrame 2<br/>ID: 2,3,4] --> C
    C --> D[Resultado<br/>ID: 2,3,4<br/>1 con NaN]
    
    style C fill:#fff9c4
    style D fill:#fff59d
```

### Outer Join
```mermaid
flowchart TD
    A[DataFrame 1<br/>ID: 1,2,3] --> C[Outer Join]
    B[DataFrame 2<br/>ID: 2,3,4] --> C
    C --> D[Resultado<br/>ID: 1,2,3,4<br/>NaN donde no match]
    
    style C fill:#f3e5f5
    style D fill:#e1bee7
```

## 📊 GroupBy Operations

```mermaid
flowchart TD
    A[📊 DataFrame] --> B[GroupBy Column]
    B --> C{Operación}
    
    C --> D[Agregación]
    D --> E[sum]
    D --> F[mean]
    D --> G[count]
    D --> H[min/max]
    
    C --> I[Transformación]
    I --> J[standardize]
    I --> K[normalize]
    
    C --> L[Filtrado]
    L --> M[filter groups]
    
    C --> N[Aplicar Función]
    N --> O[apply custom]
    
    E --> P[📈 Resultado]
    F --> P
    G --> P
    H --> P
    J --> P
    K --> P
    M --> P
    O --> P
    
    style A fill:#e3f2fd
    style B fill:#fff9c4
    style D fill:#fff3e0
    style I fill:#f3e5f5
    style L fill:#e8f5e9
    style N fill:#ffe0b2
    style P fill:#c8e6c9
```

### GroupBy Visual Example

```mermaid
flowchart LR
    subgraph INPUT[" DataFrame Original"]
        A1[Ciudad: Madrid<br/>Ventas: 100]
        A2[Ciudad: Madrid<br/>Ventas: 200]
        A3[Ciudad: BCN<br/>Ventas: 150]
        A4[Ciudad: BCN<br/>Ventas: 250]
    end
    
    INPUT --> GB[GroupBy Ciudad]
    
    GB --> G1[Grupo Madrid]
    GB --> G2[Grupo BCN]
    
    G1 --> C1[Ventas: 100, 200]
    G2 --> C2[Ventas: 150, 250]
    
    C1 --> R1[Sum: 300]
    C2 --> R2[Sum: 400]
    
    subgraph OUTPUT[" Resultado"]
        R1
        R2
    end
    
    style INPUT fill:#ffebee
    style GB fill:#fff9c4
    style G1 fill:#e3f2fd
    style G2 fill:#e3f2fd
    style OUTPUT fill:#c8e6c9
```

## 🧹 pipeline de Limpieza

```mermaid
flowchart TD
    A[📊 Raw Data<br/>Con errores] --> B{Detectar<br/>Problemas}
    
    B --> C[Nulls<br/>Encontrados]
    B --> D[Duplicados<br/>Encontrados]
    B --> E[Outliers<br/>Encontrados]
    B --> F[Tipos<br/>Incorrectos]
    
    C --> C1{Estrategia}
    C1 --> C2[Eliminar]
    C1 --> C3[Imputar Media]
    C1 --> C4[Imputar Mediana]
    C1 --> C5[Forward Fill]
    
    D --> D1[Drop Duplicates]
    D1 --> D2[Keep: first/last]
    
    E --> E1{Método}
    E1 --> E2[IQR]
    E1 --> E3[Z-Score]
    E1 --> E4[Cap Values]
    
    F --> F1[Convertir Tipos]
    F1 --> F2[to_numeric]
    F1 --> F3[to_datetime]
    
    C2 --> G[📊 Clean Data]
    C3 --> G
    C4 --> G
    C5 --> G
    D2 --> G
    E2 --> G
    E3 --> G
    E4 --> G
    F2 --> G
    F3 --> G
    
    style A fill:#ffebee
    style B fill:#fff9c4
    style C fill:#ffcdd2
    style D fill:#ffcdd2
    style E fill:#ffcdd2
    style F fill:#ffcdd2
    style G fill:#c8e6c9
```

## 📈 Multi-Level Aggregation

```mermaid
flowchart TD
    A[📊 Sales Data] --> B[GroupBy]
    B --> C[Nivel 1: País]
    C --> D[Nivel 2: Ciudad]
    D --> E[Nivel 3: Tienda]
    
    E --> F{Métricas}
    F --> G[Total Ventas<br/>sum]
    F --> H[Promedio<br/>mean]
    F --> I[Transacciones<br/>count]
    F --> J[Productos Únicos<br/>nunique]
    
    G --> K[📊 Multi-Index<br/>DataFrame]
    H --> K
    I --> K
    J --> K
    
    K --> L{Output}
    L --> M[Tabla Pivote]
    L --> N[Jerarquía]
    L --> O[Flat Table<br/>reset_index]
    
    style A fill:#e3f2fd
    style B fill:#fff9c4
    style C fill:#fff3e0
    style D fill:#ffe0b2
    style E fill:#ffecb3
    style K fill:#e8f5e9
    style M fill:#c8e6c9
    style N fill:#c8e6c9
    style O fill:#c8e6c9
```

## 🔄 Reshape Operations

### Pivot (Wide Format)
```mermaid
flowchart LR
    subgraph LONG[" Formato Largo"]
        A1[País: USA<br/>Año: 2023<br/>Ventas: 100]
        A2[País: USA<br/>Año: 2024<br/>Ventas: 120]
        A3[País: MX<br/>Año: 2023<br/>Ventas: 80]
        A4[País: MX<br/>Año: 2024<br/>Ventas: 90]
    end
    
    LONG --> P[Pivot]
    P --> WIDE
    
    subgraph WIDE[" Formato Ancho"]
        B1["País | 2023 | 2024"]
        B2["USA  | 100  | 120"]
        B3["MX   | 80   | 90"]
    end
    
    style LONG fill:#fff9c4
    style P fill:#e3f2fd
    style WIDE fill:#c8e6c9
```

### Melt (Long Format)
```mermaid
flowchart LR
    subgraph WIDE2[" Formato Ancho"]
        C1["País | 2023 | 2024"]
        C2["USA  | 100  | 120"]
    end
    
    WIDE2 --> M[Melt]
    M --> LONG2
    
    subgraph LONG2[" Formato Largo"]
        D1[País: USA<br/>Año: 2023<br/>Valor: 100]
        D2[País: USA<br/>Año: 2024<br/>Valor: 120]
    end
    
    style WIDE2 fill:#c8e6c9
    style M fill:#e3f2fd
    style LONG2 fill:#fff9c4
```

## 📊 Window Functions

```mermaid
flowchart TD
    A[📊 Time Series<br/>Data] --> B[Set Index]
    B --> C[DateTime Index]
    
    C --> D{Window Type}
    
    D --> E[Rolling]
    E --> E1[.rolling 7]
    E1 --> E2[Mean/Sum/Std]
    
    D --> F[Expanding]
    F --> F1[.expanding]
    F1 --> F2[Cumulative Stats]
    
    D --> G[EWM]
    G --> G1[.ewm alpha]
    G1 --> G2[Exponential Weight]
    
    E2 --> H[📈 Result]
    F2 --> H
    G2 --> H
    
    H --> I[Nueva Columna<br/>con Stats]
    
    style A fill:#e3f2fd
    style C fill:#fff9c4
    style E fill:#fff3e0
    style F fill:#f3e5f5
    style G fill:#ffe0b2
    style I fill:#c8e6c9
```

## 🎨 Apply, Map, Applymap

```mermaid
flowchart TD
    A[DataFrame/Series] --> B{Método}
    
    B -->|apply| C[Aplicar Función]
    C --> C1{Axis}
    C1 --> C2[axis=0<br/>Por Columna]
    C1 --> C3[axis=1<br/>Por Fila]
    
    B -->|map| D[Mapear Valores]
    D --> D1[Series Only]
    D1 --> D2[Dict Mapping]
    D1 --> D3[Function]
    
    B -->|applymap| E[Elemento a Elemento]
    E --> E1[DataFrame Only]
    E1 --> E2[Cada Celda]
    
    C2 --> F[📊 Resultado]
    C3 --> F
    D2 --> F
    D3 --> F
    E2 --> F
    
    style A fill:#e3f2fd
    style C fill:#fff9c4
    style D fill:#fff3e0
    style E fill:#f3e5f5
    style F fill:#c8e6c9
```

## 🔢 Operaciones Vectorizadas vs Loops

### ❌ Loop (Lento)
```mermaid
flowchart TD
    A[For Loop] --> B[Fila 1]
    B --> C[Procesar]
    C --> D[Fila 2]
    D --> E[Procesar]
    E --> F[Fila 3]
    F --> G[Procesar]
    G --> H[...]
    H --> I[Fila N]
    
    style A fill:#ffcdd2
    style B fill:#ffebee
    style D fill:#ffebee
    style F fill:#ffebee
    style I fill:#ffebee
```

### ✅ Vectorized (Fast)
```mermaid
flowchart LR
    A[Operación<br/>Vectorizada] --> B[Todas las Filas]
    B --> C[Una Operación]
    C --> D[Resultado]
    
    style A fill:#c8e6c9
    style B fill:#e8f5e9
    style C fill:#e8f5e9
    style D fill:#c8e6c9
```

## 🎯 Optimization Strategy

```mermaid
flowchart TD
    A[Operación Lenta] --> B{Diagnóstico}
    
    B --> C[¿Usando Loop?]
    C -->|Sí| D[Vectorizar]
    D --> D1[Operaciones Pandas]
    D --> D2[NumPy Arrays]
    
    B --> E[¿Muchas Columnas?]
    E -->|Sí| F[Seleccionar Solo<br/>Necesarias]
    
    B --> G[¿Tipos Incorrectos?]
    G -->|Sí| H[Optimizar Tipos]
    H --> H1[int64 → int32]
    H --> H2[object → category]
    
    B --> I[¿Operaciones<br/>Repetidas?]
    I -->|Sí| J[Cache Results]
    
    B --> K[¿Archivo Grande?]
    K -->|Sí| L[Chunks/Dask]
    
    D1 --> M[⚡ Optimizado]
    D2 --> M
    F --> M
    H1 --> M
    H2 --> M
    J --> M
    L --> M
    
    style A fill:#ffcdd2
    style D fill:#fff9c4
    style F fill:#fff3e0
    style H fill:#e1f5fe
    style J fill:#f3e5f5
    style L fill:#ffe0b2
    style M fill:#c8e6c9
```

## 💡 Patterns Comunes

### Pattern 1: Filter → Transform → Aggregate
```mermaid
flowchart LR
    A[📊 Data] --> B[Filter<br/>edad > 25]
    B --> C[Transform<br/>categorize]
    C --> D[Aggregate<br/>groupby.sum]
    D --> E[📈 Result]
    
    style A fill:#e3f2fd
    style B fill:#fff9c4
    style C fill:#fff3e0
    style D fill:#f3e5f5
    style E fill:#c8e6c9
```

### Pattern 2: Merge → Enrich → Export
```mermaid
flowchart LR
    A[📊 Data 1] --> C[Merge]
    B[📊 Data 2] --> C
    C --> D[Enrich<br/>new columns]
    D --> E[Export<br/>Parquet]
    
    style A fill:#e3f2fd
    style B fill:#e3f2fd
    style C fill:#fff9c4
    style D fill:#fff3e0
    style E fill:#c8e6c9
```

### Pattern 3: Clean → Validate → Load
```mermaid
flowchart LR
    A[📊 Raw] --> B[Clean<br/>nulls/dups]
    B --> C{Validate}
    C -->|✅ Pass| D[Load<br/>Production]
    C -->|❌ Fail| E[Quarantine]
    E --> F[Review]
    
    style A fill:#ffebee
    style B fill:#fff9c4
    style D fill:#c8e6c9
    style E fill:#ffcdd2
```

## 📊 Performance Comparison

```mermaid
flowchart TD
    A[100K Rows Operation] --> B{Método}
    
    B --> C[Python Loop]
    C --> C1[⏱️ 10 segundos]
    
    B --> D[List Comprehension]
    D --> D1[⏱️ 5 segundos]
    
    B --> E[Pandas Apply]
    E --> E1[⏱️ 2 segundos]
    
    B --> F[Pandas Vectorized]
    F --> F1[⏱️ 0.1 segundos]
    
    B --> G[NumPy Vectorized]
    G --> G1[⏱️ 0.05 segundos]
    
    style C fill:#ffcdd2
    style D fill:#ffe0b2
    style E fill:#fff9c4
    style F fill:#c8e6c9
    style G fill:#a5d6a7
```

## 💡 Tips Visuales

### Memory Optimization
```mermaid
flowchart LR
    A[DataFrame<br/>100 MB] --> B{Optimizar}
    B --> C[category dtype<br/>-50%]
    B --> D[int32 vs int64<br/>-25%]
    B --> E[drop unused cols<br/>-30%]
    
    C --> F[DataFrame<br/>25 MB]
    D --> F
    E --> F
    
    style A fill:#ffcdd2
    style F fill:#c8e6c9
```

---

**Note**: These diagrams are rendered in GitHub, VS Code (with extension), and Mermaid Live Editor.

