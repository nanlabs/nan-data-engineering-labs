# Data Quality - Conceptos Fundamentales

## Introduction

**Data quality** is critical to the success of any data project. Low-quality data leads to incorrect decisions, loss of trust, high operational costs, and regulatory compliance issues. In this module we will learn to measure, validate and guarantee the quality of data throughout the entire pipeline.

> **"Garbage in, garbage out"** - If the input data is of poor quality, the results will also be poor, regardless of how sophisticated the analysis is.

---

## What is Data Quality?

Data quality refers to the **suitability of the data for its intended purpose**. High quality data is:

- **Precisos**: Reflejan la realidad correctamente
- **Completos**: Contienen todos los valores requeridos
- **Consistentes**: No contienen contradicciones
- **Timely**: They are available when needed
- **Valid**: They comply with defined rules and formats
- **Unique**: No unnecessary duplicates

### Impact of Poor Data Quality

**Costos Empresariales:**
- IBM estimates that poor data quality costs companies $3.1 trillion annually in the US alone.
- Gartner reports that poor data quality costs organizations an average of $12.9 million per year

**Consecuencias Operacionales:**
- Decisiones de negocio incorrectas
- Loss of customer trust
- Incumplimiento regulatorio (GDPR, CCPA)
- Tiempo desperdiciado en limpieza manual
- Proyectos de ML/AI fallidos

**Ejemplo Real:**
In 2018, Amazon had to discontinue its AI-based recruiting tool because the model was trained with biased historical data, discriminating against female candidates.

---

## Las 6 Dimensiones de Data Quality

### 1. **Accuracy (Exactitud)**

**Definition:** Data correctly reflects the real world it represents.

**Preguntas Clave:**
- Are the values ​​correct?
- Does the information reflect reality?
- Has the data been verified against a reliable source?

**Ejemplos de Problemas:**
```python
# ❌ Problemas de exactitud
customers = [
    {"name": "John Doe", "email": "john@@example.com"},      # Email inválido
    {"name": "Jane Smith", "age": -5},                       # Edad imposible
    {"name": "Bob", "phone": "123"},                         # Teléfono incompleto
    {"name": "Alice", "salary": 999999999}                   # Salario irreal
]
```

**Validaciones de Exactitud:**
```python
import re
from typing import Dict, List

def validate_accuracy(record: Dict) -> List[str]:
    """Validate la exactitud de un registro."""
    errors = []

    # Validar email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if 'email' in record and not re.match(email_pattern, record['email']):
        errors.append(f"Email inválido: {record['email']}")

    # Validar edad
    if 'age' in record:
        if not 0 <= record['age'] <= 120:
            errors.append(f"Edad fuera de rango: {record['age']}")

    # Validar teléfono
    if 'phone' in record:
        phone_clean = re.sub(r'[^\d]', '', record['phone'])
        if len(phone_clean) < 10:
            errors.append(f"Teléfono incompleto: {record['phone']}")

    # Validar salario
    if 'salary' in record:
        if not 0 <= record['salary'] <= 10_000_000:
            errors.append(f"Salario fuera de rango razonable: {record['salary']}")

    return errors

# Uso
for customer in customers:
    errors = validate_accuracy(customer)
    if errors:
        print(f"Errores en {customer['name']}: {errors}")
```

**Accuracy Metrics:**
```python
def calculate_accuracy_rate(df, validation_func):
    """Calcula la tasa de exactitud de un DataFrame."""
    total_records = len(df)
    accurate_records = 0

    for _, row in df.iterrows():
        errors = validation_func(row.to_dict())
        if not errors:
            accurate_records += 1

    accuracy_rate = (accurate_records / total_records) * 100
    return accuracy_rate
```

---

### 2. **Completeness (Completitud)**

**Definition:** All required data is present.

**Preguntas Clave:**
- Are there any required fields missing?
- Are there null values ​​where they shouldn't exist?
- Are all expected records present?

**Ejemplos de Problemas:**
```python
# ❌ Problemas de completitud
transactions = pd.DataFrame({
    'transaction_id': [1, 2, 3, 4, 5],
    'customer_id': [101, 102, None, 104, 105],      # NULL en campo crítico
    'amount': [50.0, None, 75.0, 100.0, 25.0],     # Monto faltante
    'timestamp': ['2024-01-01', '2024-01-02', '2024-01-03', None, '2024-01-05'],
    'product': ['Widget', 'Gadget', '', 'Tool', 'Device']  # String vacío
})
```

