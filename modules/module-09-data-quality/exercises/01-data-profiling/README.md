# Exercise 01: Data Profiling

⏱️ **Estimated duration:** 1.5-2 hours
⭐ **Difficulty:** Basic

## 🎯 Goals

By completing this exercise, you will be able to:
- Analyze datasets to understand their structure and content
- Identify basic quality problems (nulls, duplicates,

 outliers)
- Generate automatic profiling reports
- Calculate descriptive statistical metrics
- Visualize data distributions

## 📚 Conceptos Clave

- **Data Profiling**: Process of examining data to understand structure, content and quality
- **Descriptive Statistics**: Mean, median, std dev, quartiles
- **Data Distribution**: Normal, skewed, multimodal
- **Cardinality**: Number of unique values ​​in a column
- **Missing Data Patterns**: MAR, MCAR, MNAR

## 📁 Archivos

```
exercises/01-data-profiling/
├── README.md                    # Este archivo
├── solution.py                  # Solution completa
└── exercises.ipynb              # Notebook con exercises
```

## 🚀 Setup

```bash
# Asegúrate de tener las dependencias instaladas
pip install pandas numpy ydata-profiling matplotlib seaborn

# Genera los datos de muestra
cd ../../
python data/scripts/generate_data.py --quality poor

# Abre el notebook
jupyter notebook exercises/01-data-profiling/exercises.ipynb
```

## 📝 Exercises

### Parte 1: Profiling Manual con Pandas

**Goal**: Implement profiling functions from scratch.

```python
import pandas as pd
import numpy as np

# Cargar datos
customers = pd.read_csv('../../data/samples/customers_poor.csv')
transactions = pd.read_csv('../../data/samples/transactions_poor.csv')
products = pd.read_csv('../../data/samples/products_poor.csv')
```

**Task 1.1: Profiling de Dataset Completo**

Implement a function that generates a basic profiling report:

```python
def profile_dataset(df: pd.DataFrame, name: str) -> dict:
    """
    Genera perfil básico de un DataFrame.

    Returns:
        dict con keys: name, rows, columns, missing_cells,
                      missing_percentage, duplicates, memory_mb
    """
    # TODO: Implementar
    pass

# Uso
profile = profile_dataset(customers, "Customers")
print(profile)
```

**Expected Output:**
```
{
    'name': 'Customers',
    'rows': 10000,
    'columns': 11,
    'missing_cells': 8250,
    'missing_percentage': 7.5,
    'duplicates': 800,
    'memory_mb': 0.85
}
```

**Task 1.2: Profiling por column**

Implement detailed analysis by column:

```python
def profile_column(df: pd.DataFrame, column: str) -> dict:
    """
    Genera perfil detallado de una columna.

    Returns:
        dict con stats relevantes según tipo de dato
    """
    series = df[column]

    profile = {
        'column': column,
        'dtype': str(series.dtype),
        'count': series.count(),
        'missing': series.isna().sum(),
        'missing_pct': (series.isna().sum() / len(series)) * 100,
        'unique': series.nunique(),
        'cardinality_ratio': series.nunique() / len(series)
    }

    # Para columnas numéricas
    if pd.api.types.is_numeric_dtype(series):
        # TODO: Agregar stats numéricas (mean, std, min, max, quartiles)
        pass

    # Para columnas categóricas
    elif pd.api.types.is_object_dtype(series):
        # TODO: Agregar stats categóricas (mode, top values)
        pass

    return profile

# Uso
email_profile = profile_column(customers, 'email')
amount_profile = profile_column(transactions, 'amount')
```

**Task 1.3: Detectar Outliers**

Implements outlier detection using IQR and Z-score:

```python
def detect_outliers_iqr(df: pd.DataFrame, column: str, multiplier: float = 1.5) -> pd.DataFrame:
    """
    Detecta outliers usando método IQR (Interquartile Range).

    Args:
        column: Columna numérica a analizar
        multiplier: Multiplicador de IQR (típicamente 1.5 o 3.0)

    Returns:
        DataFrame con outliers detectados
    """
    # TODO: Implementar
    # Q1 = percentil 25
    # Q3 = percentil 75
    # IQR = Q3 - Q1
    # Lower bound = Q1 - multiplier * IQR
    # Upper bound = Q3 + multiplier * IQR
    pass

def detect_outliers_zscore(df: pd.DataFrame, column: str, threshold: float = 3.0) -> pd.DataFrame:
    """
    Detecta outliers usando Z-score.

    Args:
        column: Columna numérica a analizar
        threshold: Umbral de Z-score (típicamente 3.0)

    Returns:
        DataFrame con outliers detectados
    """
    from scipy import stats
    # TODO: Implementar
    pass

# Uso
outliers_iqr = detect_outliers_iqr(transactions, 'amount')
outliers_zscore = detect_outliers_zscore(transactions, 'amount', threshold=3.0)

print(f"Outliers por IQR: {len(outliers_iqr)}")
print(f"Outliers por Z-score: {len(outliers_zscore)}")
```

**Task 1.4: Missing Data Analysis**

Analyze patterns of missing data:

```python
def analyze_missing_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analiza patrones de missing data.

    Returns:
        DataFrame con columnas: column, missing_count, missing_pct,
                                missing_pattern
    """
    # TODO: Implementar
    # Para cada columna, calcular:
    # - Total de missing values
    # - Porcentaje de missing
    # - Pattern (MCAR, MAR, MNAR - simplificado)
    pass

# Visualizar missing data
import matplotlib.pyplot as plt
import seaborn as sns

def visualize_missing(df: pd.DataFrame):
    """Visualiza distribución de missing values."""
    missing_matrix = df.isnull()

    plt.figure(figsize=(12, 6))
    sns.heatmap(missing_matrix, cbar=False, yticklabels=False, cmap='viridis')
    plt.title('Missing Values Heatmap')
    plt.xlabel('Columns')
    plt.ylabel('Rows')
    plt.show()

visualize_missing(customers)
```

