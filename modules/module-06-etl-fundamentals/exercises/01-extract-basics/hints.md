# Hints for Exercise 01: Extract Basics

## Task 1: CSV Extraction

### Reading CSV
```python
df = pd.read_csv(file_path, encoding='utf-8')
```

### Common Issues
1. **Encoding errors**: Try `latin-1` or `iso-8859-1` if `utf-8` fails
2. **Date parsing**: Use `parse_dates` parameter
3. **Missing values**: Check with `df.isnull().sum()`

### Validation Pattern
```python
required_cols = ['id', 'email', 'created_at']
missing = set(required_cols) - set(df.columns)
if missing:
    raise ValueError(f"Missing columns: {missing}")
```

## Task 2: JSON Extraction

### JSON Lines Format
JSON Lines has one JSON object per line:
```json
{"id": 1, "name": "Alice"}
{"id": 2, "name": "Bob"}
```

Use `lines=True`:
```python
df = pd.read_json(file_path, lines=True)
```

### Nested JSON
If JSON has nested structures:
```python
df = pd.json_normalize(data, sep='_')
```

## Task 3: API Extraction

### Basic Request
```python
import requests

response = requests.get(api_url)
response.raise_for_status()  # Raise error for bad status
data = response.json()
```

### Rate Limiting
```python
import time

for i in range(pages):
    response = requests.get(url)
    data = response.json()
    time.sleep(1)  # Wait 1 second between requests
```

### Error Handling
```python
try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    logger.error(f"API request failed: {e}")
    raise
```

## Task 4: Database Extraction

### SQLite Connection
```python
import sqlite3

conn = sqlite3.connect('database.db')
df = pd.read_sql('SELECT * FROM users', conn)
conn.close()
```

### With SQLAlchemy
```python
from sqlalchemy import create_engine

engine = create_engine('sqlite:///database.db')
df = pd.read_sql('SELECT * FROM users', engine)
```

### Context Manager (Best Practice)
```python
with sqlite3.connect('database.db') as conn:
    df = pd.read_sql('SELECT * FROM users', conn)
```

## General Tips

### Error Handling Pattern
```python
def extract_data(source):
    try:
        # Extract logic
        data = read_from_source(source)

        # Validate
        if data.empty:
            raise ValueError("No data extracted")

        return data
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        raise
```

### Logging
```python
import logging

logger = logging.getLogger(__name__)

logger.info(f"Extracting from {source}")
logger.info(f"Extracted {len(df)} records")
```

### Data Validation
```python
# Check for nulls
null_counts = df.isnull().sum()
if null_counts.any():
    logger.warning(f"Null values found: {null_counts[null_counts > 0]}")

# Check data types
assert df['id'].dtype == 'int64'
assert df['email'].dtype == 'object'

# Check value ranges
assert df['age'].between(0, 120).all()
```

## Common Pandas Parameters

### read_csv
- `encoding`: 'utf-8', 'latin-1', 'iso-8859-1'
- `parse_dates`: List of columns to parse as dates
- `dtype`: Dictionary of column types
- `na_values`: Additional strings to recognize as NaN
- `nrows`: Number of rows to read (for testing)

### read_json
- `lines`: True for JSON Lines format
- `orient`: 'records', 'split', 'index', 'columns'
- `convert_dates`: List of columns to convert to datetime

### read_sql
- `chunksize`: Read in chunks for large datasets
- `parse_dates`: List of date columns
- `index_col`: Column to use as index