**Completeness Analysis:**
```python
import pandas as pd
import numpy as np

def analyze_completeness(df: pd.DataFrame) -> pd.DataFrame:
    """Analiza la completitud de un DataFrame."""
    completeness_report = pd.DataFrame({
        'column': df.columns,
        'total_rows': len(df),
        'null_count': df.isnull().sum().values,
        'null_percentage': (df.isnull().sum() / len(df) * 100).values,
        'empty_string_count': [(df[col] == '').sum() if df[col].dtype == 'object' else 0
                               for col in df.columns],
        'whitespace_count': [(df[col].str.strip() == '').sum()
                            if df[col].dtype == 'object' else 0
                            for col in df.columns]
    })

    # Calcular completitud total (considerando NULL, empty, whitespace)
    completeness_report['missing_total'] = (
        completeness_report['null_count'] +
        completeness_report['empty_string_count'] +
        completeness_report['whitespace_count']
    )

    completeness_report['completeness_rate'] = (
        (1 - completeness_report['missing_total'] / len(df)) * 100
    ).round(2)

    return completeness_report.sort_values('completeness_rate')

# Uso
report = analyze_completeness(transactions)
print(report)
```

**Completitud por Level:**

1. **Row-Level Completeness (Completitud de Registros)**
   ```python
   def row_completeness(df: pd.DataFrame, required_fields: List[str]) -> pd.Series:
       """Calcula completitud por registro."""
       def check_row(row):
           missing = sum(1 for field in required_fields
                        if pd.isna(row[field]) or row[field] == '')
           return (len(required_fields) - missing) / len(required_fields) * 100

       return df.apply(check_row, axis=1)

   # Uso
   required_fields = ['customer_id', 'amount', 'timestamp']
   transactions['completeness'] = row_completeness(transactions, required_fields)

   # Filtrar registros incompletos
   incomplete = transactions[transactions['completeness'] < 100]
   print(f"Registros incompletos: {len(incomplete)}")
   ```

2. **Column-Level Completeness (Completitud de columns)**
   ```python
   def column_completeness(df: pd.DataFrame) -> Dict[str, float]:
       """Calcula completitud por columna."""
       return {
           col: ((df[col].notna().sum() / len(df)) * 100)
           for col in df.columns
       }
   ```

3. **Dataset-Level Completeness (Completitud del Dataset)**
   ```python
   def dataset_completeness(df: pd.DataFrame) -> float:
       """Calcula completitud global del dataset."""
       total_cells = df.shape[0] * df.shape[1]
       non_null_cells = df.notna().sum().sum()
       return (non_null_cells / total_cells) * 100
   ```

---

### 3. **Consistency (Consistencia)**

**Definition:** Data is consistent within the same dataset and between different datasets.

**Preguntas Clave:**
- Does the data follow the same format?
- Are the related values ​​consistent?
- Does the data match between systems?

**Tipos de Inconsistencias:**

**3.1 Inconsistencia de Formato:**
```python
# ❌ Formatos inconsistentes
dates_inconsistent = [
    '2024-01-15',          # ISO format
    '01/15/2024',          # US format
    '15-01-2024',          # EU format
    'January 15, 2024',    # Text format
]

phones_inconsistent = [
    '+1-555-123-4567',
    '(555) 123-4567',
    '555.123.4567',
    '5551234567',
]
```

**Standardization:**
```python
from datetime import datetime
import re

def standardize_date(date_str: str) -> str:
    """Estandariza fechas a ISO 8601."""
    formats = [
        '%Y-%m-%d',
        '%m/%d/%Y',
        '%d-%m-%Y',
        '%B %d, %Y',
        '%d %B %Y'
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue

    raise ValueError(f"Formato de fecha no reconocido: {date_str}")

def standardize_phone(phone: str) -> str:
    """Estandariza teléfonos a formato E.164."""
    # Extraer solo dígitos
    digits = re.sub(r'[^\d]', '', phone)

    # Agregar código de país si no existe
    if len(digits) == 10:
        digits = '1' + digits  # US/Canada

    return f"+{digits}"

# Uso
dates_standardized = [standardize_date(d) for d in dates_inconsistent]
phones_standardized = [standardize_phone(p) for p in phones_inconsistent]
```

**3.2 Inconsistencia Referencial:**
```python
# ❌ Referencias inconsistentes
customers = pd.DataFrame({
    'customer_id': [1, 2, 3],
    'name': ['Alice', 'Bob', 'Charlie']
})

orders = pd.DataFrame({
    'order_id': [101, 102, 103, 104],
    'customer_id': [1, 2, 999, None],  # 999 no existe, None es inválido
    'amount': [100, 200, 150, 75]
})

def check_referential_integrity(
    child_df: pd.DataFrame,
    parent_df: pd.DataFrame,
    foreign_key: str,
    primary_key: str
) -> pd.DataFrame:
    """Detecta violaciones de integridad referencial."""
    valid_ids = set(parent_df[primary_key].dropna().unique())
    child_ids = child_df[foreign_key].dropna()

    orphans = child_df[
        ~child_df[foreign_key].isin(valid_ids) &
        child_df[foreign_key].notna()
    ]

    return orphans

# Detectar orders con customer_id inválido
orphan_orders = check_referential_integrity(
    orders, customers, 'customer_id', 'customer_id'
)
print(f"Orders huérfanos: {len(orphan_orders)}")
```

