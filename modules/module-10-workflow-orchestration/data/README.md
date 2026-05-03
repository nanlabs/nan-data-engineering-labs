# Datos de Ejemplo - Module 10

Este directorio contiene datos de ejemplo y schemas para usar en los exercises de Airflow.

## 📁 Estructura

```
data/
├── sample/                    # Datos de ejemplo
│   ├── users.csv             # 10 usuarios de ejemplo
│   ├── sales.csv             # 15 órdenes de ejemplo
│   └── sensor_data.json      # 5 lecturas de sensores
│
└── schemas/                   # Definiciones de schemas
    ├── database_schema.sql   # Schema PostgreSQL
    └── data_schema.json      # Schema JSON con reglas de calidad
```

## 📊 Description de Datasets

### 1. users.csv
**Registros**: 10 usuarios
**Campos**: id, name, email, age, city, registration_date, status

Datos de usuarios para exercises de:
- Carga de CSV a base de datos
- Validation de datos
- ETL básico

**Ejemplo de uso en DAG**:
```python
import pandas as pd

def load_users():
    df = pd.read_csv('data/sample/users.csv')
    # Procesar y cargar a DB
    return len(df)
```

### 2. sales.csv
**Registros**: 15 órdenes
**Campos**: order_id, customer_id, product, category, amount, quantity, order_date, status

Datos de ventas para:
- Pipeline ETL completo
- Agregaciones y transformaciones
- Análisis de series temporales

**Ejemplo de uso**:
```python
import pandas as pd

def analyze_sales():
    df = pd.read_csv('data/sample/sales.csv')

    # Calcular totales por categoría
    category_totals = df.groupby('category')['amount'].sum()

    print(f"Total Electronics: ${category_totals['Electronics']:.2f}")
    print(f"Total Furniture: ${category_totals['Furniture']:.2f}")
```

### 3. sensor_data.json
**Registros**: 5 lecturas
**Campos**: sensor_id, location, temperature, humidity, timestamp, status

Datos de sensores IoT para:
- Procesamiento de JSON
- Detección de anomalías
- Monitoreo de alertas

**Ejemplo de uso**:
```python
import json

def process_sensors():
    with open('data/sample/sensor_data.json', 'r') as f:
        data = json.load(f)

    # Detectar alertas
    warnings = [s for s in data if s['status'] == 'warning']
    print(f"⚠️  {len(warnings)} sensores en estado warning")
```

## 🗄️ Database Schemas

### database_schema.sql

Schema completo para PostgreSQL que incluye:

**Tablas**:
- `users` - Información de usuarios
- `orders` - Órdenes de compra
- `user_stats` - Estadísticas agregadas (para ETL)
- `sensor_readings` - Lecturas de sensores
- `pipeline_logs` - Logs de ejecución de pipelines

**Features**:
- Primary keys y foreign keys
- Constraints de validation (CHECK)
- Índices para performance
- Triggers para `updated_at` automático
- Comentarios y documentación

**Uso**:
```bash
# Crear schema en PostgreSQL
psql -U postgres -d airflow -f data/schemas/database_schema.sql

# O desde DAG con PostgresOperator
create_table = PostgresOperator(
    task_id='create_tables',
    sql='data/schemas/database_schema.sql',
    postgres_conn_id='postgres_default',
)
```

### data_schema.json

Schema JSON con definiciones de datos y reglas de calidad:

**Incluye**:
- Definición de campos (tipo, required, constraints)
- Reglas de calidad de datos
- Validaciones de formato
- Rangos permitidos

**Uso con Pandera**:
```python
import json
import pandera as pa

def validate_with_schema(df, table_name):
    with open('data/schemas/data_schema.json', 'r') as f:
        schemas = json.load(f)

    schema_def = schemas[table_name]

    # Crear schema Pandera dinámicamente
    # ... validation ...
```

## 🚀 Cómo Usar con Airflow

### Opción 1: Referenciar desde DAGs

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
import pandas as pd
import os

def process_csv():
    # Path relativo desde dags/
    data_path = os.path.join(
        os.path.dirname(__file__),
        '../data/sample/users.csv'
    )
    df = pd.read_csv(data_path)
    return len(df)

