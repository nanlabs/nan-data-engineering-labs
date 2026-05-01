# ETL Design Patterns

## 🎨 Design Patterns

### 1. pipeline Pattern

**Un flujo secuencial de transformaciones**:

```python
def pipeline():
    df = extract()
    df = clean(df)
    df = transform(df)
    df = enrich(df)
    df = validate(df)
    load(df)
```

**features**:
- Linear and easy to understand
- Cada paso depende del anterior
- Easy to debug

**When to use**:
- Transformaciones simples
- Dependencies claras
- Procesos batch

### 2. Fan-Out Pattern

**Process multiple targets in parallel**:

```python
def fan_out():
    df = extract()
    df = transform(df)

    # Cargar a múltiples destinos en paralelo
    with ThreadPoolExecutor() as executor:
        executor.submit(load_warehouse, df)
        executor.submit(load_cache, df)
        executor.submit(load_search, df)
```

**features**:
- Parallelization
- Multiple consumers
- Mejor performance

**When to use**:
- Multiple destinations
- Destinos independientes
- High throughput necesario

### 3. Fan-In Pattern

**Combine data from multiple sources**:

```python
def fan_in():
    # Extract en paralelo
    with ThreadPoolExecutor() as executor:
        future1 = executor.submit(extract_db1)
        future2 = executor.submit(extract_db2)
        future3 = executor.submit(extract_api)

    # Combine
    df = pd.concat([
        future1.result(),
        future2.result(),
        future3.result()
    ])

    transform_and_load(df)
```

**features**:
- Multiple sources
- Data consolidation
- Parallel extraction

**When to use**:
- Data from multiple systems
- Necessary consolidation
- Extract es cuello de botella

### 4. Map-Reduce Pattern

**Procesar datos en paralelo y agregar**:

```python
from multiprocessing import Pool

def map_reduce(files):
    # MAP: Procesar cada archivo en paralelo
    with Pool() as pool:
        results = pool.map(process_file, files)

    # REDUCE: Combinar resultados
    final = pd.concat(results).groupby('key').sum()
    return final

def process_file(file):
    df = pd.read_csv(file)
    return df.groupby('key').sum()
```

**features**:
- Divide y conquista
- Massive parallelization
- Final aggregation

**When to use**:
- Large volumes
- Procesamiento independiente
- Agregaciones necesarias

### 5. Delta Import Pattern

**Load only changes from last run**:

```python
def delta_import():
    # Get watermark
    last_run = get_watermark()

    # Extract solo nuevos
    df = extract_where(f"updated_at > '{last_run}'")

    # Process
    transformed = transform(df)

    # Load
    upsert(transformed)

    # Update watermark
    set_watermark(datetime.now())
```

**features**:
- Eficiente
- Incremental
- Requiere timestamp column

**When to use**:
- tables grandes
- Updates frecuentes
- Tiempos de ventana limitados

### 6. Slowly Changing Dimension (SCD)

Historical track of changes in dimensions:

#### Type 1: Overwrite

```python
def scd_type1(new_record):
    """Sobreescribe - no guarda historia"""
    update_customer(
        customer_id=new_record['id'],
        name=new_record['name'],
        address=new_record['address']
    )
```

#### Type 2: Add Row

```python
def scd_type2(new_record):
    """Nueva fila - guarda historia completa"""
    # Cerrar fila actual
    update(f"""
        UPDATE customers
        SET valid_to = CURRENT_DATE, is_current = false
        WHERE customer_id = {new_record['id']} AND is_current = true
    """)

    # Insertar nueva fila
    insert(f"""
        INSERT INTO customers
        (customer_id, name, address, valid_from, valid_to, is_current)
        VALUES
        ({new_record['id']}, '{new_record['name']}', '{new_record['address']}',
         CURRENT_DATE, '9999-12-31', true)
    """)
```

#### Type 3: Add Column

```python
def scd_type3(new_record):
    """Columnas adicionales - historia limitada"""
    update(f"""
        UPDATE customers
        SET
            current_address = '{new_record['address']}',
            previous_address = current_address,
            last_updated = CURRENT_DATE
        WHERE customer_id = {new_record['id']}
    """)
```

**When to use each type**:
- **Type 1**: Correcciones, datos que no necesitan historia
- **Type 2**: Complete audit trail, historical reporting
- **Type 3**: Limited history, specific columns

---

## 🛠️ Implementation Patterns

### Configuration-Driven ETL