**3.3 Logical Inconsistency:**
```python
# ❌ Inconsistencias lógicas
employees = pd.DataFrame({
    'employee_id': [1, 2, 3, 4],
    'birth_date': ['1990-01-15', '1985-05-20', '2010-03-10', '1975-11-30'],
    'hire_date': ['2015-06-01', '2010-01-15', '2020-09-01', '2000-05-15'],
    'retirement_date': ['2019-12-31', None, None, None]
})

def validate_logical_consistency(df: pd.DataFrame) -> List[Dict]:
    """Validate reglas lógicas de negocio."""
    issues = []

    for idx, row in df.iterrows():
        birth = pd.to_datetime(row['birth_date'])
        hire = pd.to_datetime(row['hire_date'])
        retire = pd.to_datetime(row['retirement_date']) if row['retirement_date'] else None

        # Regla: debe tener al menos 18 años al ser contratado
        age_at_hire = (hire - birth).days / 365.25
        if age_at_hire < 18:
            issues.append({
                'employee_id': row['employee_id'],
                'issue': f"Contratado con {age_at_hire:.1f} años (mínimo: 18)"
            })

        # Regla: fecha de retiro debe ser después de contratación
        if retire and retire < hire:
            issues.append({
                'employee_id': row['employee_id'],
                'issue': "Fecha de retiro anterior a contratación"
            })

        # Regla: retiro debe ser antes de muerte (asumiendo edad máxima 100)
        if retire:
            age_at_retire = (retire - birth).days / 365.25
            if age_at_retire > 100:
                issues.append({
                    'employee_id': row['employee_id'],
                    'issue': f"Edad al retiro irreal: {age_at_retire:.1f} años"
                })

    return issues

# Validar
consistency_issues = validate_logical_consistency(employees)
for issue in consistency_issues:
    print(f"Employee {issue['employee_id']}: {issue['issue']}")
```

---

### 4. **Timeliness (Oportunidad)**

**Definition:** Data is available when needed and represents the correct time period.

**Preguntas Clave:**
- Is the data up to date?
- Are there delays in intake?
- Does the data represent the correct period?

**Ejemplos de Problemas:**
```python
from datetime import datetime, timedelta

# ❌ Problemas de oportunidad
data_lake_records = pd.DataFrame({
    'record_id': [1, 2, 3, 4, 5],
    'event_timestamp': [
        datetime.now() - timedelta(hours=1),
        datetime.now() - timedelta(days=7),    # Dato viejo
        datetime.now() - timedelta(hours=2),
        datetime.now() - timedelta(days=30),   # Muy viejo
        datetime.now() - timedelta(minutes=10)
    ],
    'ingestion_timestamp': [
        datetime.now(),
        datetime.now(),
        datetime.now(),
        datetime.now(),
        datetime.now()
    ]
})

def analyze_timeliness(df: pd.DataFrame) -> Dict:
    """Analiza la oportunidad de los datos."""
    current_time = datetime.now()

    # Calcular latencia (diferencia entre evento e ingesta)
    df['latency'] = (df['ingestion_timestamp'] - df['event_timestamp']
                     ).dt.total_seconds() / 3600  # en hours

    # Calcular edad de los datos
    df['data_age'] = (current_time - df['event_timestamp']
                      ).dt.total_seconds() / 3600  # en hours

    analysis = {
        'avg_latency_hours': df['latency'].mean(),
        'max_latency_hours': df['latency'].max(),
        'avg_data_age_hours': df['data_age'].mean(),
        'records_older_than_24h': (df['data_age'] > 24).sum(),
        'records_older_than_7days': (df['data_age'] > 168).sum(),
        'sla_compliance_rate': ((df['latency'] < 4).sum() / len(df) * 100)  # SLA: 4h
    }

    return analysis

# Analizar
timeliness_report = analyze_timeliness(data_lake_records)
print(f"Latencia promedio: {timeliness_report['avg_latency_hours']:.2f}h")
print(f"Compliance con SLA (4h): {timeliness_report['sla_compliance_rate']:.1f}%")
```

**Monitoreo de Freshness:**
```python
def check_data_freshness(df: pd.DataFrame,
                         timestamp_col: str,
                         max_age_hours: int = 24) -> Dict:
    """Verify que los datos sean recientes."""
    current_time = datetime.now()
    latest_record = pd.to_datetime(df[timestamp_col]).max()

    data_age_hours = (current_time - latest_record).total_seconds() / 3600

    return {
        'latest_record': latest_record,
        'age_hours': data_age_hours,
        'is_fresh': data_age_hours <= max_age_hours,
        'status': 'OK' if data_age_hours <= max_age_hours else 'STALE'
    }

# Uso
freshness = check_data_freshness(data_lake_records, 'event_timestamp', max_age_hours=24)
print(f"Estado de frescura: {freshness['status']}")
print(f"Último registro hace: {freshness['age_hours']:.1f} hours")
```

---

### 5. **Validity (Validez)**

**Definition:** The data complies with defined business rules, formats and restrictions.

**Preguntas Clave:**
- Are the values ​​in the allowed domain?
- Are the formats correct?
- Are business rules followed?

**Tipos de Validaciones:**

