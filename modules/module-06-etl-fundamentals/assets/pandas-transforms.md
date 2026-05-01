# pandas Transforms Cheat Sheet

## 📊 Data Loading

```python
import pandas as pd

# CSV
df = pd.read_csv('file.csv', encoding='utf-8', parse_dates=['date_col'])

# JSON
df = pd.read_json('file.json', orient='records', lines=True)

# Parquet
df = pd.read_parquet('file.parquet')

# SQL
df = pd.read_sql('SELECT * FROM table', connection)

# Excel
df = pd.read_excel('file.xlsx', sheet_name='Sheet1')
```

## 🧹 Data Cleaning

### Remove Duplicates
```python
# All columns
df = df.drop_duplicates()

# Specific columns
df = df.drop_duplicates(subset=['id', 'email'])

# Keep last occurrence
df = df.drop_duplicates(keep='last')
```

### Handle Missing Values
```python
# Drop rows with any null
df = df.dropna()

# Drop rows with null in specific columns
df = df.dropna(subset=['email', 'id'])

# Fill nulls
df['col'] = df['col'].fillna(0)
df['col'] = df['col'].fillna(df['col'].mean())
df = df.fillna({'col1': 0, 'col2': 'Unknown'})

# Forward/backward fill
df['col'] = df['col'].ffill()  # Forward fill
df['col'] = df['col'].bfill()  # Backward fill
```

### Filter Rows
```python
# Simple filter
df = df[df['age'] > 18]
df = df[df['status'] == 'active']

# Multiple conditions
df = df[(df['age'] > 18) & (df['country'] == 'USA')]
df = df[(df['status'] == 'active') | (df['status'] == 'pending')]

# isin
df = df[df['country'].isin(['USA', 'UK', 'Canada'])]

# String contains
df = df[df['email'].str.contains('@gmail.com')]

# Regex
df = df[df['email'].str.match(r'^[\w\.-]+@[\w\.-]+\.\w+$')]
```

## 🔄 Data Transformation

### String Operations
```python
# Case conversion
df['email'] = df['email'].str.lower()
df['name'] = df['name'].str.upper()
df['name'] = df['name'].str.title()

# Strip whitespace
df['name'] = df['name'].str.strip()

# Replace
df['status'] = df['status'].str.replace('old', 'new')

# Split
df[['first', 'last']] = df['name'].str.split(' ', n=1, expand=True)

# Extract with regex
df['area_code'] = df['phone'].str.extract(r'(\d{3})-')
```

### Type Conversions
```python
# To numeric
df['age'] = pd.to_numeric(df['age'], errors='coerce')

# To datetime
df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')

# To category (saves memory)
df['status'] = df['status'].astype('category')

# To string
df['id'] = df['id'].astype(str)
```

### Create New Columns
```python
# Simple calculation
df['total'] = df['price'] * df['quantity']

# Conditional
df['category'] = df['age'].apply(lambda x: 'adult' if x >= 18 else 'minor')

# Using np.where
import numpy as np
df['category'] = np.where(df['age'] >= 18, 'adult', 'minor')

# Multiple conditions
df['category'] = np.select(
    [df['age'] < 18, df['age'] < 65, df['age'] >= 65],
    ['minor', 'adult', 'senior']
)

# Apply function
def categorize(age):
    if age < 18:
        return 'minor'
    elif age < 65:
        return 'adult'
    else:
        return 'senior'

df['category'] = df['age'].apply(categorize)
```

### Date/Time Operations
```python
# Extract components
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
df['day'] = df['date'].dt.day
df['dayofweek'] = df['date'].dt.dayofweek
df['quarter'] = df['date'].dt.quarter

# Date arithmetic
df['next_week'] = df['date'] + pd.Timedelta(days=7)
df['age_days'] = (pd.Timestamp.now() - df['created_at']).dt.days
```

## 📊 Aggregations