with DAG('process_users', ...) as dag:
    task = PythonOperator(
        task_id='process',
        python_callable=process_csv,
    )
```

### Opción 2: Copiar a Directorio Temporal

```python
def load_and_process():
    import shutil

    # Copiar a /tmp para procesamiento
    shutil.copy(
        'data/sample/sales.csv',
        '/tmp/sales.csv'
    )

    # Procesar desde /tmp
    df = pd.read_csv('/tmp/sales.csv')
    # ...
```

### Opción 3: Usar con Docker Volumes

Si usas Docker Compose del module, los datos ya están montados:

```yaml
# En docker-compose.yml
volumes:
  - ./data:/opt/airflow/data:ro  # Read-only
```

Acceder desde DAG:
```python
df = pd.read_csv('/opt/airflow/data/sample/users.csv')
```

## 📋 Casos de Uso por Exercise

### Exercise 01: Primer DAG
- ✅ No requiere datos externos

### Exercise 02: Operadores y Sensores
- ✅ `users.csv` para FileSensor
- ✅ `sales.csv` para procesamiento

### Exercise 03: Dependencias
- ✅ `sensor_data.json` para branching basado en status

### Exercise 04: Pipeline ETL
- ✅ API externa (JSONPlaceholder) - no requiere datos locales
- ✅ `database_schema.sql` para create tablas
- ✅ `users.csv` + `sales.csv` para pipeline completo

### Exercise 05: Monitoreo
- ✅ `sales.csv` para métricas de calidad
- ✅ `data_schema.json` para validaciones

### Exercise 06: Producción
- ✅ Todos los datasets para pipeline completo
- ✅ `database_schema.sql` para setup de DB

## 🔧 Generación de Datos

Para generar más datos de ejemplo, puedes usar el siguiente script:

```python
# generate_more_data.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_users(n=100):
    names = ['Ana', 'Carlos', 'María', 'Juan', 'Laura', 'Pedro']
    cities = ['Madrid', 'Barcelona', 'Valencia', 'Sevilla', 'Bilbao']

    data = {
        'id': range(1, n+1),
        'name': np.random.choice(names, n),
        'email': [f'user{i}@example.com' for i in range(1, n+1)],
        'age': np.random.randint(18, 70, n),
        'city': np.random.choice(cities, n),
        'registration_date': [
            (datetime.now() - timedelta(days=np.random.randint(0, 365))).date()
            for _ in range(n)
        ],
        'status': np.random.choice(['active', 'inactive'], n, p=[0.8, 0.2])
    }

    df = pd.DataFrame(data)
    df.to_csv('data/sample/users_extended.csv', index=False)
    print(f"✓ Generados {n} usuarios")

if __name__ == '__main__':
    generate_users(100)
```

## 📊 Estadísticas de Datos

### users.csv
- Total registros: 10
- Status: 8 active, 2 inactive
- Rango edad: 26-45 años
- Ciudades: 10 ciudades españolas distintas

### sales.csv
- Total registros: 15
- Total ventas: $3,114.44
- Categorías: Electronics (80%), Furniture (13%), Stationery (7%)
- Status: 10 completed, 2 pending, 2 shipped, 1 cancelled

### sensor_data.json
- Total lecturas: 5
- Sensores únicos: 3
- Rango temperatura: 21.0°C - 28.5°C
- Alertas: 1 warning (sensor TEMP002)

## ✅ Validation

Para validate la integridad de los datos:

```bash
# Contar registros
wc -l data/sample/*.csv

# Validar JSON
jq . data/sample/sensor_data.json

# Verificar schema SQL
psql --dry-run -f data/schemas/database_schema.sql
```

## 🔒 Buenas Prácticas

1. **No modificar datos de ejemplo**: Estos están versionados en Git
2. **Crear copias locales**: Si necesitas modificar, copia primero
3. **Usar datos sintéticos**: No usar datos reales de producción
4. **Validar antes de usar**: Siempre validate schema y calidad
5. **Documentar cambios**: Si añades datasets, actualiza este README

## 📚 Recursos Adicionales

- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [PostgreSQL Data Types](https://www.postgresql.org/docs/current/datatype.html)
- [JSON Schema](https://json-schema.org/)

---

**Datos listos para usar** ✅ | **Schema validado** ✅ | **Documentado** ✅