**5.1 Domain Validation:**
```python
# Definir dominios válidos
VALID_DOMAINS = {
    'status': ['active', 'inactive', 'pending', 'suspended'],
    'country': ['US', 'CA', 'MX', 'UK', 'DE', 'FR'],
    'payment_method': ['credit_card', 'debit_card', 'paypal', 'bank_transfer'],
    'priority': ['low', 'medium', 'high', 'critical']
}

def validate_domain(df: pd.DataFrame,
                   column: str,
                   valid_values: List) -> pd.DataFrame:
    """Validate que los valores estén en el dominio permitido."""
    invalid_records = df[~df[column].isin(valid_values)]

    if len(invalid_records) > 0:
        print(f"❌ {len(invalid_records)} valores inválidos en '{column}':")
        print(invalid_records[[column]].value_counts())
    else:
        print(f"✅ Todos los valores de '{column}' son válidos")

    return invalid_records

# Uso
validate_domain(transactions, 'status', VALID_DOMAINS['status'])
```

**5.2 Range Validation:**
```python
def validate_range(df: pd.DataFrame,
                   column: str,
                   min_val: float = None,
                   max_val: float = None) -> pd.DataFrame:
    """Validate que los valores estén en el rango permitido."""
    conditions = []

    if min_val is not None:
        conditions.append(df[column] < min_val)
    if max_val is not None:
        conditions.append(df[column] > max_val)

    if conditions:
        invalid_mask = pd.concat(conditions, axis=1).any(axis=1)
        invalid_records = df[invalid_mask]

        if len(invalid_records) > 0:
            print(f"❌ {len(invalid_records)} valores fuera de rango en '{column}':")
            print(f"   Rango válido: [{min_val}, {max_val}]")
            print(f"   Min encontrado: {df[column].min()}")
            print(f"   Max encontrado: {df[column].max()}")
        else:
            print(f"✅ Todos los valores de '{column}' están en rango")

        return invalid_records

    return pd.DataFrame()

# Uso
validate_range(transactions, 'amount', min_val=0, max_val=100000)
validate_range(customers, 'age', min_val=0, max_val=120)
```

**5.3 Format Validation:**
```python
import re

REGEX_PATTERNS = {
    'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    'phone_us': r'^\+?1?[\s.-]?\(?[2-9]\d{2}\)?[\s.-]?\d{3}[\s.-]?\d{4}$',
    'zipcode_us': r'^\d{5}(-\d{4})?$',
    'ssn_us': r'^\d{3}-\d{2}-\d{4}$',
    'credit_card': r'^\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}$',
    'ipv4': r'^(\d{1,3}\.){3}\d{1,3}$',
    'url': r'^https?://[^\s/$.?#].[^\s]*$'
}

def validate_format(df: pd.DataFrame,
                    column: str,
                    pattern_name: str) -> pd.DataFrame:
    """Validate que los valores cumplan un formato específico."""
    pattern = REGEX_PATTERNS.get(pattern_name)

    if not pattern:
        raise ValueError(f"Patrón '{pattern_name}' no encontrado")

    def matches_pattern(value):
        if pd.isna(value):
            return True  # Skip nulls
        return bool(re.match(pattern, str(value)))

    mask = df[column].apply(matches_pattern)
    invalid_records = df[~mask]

    if len(invalid_records) > 0:
        print(f"❌ {len(invalid_records)} valores con formato inválido en '{column}':")
        print(invalid_records[[column]].head())
    else:
        print(f"✅ Todos los valores de '{column}' tienen formato válido")

    return invalid_records

# Uso
validate_format(customers, 'email', 'email')
validate_format(customers, 'phone', 'phone_us')
```

**5.4 Business Rule Validation:**
```python
class BusinessRuleValidator:
    """Validate reglas de negocio complejas."""

    @staticmethod
    def rule_order_amount_with_discount(row):
        """Regla: Si hay descuento, el total debe ser menor al subtotal."""
        if row['discount'] > 0:
            return row['total'] < row['subtotal']
        return row['total'] == row['subtotal']

    @staticmethod
    def rule_employee_age_vs_experience(row):
        """Regla: Años de experiencia no pueden exceder edad - 18."""
        max_experience = row['age'] - 18
        return row['years_experience'] <= max_experience

    @staticmethod
    def rule_shipping_cost(row):
        """Regla: Free shipping para orders > $100."""
        if row['order_total'] >= 100:
            return row['shipping_cost'] == 0
        return row['shipping_cost'] > 0

    @classmethod
    def validate_all_rules(cls, df: pd.DataFrame, rules: List[str]) -> pd.DataFrame:
        """Aplica múltiples reglas de negocio."""
        results = []

        for rule_name in rules:
            rule_func = getattr(cls, rule_name, None)
            if rule_func:
                mask = df.apply(rule_func, axis=1)
                violations = df[~mask]
                results.append({
                    'rule': rule_name,
                    'violations': len(violations),
                    'records': violations
                })

        return results

# Uso
validator = BusinessRuleValidator()
rules = [
    'rule_order_amount_with_discount',
    'rule_employee_age_vs_experience',
    'rule_shipping_cost'
]
violations = validator.validate_all_rules(orders_df, rules)

for v in violations:
    if v['violations'] > 0:
        print(f"❌ {v['rule']}: {v['violations']} violaciones")
```