### Basic Aggregations
```python
# Single column
df['amount'].sum()
df['age'].mean()
df['id'].count()
df['price'].max()
df['price'].min()
df['quantity'].std()

# Multiple aggregations
df.agg({
    'amount': ['sum', 'mean', 'count'],
    'quantity': ['sum', 'max']
})
```

### Group By
```python
# Simple group by
df.groupby('country')['amount'].sum()

# Multiple columns
df.groupby(['country', 'status'])['amount'].sum()

# Multiple aggregations
df.groupby('country').agg({
    'amount': ['sum', 'mean', 'count'],
    'age': 'mean'
})

# Custom aggregation
df.groupby('country').agg(
    total_amount=('amount', 'sum'),
    avg_age=('age', 'mean'),
    count=('id', 'count')
)

# Filter groups
df.groupby('country').filter(lambda x: len(x) > 10)
```

### Pivot Tables
```python
# Simple pivot
pd.pivot_table(
    df,
    values='amount',
    index='country',
    columns='status',
    aggfunc='sum'
)

# Multiple aggregations
pd.pivot_table(
    df,
    values='amount',
    index='country',
    columns='status',
    aggfunc=['sum', 'mean', 'count']
)
```

## 🔗 Joins and Merges

### Merge DataFrames
```python
# Inner join
result = pd.merge(df1, df2, on='id', how='inner')

# Left join
result = pd.merge(df1, df2, on='id', how='left')

# Multiple keys
result = pd.merge(df1, df2, on=['id', 'date'], how='inner')

# Different column names
result = pd.merge(
    df1, df2,
    left_on='user_id',
    right_on='id',
    how='left'
)

# Suffixes for duplicate columns
result = pd.merge(
    df1, df2,
    on='id',
    how='inner',
    suffixes=('_left', '_right')
)
```

### Concat DataFrames
```python
# Vertical concat (stack)
result = pd.concat([df1, df2], axis=0, ignore_index=True)

# Horizontal concat (side by side)
result = pd.concat([df1, df2], axis=1)
```

## 🎯 Advanced Transforms

### Window Functions
```python
# Rolling average
df['rolling_avg'] = df['amount'].rolling(window=7).mean()

# Cumulative sum
df['cumsum'] = df['amount'].cumsum()

# Rank
df['rank'] = df['amount'].rank(ascending=False)

# Percentage change
df['pct_change'] = df['amount'].pct_change()
```

### Reshaping
```python
# Wide to long
df_long = pd.melt(
    df,
    id_vars=['id', 'date'],
    value_vars=['jan', 'feb', 'mar'],
    var_name='month',
    value_name='sales'
)

# Long to wide
df_wide = df_long.pivot(
    index='id',
    columns='month',
    values='sales'
)
```

## 💾 Data Export

```python
# CSV
df.to_csv('output.csv', index=False, encoding='utf-8')

# JSON
df.to_json('output.json', orient='records', lines=True)

# Parquet
df.to_parquet('output.parquet', compression='snappy')

# SQL
df.to_sql('table_name', connection, if_exists='replace', index=False)

# Excel
df.to_excel('output.xlsx', sheet_name='Sheet1', index=False)
```

## 🔍 Data Inspection

```python
# Basic info
df.info()
df.describe()
df.head(10)
df.tail(10)
df.sample(5)

# Shape and size
df.shape
len(df)
df.columns
df.dtypes

# Nulls
df.isnull().sum()
df.isnull().sum() / len(df) * 100  # Percentage

# Unique values
df['col'].nunique()
df['col'].value_counts()
df['col'].unique()

# Memory usage
df.memory_usage(deep=True)
```

---

💡 **Pro Tips**:
- Use `.copy()` to avoid SettingWithCopyWarning
- Chain operations for readability
- Use vectorized operations (avoid loops)
- Use `.loc[]` for setting values safely
- Profile with `%%timeit` for performance