---

### Part 2: Automatic Profiling

**Goal**: Use ydata-profiling to generate complete reports.

**Task 2.1: Generar Reporte HTML**

```python
from ydata_profiling import ProfileReport

# Generar reporte
profile = ProfileReport(
    customers,
    title="Customers Data Quality Report",
    explorative=True,
    minimal=False
)

# Guardar reporte
profile.to_file("customers_profile.html")

# Abrir en navegador
import webbrowser
webbrowser.open("customers_profile.html")
```

**Task 2.2: Comparar Datasets**

Compare datasets with different quality levels:

```python
# Generar datasets de diferentes calidades
import subprocess

subprocess.run(["python", "../../data/scripts/generate_data.py", "--quality", "clean"])
subprocess.run(["python", "../../data/scripts/generate_data.py", "--quality", "poor"])

# Cargar ambos
customers_clean = pd.read_csv('../../data/samples/customers_clean.csv')
customers_poor = pd.read_csv('../../data/samples/customers_poor.csv')

# Comparar
from ydata_profiling import compare

clean_profile = ProfileReport(customers_clean, title="Clean")
poor_profile = ProfileReport(customers_poor, title="Poor")

comparison = compare([clean_profile, poor_profile])
comparison.to_file("comparison_report.html")
```

---

### Part 3: Viewing Distributions

**Objective**: Visualize distributions to identify anomalies.

**Task 3.1: Histogramas**

```python
def plot_distributions(df: pd.DataFrame, numeric_columns: list):
    """Plotea distribuciones de columnas numéricas."""
    n_cols = len(numeric_columns)
    fig, axes = plt.subplots(n_cols, 2, figsize=(15, n_cols * 3))

    for i, col in enumerate(numeric_columns):
        # Histogram
        axes[i, 0].hist(df[col].dropna(), bins=50, edgecolor='black')
        axes[i, 0].set_title(f'{col} - Distribution')
        axes[i, 0].set_xlabel(col)
        axes[i, 0].set_ylabel('Frequency')

        # Box plot
        axes[i, 1].boxplot(df[col].dropna())
        axes[i, 1].set_title(f'{col} - Box Plot')
        axes[i, 1].set_ylabel(col)

    plt.tight_layout()
    plt.show()

# Uso
numeric_cols = ['amount', 'quantity', 'total']
plot_distributions(transactions, numeric_cols)
```

**Task 3.2: Correlation Matrix**

```python
def plot_correlation_matrix(df: pd.DataFrame):
    """Plotea matriz de correlación."""
    # Select numeric columns only
    numeric_df = df.select_dtypes(include=[np.number])

    # Calculate correlation
    corr = numeric_df.corr()

    # Plot
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr, annot=True, cmap='coolwarm', center=0,
                square=True, linewidths=1, cbar_kws={"shrink": 0.8})
    plt.title('Correlation Matrix')
    plt.tight_layout()
    plt.show()

plot_correlation_matrix(transactions)
```

---

### Parte 4: Profiling Report Custom

**Objective**: Create your own consolidated profiling report.

**Task 4.1: Clase ProfilerReport**

```python
class DataQualityProfiler:
    """Profiler personalizado para análisis de calidad."""

    def __init__(self, df: pd.DataFrame, name: str):
        self.df = df
        self.name = name
        self.report = {}

    def run_full_profile(self):
        """Execute profiling completo."""
        self.report['overview'] = self._profile_overview()
        self.report['columns'] = self._profile_columns()
        self.report['quality_issues'] = self._detect_quality_issues()
        self.report['recommendations'] = self._generate_recommendations()
        return self.report

    def _profile_overview(self) -> dict:
        """Overview del dataset."""
        # TODO: Implementar
        pass

    def _profile_columns(self) -> list:
        """Perfil de cada columna."""
        # TODO: Implementar
        pass

    def _detect_quality_issues(self) -> dict:
        """Detecta problemas de calidad."""
        issues = {
            'missing_values': {},
            'duplicates': 0,
            'outliers': {},
            'invalid_formats': {}
        }
        # TODO: Implementar detección
        return issues

    def _generate_recommendations(self) -> list:
        """Genera recomendaciones de limpieza."""
        # TODO: Basado en issues, sugerir acciones
        pass

    def print_report(self):
        """Imprime reporte formateado."""
        print("=" * 70)
        print(f"DATA QUALITY PROFILE: {self.name}")
        print("=" * 70)
        # TODO: Formatear y printear cada sección
        pass

# Uso
profiler = DataQualityProfiler(customers, "Customers")
report = profiler.run_full_profile()
profiler.print_report()
```

---

## ✅ Success Criteria

You have successfully completed this exercise if:

- [ ] Implementaste todas las funciones de profiling
- [ ] Generaste reportes HTML con ydata-profiling
- [ ] Identificaste outliers usando IQR y Z-score
- [ ] Visualizaste distribuciones y correlaciones
- [ ] Detectaste patrones de missing data
- [ ] Creaste un reporte de profiling custom

## 🎓 Conceptos Aprendidos

- Manual vs automatic data profiling
- Descriptive statistical metrics
- Outlier detection (IQR, Z-score)
- Missing data analysis
- Viewing distributions
- Correlaciones entre variables

## 📚 Additional Resources

- **ydata-profiling docs**: https://docs.profiling.ydata.ai/
- **Pandas profiling**: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.describe.html
- **Seaborn gallery**: https://seaborn.pydata.org/examples/index.html

## ➡️ Next Exercise

**Exercise 02: Validation Rules** - Implement custom validation rules