---

### 6. **Uniqueness (Unicidad)**

**Definition:** The data does not contain unnecessary duplicates.

**Preguntas Clave:**
- Are there duplicate records?
- Are the IDs unique?
- Are the duplicates legitimate or errors?

**Duplicate Detection:**

**6.1 Duplicados Exactos:**
```python
def detect_exact_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Detecta duplicados exactos (todas las columnas iguales)."""
    duplicates = df[df.duplicated(keep=False)]

    if len(duplicates) > 0:
        print(f"❌ {len(duplicates)} registros duplicados encontrados")
        print(f"   {df.duplicated().sum()} duplicados (excluyendo primera ocurrencia)")

        # Agrupar duplicados
        duplicate_groups = duplicates.groupby(list(df.columns)).size().reset_index(name='count')
        print(f"\n   {len(duplicate_groups)} grupos de duplicados")
    else:
        print("✅ No se encontraron duplicados exactos")

    return duplicates

# Uso
exact_dupes = detect_exact_duplicates(customers)
```

**6.2 Duplicados por Clave:**
```python
def detect_key_duplicates(df: pd.DataFrame, key_columns: List[str]) -> pd.DataFrame:
    """Detecta duplicados basados en columnas clave."""
    duplicates = df[df.duplicated(subset=key_columns, keep=False)]

    if len(duplicates) > 0:
        print(f"❌ {len(duplicates)} registros con claves duplicadas: {key_columns}")

        # Mostrar ejemplos
        for key_vals, group in duplicates.groupby(key_columns):
            if len(group) > 1:
                print(f"\n   Clave duplicada: {dict(zip(key_columns, key_vals))}")
                print(f"   {len(group)} ocurrencias")
                print(group.head(2))
    else:
        print(f"✅ No hay duplicados en claves: {key_columns}")

    return duplicates

# Uso
key_dupes = detect_key_duplicates(customers, ['email'])
key_dupes = detect_key_duplicates(transactions, ['transaction_id'])
```

**6.3 Duplicados Fuzzy (Aproximados):**
```python
from difflib import SequenceMatcher

def fuzzy_duplicates(df: pd.DataFrame,
                     column: str,
                     threshold: float = 0.85) -> List[tuple]:
    """Detecta duplicados aproximados usando similitud de strings."""
    duplicates = []
    values = df[column].dropna().unique()

    for i, val1 in enumerate(values):
        for val2 in values[i+1:]:
            similarity = SequenceMatcher(None, str(val1), str(val2)).ratio()
            if similarity >= threshold:
                duplicates.append({
                    'value1': val1,
                    'value2': val2,
                    'similarity': similarity,
                    'count1': (df[column] == val1).sum(),
                    'count2': (df[column] == val2).sum()
                })

    return duplicates

# Uso
fuzzy_dupes = fuzzy_duplicates(customers, 'name', threshold=0.90)
for dupe in fuzzy_dupes:
    print(f"Posible duplicado: '{dupe['value1']}' ≈ '{dupe['value2']}' "
          f"(similitud: {dupe['similarity']:.2%})")
```

**Deduplication:**
```python
def deduplicate_dataframe(df: pd.DataFrame,
                          subset: List[str] = None,
                          keep: str = 'first',
                          priority_column: str = None) -> pd.DataFrame:
    """
    Elimina duplicados con estrategias avanzadas.

    Args:
        subset: Columnas para identificar duplicados
        keep: 'first', 'last', o 'priority'
        priority_column: Columna para priorizar (ej: timestamp más reciente)
    """
    if keep == 'priority' and priority_column:
        # Ordenar por prioridad antes de eliminar duplicados
        df_sorted = df.sort_values(priority_column, ascending=False)
        df_deduped = df_sorted.drop_duplicates(subset=subset, keep='first')
    else:
        df_deduped = df.drop_duplicates(subset=subset, keep=keep)

    removed = len(df) - len(df_deduped)
    print(f"Registros originales: {len(df)}")
    print(f"Duplicados eliminados: {removed}")
    print(f"Registros finales: {len(df_deduped)}")

    return df_deduped

# Uso
# Mantener registro más reciente en caso de duplicados
deduped = deduplicate_dataframe(
    transactions,
    subset=['customer_id', 'product_id'],
    keep='priority',
    priority_column='timestamp'
)
```

---

## Data Profiling

Data profiling is the process of examining data to understand its structure, content and quality.

### Profiling Techniques

**1. Statistical Profiling:**
```python
def statistical_profile(df: pd.DataFrame, column: str) -> Dict:
    """Genera perfil estadístico de una columna numérica."""
    series = df[column]

    return {
        'count': series.count(),
        'missing': series.isna().sum(),
        'missing_pct': (series.isna().sum() / len(series)) * 100,
        'unique': series.nunique(),
        'mean': series.mean(),
        'std': series.std(),
        'min': series.min(),
        '25%': series.quantile(0.25),
        'median': series.median(),
        '75%': series.quantile(0.75),
        'max': series.max(),
        'skewness': series.skew(),
        'kurtosis': series.kurt()
    }

# Uso
profile = statistical_profile(transactions, 'amount')
for key, value in profile.items():
    print(f"{key:15s}: {value}")
```