**pipeline configurable via config file**:

```python
# config.yaml
source:
  type: postgres
  host: localhost
  database: source_db
  table: users

transformations:
  - type: filter
    column: status
    value: active
  - type: rename
    mapping:
      user_id: id
      user_name: name

destination:
  type: s3
  bucket: data-lake
  prefix: users/
```

```python
# etl.py
def run_etl(config):
    # Extract dinámico
    source = SourceFactory.create(config['source'])
    df = source.extract()

    # Transform dinámico
    for transform in config['transformations']:
        df = apply_transform(df, transform)

    # Load dinámico
    destination = DestinationFactory.create(config['destination'])
    destination.load(df)
```

**Ventajas**:
- Reutilizable
- No code changes para nuevos pipelines
- Easy to test

### Template Method Pattern

**Define estructura, subclases implementan detalles**:

```python
from abc import ABC, abstractmethod

class ETLPipeline(ABC):
    def run(self):
        """Template method - no override"""
        self.setup()
        data = self.extract()
        data = self.transform(data)
        self.load(data)
        self.cleanup()

    @abstractmethod
    def extract(self):
        """Subclases implementan"""
        pass

    @abstractmethod
    def transform(self, data):
        pass

    @abstractmethod
    def load(self, data):
        pass

    def setup(self):
        """Default implementation - puede override"""
        self.logger.info("Starting ETL")

    def cleanup(self):
        self.logger.info("ETL completed")

# Implementación concreta
class UserETL(ETLPipeline):
    def extract(self):
        return pd.read_sql("SELECT * FROM users", self.conn)

    def transform(self, data):
        data['email'] = data['email'].str.lower()
        return data

    def load(self, data):
        data.to_parquet('users.parquet')
```

### Strategy Pattern

**Intercambiar algoritmos en runtime**:

```python
class TransformStrategy(ABC):
    @abstractmethod
    def transform(self, df):
        pass

class CleaningStrategy(TransformStrategy):
    def transform(self, df):
        df = df.dropna()
        df = df.drop_duplicates()
        return df

class AggregationStrategy(TransformStrategy):
    def transform(self, df):
        return df.groupby('user_id').agg({
            'amount': 'sum',
            'count': 'count'
        })

class ETLPipeline:
    def __init__(self, strategy: TransformStrategy):
        self.strategy = strategy

    def run(self):
        df = self.extract()
        df = self.strategy.transform(df)  # Strategy aplicado
        self.load(df)
```

---

## 🚨 Error Handling Patterns

### Retry Pattern

**Re-intentar operaciones que fallan**:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def extract_from_api():
    response = requests.get(API_URL)
    response.raise_for_status()
    return response.json()
```

### Circuit Breaker Pattern

**Evitar requests a service que falla**:

```python
from pybreaker import CircuitBreaker

breaker = CircuitBreaker(fail_max=5, timeout_duration=60)

@breaker
def call_external_api():
    return requests.get(API_URL).json()

try:
    data = call_external_api()
except CircuitBreakerError:
    # Usar fallback o cached data
    data = get_cached_data()
```

### Dead Letter Queue Pattern

**Guardar registros que fallan para reprocessing**:

```python
def process_records(records):
    successful = []
    failed = []

    for record in records:
        try:
            processed = transform(record)
            successful.append(processed)
        except Exception as e:
            failed.append({
                'record': record,
                'error': str(e),
                'timestamp': datetime.now()
            })

    # Load successful
    load(successful)

    # Save failed to DLQ
    save_to_dlq(failed)
```

### Graceful Degradation

**Continuar con funcionalidad parcial**:

```python
def enrich_data(df):
    # Intentar enrichment externo
    try:
        df = enrich_with_api(df)
    except Exception as e:
        logger.warning(f"API enrichment failed: {e}")
        # Continuar sin enrichment

    # Resto del pipeline continúa
    return df
```

---

## 📊 Data Quality Patterns

### Schema Validation Pattern

**Validar schema antes de procesar**:

```python
from pydantic import BaseModel, ValidationError

class UserRecord(BaseModel):
    id: int
    name: str
    email: str
    age: int

def validate_and_load(records):
    valid = []
    invalid = []

    for record in records:
        try:
            validated = UserRecord(**record)
            valid.append(validated.dict())
        except ValidationError as e:
            invalid.append({'record': record, 'errors': e.errors()})

    return valid, invalid
