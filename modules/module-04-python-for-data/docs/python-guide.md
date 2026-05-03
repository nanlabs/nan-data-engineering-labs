# 🐍 Python Guide - Best Practices for Data Engineering

## 📋 Table of Contents

1. [Fundamental Principles](#fundamental-principles)
2. [Code Style (PEP 8)](#code-style-pep-8)
3. [Data Structures](#data-structures)
4. [Error Handling](#error-handling)
5. [Performance and Optimization](#performance-and-optimization)
6. [Testing](#testing)
7. [Documentation](#documentation)
8. [Logging](#logging)
9. [Security](#security)
10. [Common Patterns](#common-patterns)

---

## 🎯 Fundamental Principles

### The Zen of Python

```python
import this
```

**Principios clave**:
- **Explicit is better than implicit**: Clear code over "smart" code
- **Simple is better than complex**: Avoid over-engineering
- **Readability counts**: Code that reads like prose
- **Errors should never pass silently**: Explicit error handling

### Philosophy for Data Engineering

1. **Idempotence**: Code must produce the same result if executed multiple times
2. **Reproducibilidad**: Mismo input → mismo output
3. **Observabilidad**: Log suficiente para debug
4. **Fail Fast**: Detectar errores temprano
5. **Validation**: Validate data at each critical step

---

## 📝 Code Style (PEP 8)

### Naming Conventions

```python
# ✅ Correct
class CustomerDataProcessor:
    """Usa PascalCase para clases"""
    pass

def calculate_total_sales(transactions):
    """Usa snake_case para funciones"""
    pass

MAXIMUM_RETRIES = 3  # UPPER_CASE para constantes
customer_id = 123    # snake_case para variables

# ❌ Incorrect
class customer_processor:  # Should be PascalCase
    pass

def CalculateSales():  # Should be snake_case
    pass

MaxRetries = 3  # Should be UPPER_CASE
```

### Indentation and Spacing

```python
# ✅ Correct: 4 espacios
def process_data(df):
    if df is not None:
        df = df.dropna()
        return df
    return None

# ✅ Correct: espacios alrededor de operadores
result = (value1 + value2) * factor
items = [1, 2, 3, 4, 5]

# ❌ Incorrect: tabulaciones mezcladas con espacios
def bad_function():
	print("Tab")  # Tab
    print("Spaces")  # Espacios

# ❌ Incorrect: sin espacios
result=(value1+value2)*factor
```

### Line Length

```python
# ✅ Correct: maximum 79 characters
def calculate_customer_lifetime_value(
    customer_id,
    purchase_history,
    average_order_value
):
    return sum(purchase_history) * average_order_value

# ✅ Correct: break en operadores
total = (
    first_value +
    second_value +
    third_value
)

# ❌ Incorrect: linea muy larga
def calculate_customer_lifetime_value(customer_id, purchase_history, average_order_value, discount_rate, retention_rate):
    pass
```

### Imports

```python
# ✅ Correct: orden de imports
# 1. Standard library
import os
import sys
from pathlib import Path

# 2. Third party
import pandas as pd
import numpy as np

# 3. Local
from .utils import process_data
from .validators import validate_schema

# ✅ Correct: one import per line
import pandas as pd
import numpy as np

# ❌ Incorrect: multiple imports on one line
import pandas, numpy, matplotlib
```

---

## 📦 Structures de Data

### Eligiendo la Structure Correcta

```python
# Lista: Orden importa, elementos duplicados OK
transactions = [100, 200, 100, 300]

# Tupla: Inmutable, faster than list
coordinates = (10.5, 20.3)

# Set: Unique, unordered, O(1) lookup
unique_customers = {1, 2, 3, 4, 5}

# Dict: Key-value, O(1) lookup
customer_data = {"name": "Ana", "age": 25}
```

### Comprehensions (Pythonic)

```python
# ✅ List comprehension (Pythonic)
squares = [x**2 for x in range(10)]

# ❌ Loop tradicional (no Pythonic)
squares = []
for x in range(10):
    squares.append(x**2)

# ✅ Con filtro
even_squares = [x**2 for x in range(10) if x % 2 == 0]

# ✅ Dict comprehension
id_to_name = {user['id']: user['name'] for user in users}

# ✅ Set comprehension
unique_lengths = {len(word) for word in words}
```

### Collections Module

```python
from collections import defaultdict, Counter, namedtuple

# defaultdict: evita KeyError
customer_orders = defaultdict(list)
customer_orders[123].append(order)  # No error si no existe

# Counter: contar elementos
word_counts = Counter(words)
most_common = word_counts.most_common(5)

# namedtuple: estructura ligera
Customer = namedtuple('Customer', ['id', 'name', 'email'])
customer = Customer(1, 'Ana', 'ana@example.com')
print(customer.name)  # More readable than customer[1]
```

---

## ⚠️ Manejo de Errores

### Try-Except (Specific)

```python
# ✅ Correct: captures specific exceptions
try:
    df = pd.read_csv(file_path)
except FileNotFoundError:
    logger.error(f"File not found: {file_path}")
    raise
except pd.errors.EmptyDataError:
    logger.warning("CSV file is empty")
    return pd.DataFrame()

# ❌ Incorrect: generic catch
try:
    df = pd.read_csv(file_path)
except Exception as e:  # Demasiado amplio
    pass  # Nunca usar pass silencioso
```

### Context Managers

```python
# ✅ Correct: with statement (automatically closes file)
with open('data.csv', 'r') as f:
    data = f.read()
# File closed automatically

# ❌ Incorrect: sin context manager
f = open('data.csv', 'r')
data = f.read()
f.close()  # Easy to forget
```

### Custom Exceptions

```python
# ✅ Create specific exceptions
class DataValidationError(Exception):
    """Raised when data validation fails"""
    pass

class SchemaError(DataValidationError):
    """Raised when schema doesn't match"""
    pass

def validate_data(df, expected_columns):
    if not all(col in df.columns for col in expected_columns):
        raise SchemaError(f"Missing columns: {expected_columns}")
```

### Logging Errors

```python
import logging

logger = logging.getLogger(__name__)

# ✅ Correct: log con contexto
try:
    result = risky_operation()
except ValueError as e:
    logger.error(
        f"Failed to process customer {customer_id}",
        exc_info=True,  # Include stack trace
        extra={'customer_id': customer_id}
    )
    raise
```

---

## ⚡ Performance and Optimization

### Vectorization (Pandas/NumPy)

```python
import pandas as pd
import numpy as np

# ❌ Slow: loop sobre DataFrame
for i in range(len(df)):
    df.loc[i, 'total'] = df.loc[i, 'price'] * df.loc[i, 'quantity']

# ✅ Fast: vectorized operation
df['total'] = df['price'] * df['quantity']

# ❌ Slow: apply with a simple function
df['doubled'] = df['value'].apply(lambda x: x * 2)

# ✅ Fast: direct operation
df['doubled'] = df['value'] * 2
```

### Generators (Lazy Evaluation)

```python
# ✅ Generator: bajo uso de memoria
def read_large_file(file_path):
    with open(file_path, 'r') as f:
        for line in f:
            yield process_line(line)

# Process line by line without loading all
for processed_line in read_large_file('huge_file.txt'):
    save(processed_line)

# ❌ Loadr todo en memoria
with open('huge_file.txt', 'r') as f:
    lines = [process_line(line) for line in f]  # Consume mucha RAM
```

### Caching

```python
from functools import lru_cache

# ✅ Cachear resultados costosos
@lru_cache(maxsize=128)
def expensive_calculation(n):
    # Expensive operation
    return result

# Primera llamada: calcula
result1 = expensive_calculation(10)  # Slow

# Segunda llamada: usa cache
result2 = expensive_calculation(10)  # Instant
```

### Profiling

```python
import cProfile
import pstats

# Profile function
cProfile.run('my_function()', 'profile_stats')

# Analizar resultados
stats = pstats.Stats('profile_stats')
stats.sort_stats('cumulative')
stats.print_stats(10)  # Top 10 slowest functions
```

---

## ✅ Testing

### Structure de Tests

```python
# ✅ AAA pattern (Arrange, Act, Assert)
def test_calculate_total():
    # Arrange: preparar data
    df = pd.DataFrame({
        'price': [10, 20, 30],
        'quantity': [2, 3, 1]
    })
    
    # Act: run function
    result = calculate_total(df)
    
    # Assert: verificar resultado
    assert result == 110  # (10*2 + 20*3 + 30*1)
```

### Fixtures (pytest)

```python
import pytest

# ✅ Fixture reutilizable
@pytest.fixture
def sample_dataframe():
    return pd.DataFrame({
        'id': [1, 2, 3],
        'value': [10, 20, 30]
    })

def test_process_data(sample_dataframe):
    result = process_data(sample_dataframe)
    assert len(result) == 3
```

### Parameterization

```python
# ✅ Test multiple cases
@pytest.mark.parametrize("input,expected", [
    (0, 0),
    (1, 1),
    (2, 4),
    (3, 9),
    (-2, 4),
])
def test_square(input, expected):
    assert square(input) == expected
```

### Mocking

```python
from unittest.mock import patch, Mock

# ✅ Mockear llamada externa
def test_fetch_data():
    with patch('requests.get') as mock_get:
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: {'data': [1, 2, 3]}
        )
        
        result = fetch_data('https://api.example.com')
        assert result == {'data': [1, 2, 3]}
```

---

## 📖 Documentation

### Docstrings (Google Style)

```python
def calculate_customer_ltv(transactions, discount_rate=0.1):
    """
    Calculate Customer Lifetime Value.
    
    Args:
        transactions (pd.DataFrame): DataFrame with customer transactions.
            Must contain 'customer_id', 'amount', 'date' columns.
        discount_rate (float, optional): Discount rate for future value.
            Defaults to 0.1.
    
    Returns:
        pd.DataFrame: DataFrame with customer_id and ltv columns.
    
    Raises:
        ValueError: If required columns are missing.
        TypeError: If transactions is not a DataFrame.
    
    Examples:
        >>> transactions = pd.DataFrame({
        ...     'customer_id': [1, 1, 2],
        ...     'amount': [100, 200, 150],
        ...     'date': ['2024-01-01', '2024-02-01', '2024-01-15']
        ... })
        >>> calculate_customer_ltv(transactions)
           customer_id  ltv
        0            1  300
        1            2  150
    """
    if not isinstance(transactions, pd.DataFrame):
        raise TypeError("transactions must be a DataFrame")
    
    required_cols = ['customer_id', 'amount', 'date']
    if not all(col in transactions.columns for col in required_cols):
        raise ValueError(f"Missing required columns: {required_cols}")
    
    # Implementation...
    return result
```

### Type Hints

```python
from typing import List, Dict, Optional, Union
import pandas as pd

# ✅ Type hints para claridad
def process_customers(
    customer_ids: List[int],
    filters: Optional[Dict[str, str]] = None
) -> pd.DataFrame:
    """Process customer data with optional filters."""
    if filters is None:
        filters = {}
    # Implementation...
    return df

# Tipos complejos
def merge_data(
    left: pd.DataFrame,
    right: pd.DataFrame,
    on: Union[str, List[str]]
) -> pd.DataFrame:
    """Merge two DataFrames."""
    return pd.merge(left, right, on=on)
```

---

## 📝 Logging

### Basic Configuration

```python
import logging

# ✅ Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

### Logging Levels

```python
# DEBUG: Detailed information for diagnostics
logger.debug(f"Processing customer {customer_id}")

# INFO: Confirmation of normal operations
logger.info(f"Successfully processed {count} records")

# WARNING: Something unexpected but not critical
logger.warning(f"Missing data for customer {customer_id}, using default")

# ERROR: Error that prevents an operation
logger.error(f"Failed to process file {file_name}", exc_info=True)

# CRITICAL: Critical error, the application may fail
logger.critical("Database connection lost")
```

### Structured Logging

```python
import logging
import json

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
        }
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        return json.dumps(log_data)

# ✅ Structured logs for analysis
logger.info(
    "Customer processed",
    extra={
        'customer_id': 123,
        'transaction_count': 5,
        'total_amount': 500.00
    }
)
```

---

## 🔒 security

### No Hardcodear Credenciales

```python
import os
from dotenv import load_dotenv

# ✅ Correct: variables de environment
load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# ❌ Incorrect: credentials in code
DB_PASSWORD = "my_secret_password"  # NUNCA!
```

### Input Validation

```python
# ✅ Validate y sanitizar inputs
def get_customer_data(customer_id: int) -> dict:
    if not isinstance(customer_id, int):
        raise TypeError("customer_id must be an integer")
    
    if customer_id <= 0:
        raise ValueError("customer_id must be positive")
    
    # Usar parametrized queries
    query = "SELECT * FROM customers WHERE id = %s"
    result = db.execute(query, (customer_id,))
    return result

# ❌ Vulnerable a SQL injection
def bad_query(customer_id):
    query = f"SELECT * FROM customers WHERE id = {customer_id}"
    return db.execute(query)
```

---

## 🎨 Patrones Comunes

### Factory Pattern

```python
# ✅ Factory para crear procesadores
class DataProcessorFactory:
    @staticmethod
    def create_processor(data_type: str):
        processors = {
            'csv': CSVProcessor,
            'json': JSONProcessor,
            'parquet': ParquetProcessor
        }
        
        processor_class = processors.get(data_type)
        if processor_class is None:
            raise ValueError(f"Unknown data type: {data_type}")
        
        return processor_class()

# Uso
processor = DataProcessorFactory.create_processor('csv')
processor.process(data)
```

### pipeline Pattern

```python
# ✅ Pipeline para transformaciones
class DataPipeline:
    def __init__(self):
        self.steps = []
    
    def add_step(self, func):
        self.steps.append(func)
        return self
    
    def execute(self, data):
        for step in self.steps:
            data = step(data)
        return data

# Uso
pipeline = (DataPipeline()
    .add_step(remove_nulls)
    .add_step(remove_duplicates)
    .add_step(normalize_values)
)

clean_data = pipeline.execute(raw_data)
```

### Singleton Pattern

```python
# ✅ Singleton para configuration
class Config:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        # Loadr configuration
        pass

# Siempre devuelve la misma instancia
config1 = Config()
config2 = Config()
assert config1 is config2  # True
```

---

## 💡 Best Practices Checklist

### Antes de Commit

- [ ] Code follows PEP 8
- [ ] Funciones tienen docstrings
- [ ] Tests pasan
- [ ] No hay print() de debug
- [ ] No hay credenciales hardcodeadas
- [ ] Imports organizados
- [ ] Variables tienen nombres descriptivos
- [ ] Code is DRY (Don't Repeat Yourself)

### Antes de Deploy

- [ ] Integration tests pass
- [ ] Logging configurado adecuadamente
- [ ] Manejo de errores implementado
- [ ] Updated documentation
- [ ] Performance aceptable
- [ ] Peer reviewed code
- [ ] Variables de environment configuradas
- [ ] Dependencias documentadas

---

## 📚 Additional Resources

- **PEP 8**: https://pep8.org/
- **Python Type Hints**: https://docs.python.org/3/library/typing.html
- **pytest**: https://docs.pytest.org/
- **Clean Code in Python**: Libro recomendado
- **Effective Python**: Libro recomendado

---

**Last update**: Module 04 - Step 8
**Version**: 1.0