**2. Categorical Profiling:**
```python
def categorical_profile(df: pd.DataFrame, column: str, top_n: int = 10) -> Dict:
    """Genera perfil de una columna categórica."""
    series = df[column]
    value_counts = series.value_counts()

    return {
        'count': series.count(),
        'missing': series.isna().sum(),
        'unique': series.nunique(),
        'cardinality_ratio': series.nunique() / len(series),
        'mode': series.mode()[0] if not series.mode().empty else None,
        'top_values': value_counts.head(top_n).to_dict(),
        'distribution_entropy': -(value_counts / len(series) *
                                  np.log(value_counts / len(series))).sum()
    }
```

**3. Profiling Completo con ydata-profiling:**
```python
from ydata_profiling import ProfileReport

def generate_full_profile(df: pd.DataFrame, output_file: str = 'report.html'):
    """Genera reporte completo de profiling."""
    profile = ProfileReport(
        df,
        title="Data Quality Report",
        explorative=True,
        correlations={
            "pearson": {"calculate": True},
            "spearman": {"calculate": True},
        }
    )

    profile.to_file(output_file)
    print(f"Reporte generado: {output_file}")

    return profile

# Uso
profile = generate_full_profile(transactions, 'transactions_profile.html')
```

---

## Validation Strategies

### 1. Input Validation

**Fail Fast:** Reject invalid data at the entry point.

```python
class DataIngestor:
    """Validator para datos entrantes."""

    def __init__(self, schema: Dict):
        self.schema = schema
        self.validation_errors = []

    def validate_record(self, record: Dict) -> bool:
        """Validate un registro contra schema."""
        errors = []

        # Validar campos requeridos
        required_fields = [k for k, v in self.schema.items()
                          if v.get('required', False)]
        for field in required_fields:
            if field not in record or record[field] is None:
                errors.append(f"Campo required faltante: {field}")

        # Validar tipos
        for field, rules in self.schema.items():
            if field in record and record[field] is not None:
                value = record[field]
                expected_type = rules.get('type')

                if expected_type and not isinstance(value, expected_type):
                    errors.append(f"{field}: tipo inválido (esperado: {expected_type})")

                # Validar rango
                if 'min' in rules and value < rules['min']:
                    errors.append(f"{field}: valor < mínimo ({rules['min']})")
                if 'max' in rules and value > rules['max']:
                    errors.append(f"{field}: valor > máximo ({rules['max']})")

        if errors:
            self.validation_errors.extend(errors)
            return False

        return True

    def ingest(self, records: List[Dict]) -> tuple:
        """Ingesta datos con validation."""
        valid_records = []
        invalid_records = []

        for record in records:
            if self.validate_record(record):
                valid_records.append(record)
            else:
                invalid_records.append(record)

        return valid_records, invalid_records

# Schema definition
transaction_schema = {
    'transaction_id': {'type': int, 'required': True},
    'customer_id': {'type': int, 'required': True},
    'amount': {'type': float, 'required': True, 'min': 0, 'max': 1000000},
    'timestamp': {'type': str, 'required': True}
}

# Uso
ingestor = DataIngestor(transaction_schema)
valid, invalid = ingestor.ingest(incoming_transactions)
print(f"Válidos: {len(valid)}, Inválidos: {len(invalid)}")
```

### 2. Validation in Transformation (pipeline Validation)

```python
class DataPipeline:
    """Pipeline con validaciones en cada etapa."""

    def __init__(self):
        self.validations = []
        self.data = None

    def load(self, data: pd.DataFrame) -> 'DataPipeline':
        """Carga datos."""
        self.data = data.copy()
        return self

    def validate(self, name: str, func: callable) -> 'DataPipeline':
        """Agrega validation."""
        if self.data is None:
            raise ValueError("No hay datos cargados")

        try:
            result = func(self.data)
            self.validations.append({
                'step': name,
                'status': 'PASS' if result else 'FAIL',
                'message': getattr(result, 'message', 'OK')
            })

            if not result:
                raise ValueError(f"Validation fallida: {name}")
        except Exception as e:
            self.validations.append({
                'step': name,
                'status': 'ERROR',
                'message': str(e)
            })
            raise

        return self

    def transform(self, func: callable) -> 'DataPipeline':
        """Aplica transformación."""
        self.data = func(self.data)
        return self

    def get_results(self) -> tuple:
        """Retorna datos y reporte de validaciones."""
        return self.data, self.validations

# Uso
pipeline = (
    DataPipeline()
    .load(raw_data)
    .validate('no_nulls_in_id', lambda df: df['id'].notna().all())
    .validate('amounts_positive', lambda df: (df['amount'] > 0).all())
    .transform(lambda df: df.drop_duplicates())
    .validate('unique_ids', lambda df: df['id'].nunique() == len(df))
    .transform(lambda df: df[df['amount'] <= 100000])
)

clean_data, validation_report = pipeline.get_results()
```