```

### Data Profiling Pattern

**Generate data statistics**:

```python
def profile_data(df):
    profile = {
        'row_count': len(df),
        'null_counts': df.isnull().sum().to_dict(),
        'dtypes': df.dtypes.to_dict(),
        'unique_counts': df.nunique().to_dict(),
        'numeric_stats': df.describe().to_dict()
    }

    # Save profile
    save_profile(profile)

    # Check thresholds
    if profile['null_counts']['email'] > 100:
        raise DataQualityError("Too many null emails")

    return profile
```

### Reconciliation Pattern

**Comparar source vs destination**:

```python
def reconcile():
    # Count source
    source_count = count_source_records()

    # Count destination
    dest_count = count_dest_records()

    # Compare
    if source_count != dest_count:
        alert(f"Mismatch: {source_count} source vs {dest_count} dest")

    # Sample checking
    source_sample = get_source_sample()
    dest_sample = get_dest_sample()

    if not samples_match(source_sample, dest_sample):
        alert("Sample data mismatch")
```

---

## 🔄 Transaction Patterns

### All-or-Nothing Pattern

**Commit solo si todo es exitoso**:

```python
def transactional_load(df):
    conn = create_connection()
    try:
        with conn.begin():  # Transaction
            # Truncate staging
            conn.execute("TRUNCATE staging_table")

            # Load to staging
            df.to_sql('staging_table', conn, if_exists='append')

            # Validate
            validate_staging(conn)

            # Swap tables
            conn.execute("ALTER TABLE main_table RENAME TO main_table_old")
            conn.execute("ALTER TABLE staging_table RENAME TO main_table")
            conn.execute("DROP TABLE main_table_old")

            # Commit implícito al salir de with
    except Exception as e:
        # Rollback automático
        logger.error(f"Transaction failed: {e}")
        raise
```

### Staging Pattern

**Upload to staging before production**:

```python
def staged_load(df):
    # Step 1: Load to staging
    df.to_sql('staging_users', conn, if_exists='replace')

    # Step 2: Validate staging
    validate_counts('staging_users')
    validate_quality('staging_users')

    # Step 3: Move to production
    conn.execute("""
        INSERT INTO users
        SELECT * FROM staging_users
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            email = EXCLUDED.email,
            updated_at = CURRENT_TIMESTAMP
    """)

    # Step 4: Cleanup staging
    conn.execute("DROP TABLE staging_users")
```

---

## 🧪 Testing Patterns

### Test Data Builders

```python
class UserBuilder:
    def __init__(self):
        self.data = {
            'id': 1,
            'name': 'Test User',
            'email': 'test@example.com',
            'age': 30
        }

    def with_id(self, id):
        self.data['id'] = id
        return self

    def with_invalid_email(self):
        self.data['email'] = 'invalid'
        return self

    def build(self):
        return self.data

# Uso
user = UserBuilder().with_id(123).with_invalid_email().build()
```

### Assertions Pattern

```python
def test_etl():
    # Arrange
    input_df = create_test_data()

    # Act
    result = run_pipeline(input_df)

    # Assert
    assert len(result) == len(input_df)
    assert result['email'].notnull().all()
    assert result['age'].between(0, 120).all()
    assert not result.duplicated('id').any()
```

### Mock Pattern

```python
from unittest.mock import Mock, patch

def test_api_extraction():
    # Mock API response
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = [
            {'id': 1, 'name': 'User 1'},
            {'id': 2, 'name': 'User 2'}
        ]

        # Test
        result = extract_from_api()

        # Verify
        assert len(result) == 2
        mock_get.assert_called_once()
```

---

## 📈 Performance Patterns

### Chunking Pattern

**Procesar datos en chunks para mejor memory management**:

```python
def chunked_processing(file, chunk_size=10000):
    for chunk in pd.read_csv(file, chunksize=chunk_size):
        transformed = transform(chunk)
        load(transformed)
```

### Parallel Processing Pattern

```python
from concurrent.futures import ThreadPoolExecutor

def parallel_load(dfs, workers=4):
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(load_partition, df, i)
            for i, df in enumerate(dfs)
        ]

        # Wait for all
        for future in futures:
            future.result()
```

### Caching Pattern

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_lookup_value(key):
    """Cache lookup table en memoria"""
    return db.query(f"SELECT value FROM lookup WHERE key='{key}'")
```

---

Continue to [03-resources.md](./03-resources.md) for additional tools and resources.