### 3. Output Validation

```python
def validate_output(df: pd.DataFrame, expectations: Dict) -> Dict:
    """Validate datos de salida antes de escribir."""
    results = {
        'passed': True,
        'checks': []
    }

    # Row count
    if 'min_rows' in expectations:
        check = len(df) >= expectations['min_rows']
        results['checks'].append({
            'check': 'min_rows',
            'passed': check,
            'expected': expectations['min_rows'],
            'actual': len(df)
        })
        results['passed'] &= check

    # Schema
    if 'required_columns' in expectations:
        missing_cols = set(expectations['required_columns']) - set(df.columns)
        check = len(missing_cols) == 0
        results['checks'].append({
            'check': 'required_columns',
            'passed': check,
            'missing': list(missing_cols)
        })
        results['passed'] &= check

    # Quality thresholds
    if 'max_null_percentage' in expectations:
        null_pct = (df.isnull().sum().sum() / (df.shape[0] * df.shape[1])) * 100
        check = null_pct <= expectations['max_null_percentage']
        results['checks'].append({
            'check': 'null_percentage',
            'passed': check,
            'threshold': expectations['max_null_percentage'],
            'actual': null_pct
        })
        results['passed'] &= check

    return results

# Uso
output_expectations = {
    'min_rows': 1000,
    'required_columns': ['id', 'amount', 'timestamp'],
    'max_null_percentage': 5.0
}

validation_result = validate_output(final_data, output_expectations)
if validation_result['passed']:
    final_data.to_parquet('output.parquet')
    print("✅ Datos validados y guardados")
else:
    print("❌ Validation de salida fallida")
    for check in validation_result['checks']:
        if not check['passed']:
            print(f"   - {check}")
```

---

## Data Quality Metrics

### Quality KPIs

```python
class DataQualityMetrics:
    """Calcula métricas de calidad de datos."""

    @staticmethod
    def completeness_score(df: pd.DataFrame) -> float:
        """% de celdas con datos."""
        total_cells = df.shape[0] * df.shape[1]
        non_null_cells = df.notna().sum().sum()
        return (non_null_cells / total_cells) * 100

    @staticmethod
    def uniqueness_score(df: pd.DataFrame, key_column: str) -> float:
        """% de registros únicos por clave."""
        total = len(df)
        unique = df[key_column].nunique()
        return (unique / total) * 100

    @staticmethod
    def validity_score(df: pd.DataFrame, validation_func: callable) -> float:
        """% de registros que pasan validation."""
        results = df.apply(validation_func, axis=1)
        return (results.sum() / len(df)) * 100

    @staticmethod
    def consistency_score(df: pd.DataFrame, rule_funcs: List[callable]) -> float:
        """% de registros que pasan todas las reglas."""
        all_passed = pd.Series([True] * len(df))

        for rule_func in rule_funcs:
            all_passed &= df.apply(rule_func, axis=1)

        return (all_passed.sum() / len(df)) * 100

    @classmethod
    def overall_quality_score(cls, df: pd.DataFrame,
                             key_column: str,
                             validation_func: callable,
                             consistency_rules: List[callable],
                             weights: Dict = None) -> Dict:
        """Score global de calidad (weighted)."""
        # Pesos por defecto
        if weights is None:
            weights = {
                'completeness': 0.25,
                'uniqueness': 0.20,
                'validity': 0.30,
                'consistency': 0.25
            }

        scores = {
            'completeness': cls.completeness_score(df),
            'uniqueness': cls.uniqueness_score(df, key_column),
            'validity': cls.validity_score(df, validation_func),
            'consistency': cls.consistency_score(df, consistency_rules)
        }

        # Score global ponderado
        overall = sum(scores[dim] * weights[dim] for dim in scores)

        return {
            'scores': scores,
            'weights': weights,
            'overall_score': overall,
            'grade': cls._get_grade(overall)
        }

    @staticmethod
    def _get_grade(score: float) -> str:
        """Convierte score a grado."""
        if score >= 95:
            return 'A+'
        elif score >= 90:
            return 'A'
        elif score >= 85:
            return 'B+'
        elif score >= 80:
            return 'B'
        elif score >= 75:
            return 'C+'
        elif score >= 70:
            return 'C'
        else:
            return 'F'

# Uso
metrics = DataQualityMetrics()
quality_report = metrics.overall_quality_score(
    df=transactions,
    key_column='transaction_id',
    validation_func=lambda row: row['amount'] > 0,
    consistency_rules=[
        lambda row: row['amount'] == row['subtotal'] - row['discount'],
        lambda row: pd.to_datetime(row['timestamp check']) <= datetime.now()
    ]
)

print(f"Overall Quality Score: {quality_report['overall_score']:.1f}% ({quality_report['grade']})")
for dim, score in quality_report['scores'].items():
    print(f"  {dim:15s}: {score:5.1f}%")
```

---

## Best Practices

### 1. Establecer Data Quality Framework

```
Definir → Medir → Monitorear → Mejorar
```

**Steps:**
1. **Define critical dimensions** for your domain
2. **Establecer thresholds** aceptables
3. **Implement automatic validations**
4. **monitor continuamente**
5. **Iterar y mejorar**

### 2. Shift Left (Early Validation)

Validate as early as possible in the pipeline:
- **Input validation**: En el punto de ingesta
- **Schema enforcement**: Al escribir a storage
- **pipeline checkpoints**: Between transformation stages

### 3. Automation

```python
# ❌ Mal: Validation manual
# Revisar datos manualmente en Excel
# Depender de usuarios para reportar problemas

# ✅ Bien: Validation automatizada
def automated_quality_check(data_path: str):
    """Quality check automatizado que se ejecuta en cada run."""
    df = pd.read_parquet(data_path)

    # Suite de validaciones
    checks = [
        ('completeness', check_completeness(df)),
        ('duplicates', check_duplicates(df)),
        ('validity', check_validity(df)),
        ('freshness', check_freshness(df))
    ]

    # Si algún check falla, detener pipeline
    failed = [name for name, result in checks if not result]
    if failed:
        raise DataQualityException(f"Failed checks: {failed}")

    return True
```

### 4. Data Quality SLAs

Establish Service Level Agreements for quality:

```python
DATA_QUALITY_SLAS = {
    'completeness': {
        'threshold': 95.0,
        'critical_columns': ['customer_id', 'amount', 'timestamp']
    },
    'accuracy': {
        'threshold': 99.0,
        'validation_rules': ['valid_email', 'valid_phone', 'valid_amount']
    },
    'timeliness': {
        'max_latency_hours': 4,
        'max_age_hours': 24
    },
    'uniqueness': {
        'duplicate_threshold': 0.1  # Max 0.1% duplicates
    }
}

def check_sla_compliance(df: pd.DataFrame, slas: Dict) -> Dict:
    """Verify compliance con SLAs de calidad."""
    results = {}

    for dimension, sla in slas.items():
        if dimension == 'completeness':
            score = calculate_completeness(df, sla['critical_columns'])
            results[dimension] = {
                'score': score,
                'threshold': sla['threshold'],
                'compliant': score >= sla['threshold']
            }

    # Alerta si no hay compliance
    non_compliant = [d for d, r in results.items() if not r['compliant']]
    if non_compliant:
        send_alert(f"SLA violation: {non_compliant}")

    return results
```

### 5. Quality Documentation

Mantener un **data quality catalog**:

```yaml
# data_quality_catalog.yaml
datasets:
  transactions:
    owner: data-engineering-team
    quality_dimensions:
      completeness:
        target: 98%
        critical_columns: [transaction_id, amount, customer_id]
      accuracy:
        validations:
          - amount > 0
          - amount < 1000000
          - valid_timestamp
      timeliness:
        max_age: 24h
        refresh_frequency: hourly
    known_issues:
      - "~2% of transactions missing customer_id (guest checkouts)"
      - "Amounts rounded to 2 decimals"
    last_validated: 2024-01-15T10:30:00Z
```

---

## Common Quality Issues & Solutions

| Issue | Detection | Solution |
|-------|-----------|----------|
| **Missing Values** | `df.isnull().sum()` | Imputation, deletion, or flagging |
| **Duplicates** | `df.duplicated()` | Deduplication with priority rules |
| **Inconsistent Formats** | Regex validation | Standardization functions |
| **Outliers** | IQR, Z-score | Capping, transformation, or flagging |
| **Invalid References** | Foreign key checks | Cleanup or cascading deletes |
| **Stale Data** | Timestamp analysis | Automated refresh, alerting |
| **Schema Drift** | Schema comparison | Schema evolution strategy |
| **Data Type Mismatches** | Type inference | Explicit type casting |

---

## Testing Data Quality

### Unit Tests para Validaciones

```python
import pytest

def test_no_negative_amounts():
    df = pd.DataFrame({'amount': [10, 20, 30]})
    assert (df['amount'] > 0).all()

def test_all_emails_valid():
    df = pd.DataFrame({'email': ['a@b.com', 'x@y.org']})
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    assert df['email'].str.match(email_pattern).all()

def test_completeness_threshold():
    df = pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'value': [10, None, 30, 40, 50]
    })
    completeness = df['value'].notna().sum() / len(df)
    assert completeness >= 0.80, f"Completeness {completeness} below 80% threshold"
```

---

## Conclusion

Data quality is a continuous process that requires:
1. **Clear definition** of dimensions and metrics
2. **Validaciones automatizadas** en todo el pipeline
3. **Proactive monitoring** with alerts
4. **Constant iteration** based on feedback

In the following files we will explore specific frameworks such as **Great Expectations** and architectures to implement data quality at an enterprise scale.

---

## Next Steps

➡️ **theory/02-architecture.md**: Arquitecturas y frameworks de Data Quality
➡️ **theory/03-resources.md**: Herramientas y resources adicionales
