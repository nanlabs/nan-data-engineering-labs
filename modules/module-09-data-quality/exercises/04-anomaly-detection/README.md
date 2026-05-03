# Exercise 04: Anomaly Detection

⏱️ **Estimated duration:** 2-3 hours
⭐⭐⭐ **Difficulty:** Intermediate-Advanced

## 🎯 Goals

- Detect univariate anomalies (outliers)
- Detect multivariate anomalies
- Use statistical methods (IQR, Z-score)
- Use ML methods (Isolation Forest, LOF)
- Identify anomalies in time series
- Create automatic detection system

## 📚 Conceptos Clave

- **Anomaly/Outlier**: Data that deviates significantly from the pattern
- **Univariate**: Anomalies in a single variable
- **Multivariate**: Anomalies in combination of variables
- **Point Anomalies**: Anomalous individual instances
- **Contextual Anomalies**: Anomalous in a certain context (e.g. time of year)
- **Collective Anomalies**: Anomalous sequences

## 📝 Exercises

### Part 1: Statistical Methods

**Task 1.1: IQR Method (Interquartile Range)**

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def detect_outliers_iqr(df: pd.DataFrame, column: str, multiplier: float = 1.5) -> pd.DataFrame:
    """
    Detecta outliers usando método IQR.

    Outliers: valores fuera de [Q1 - 1.5*IQR, Q3 + 1.5*IQR]
    """
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1

    lower_bound = Q1 - multiplier * IQR
    upper_bound = Q3 + multiplier * IQR

    outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]

    print(f"Column: {column}")
    print(f"Q1: {Q1:.2f}, Q3: {Q3:.2f}, IQR: {IQR:.2f}")
    print(f"Bounds: [{lower_bound:.2f}, {upper_bound:.2f}]")
    print(f"Outliers found: {len(outliers)} ({len(outliers)/len(df)*100:.2f}%)")

    return outliers

# Uso
outliers = detect_outliers_iqr(transactions, 'amount', multiplier=1.5)
```

**Task 1.2: Z-Score Method**

```python
from scipy import stats

def detect_outliers_zscore(df: pd.DataFrame, column: str, threshold: float = 3) -> pd.DataFrame:
    """
    Detecta outliers usando Z-score.

    Outliers: |z-score| > threshold (típicamente 3)
    """
    z_scores = np.abs(stats.zscore(df[column].dropna()))

    # Indices con z-score > threshold
    outlier_indices = np.where(z_scores > threshold)[0]
    outliers = df.iloc[outlier_indices]

    print(f"Column: {column}")
    print(f"Mean: {df[column].mean():.2f}, Std: {df[column].std():.2f}")
    print(f"Threshold: {threshold} standard deviations")
    print(f"Outliers found: {len(outliers)} ({len(outliers)/len(df)*100:.2f}%)")

    return outliers

# Uso
outliers = detect_outliers_zscore(transactions, 'amount', threshold=3)
```

**Task 1.3: Visualizar Outliers**

```python
def visualize_outliers(df: pd.DataFrame, column: str):
    """Visualiza distribución y outliers."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    # Box plot
    axes[0].boxplot(df[column].dropna())
    axes[0].set_title(f'{column} - Box Plot')
    axes[0].set_ylabel(column)

    # Histogram
    axes[1].hist(df[column].dropna(), bins=50, edgecolor='black')
    axes[1].set_title(f'{column} - Histogram')
    axes[1].set_xlabel(column)
    axes[1].set_ylabel('Frequency')

    # Q-Q plot (normalidad)
    stats.probplot(df[column].dropna(), dist="norm", plot=axes[2])
    axes[2].set_title(f'{column} - Q-Q Plot')

    plt.tight_layout()
    plt.savefig(f'outliers_{column}.png', dpi=300, bbox_inches='tight')
    plt.show()

visualize_outliers(transactions, 'amount')
```

---

### Part 2: Machine Learning Methods

**Task 2.1: Isolation Forest**

```python
from sklearn.ensemble import IsolationForest

def detect_anomalies_isolation_forest(df: pd.DataFrame,
                                      features: list,
                                      contamination: float = 0.05) -> pd.DataFrame:
    """
    Detecta anomalías usando Isolation Forest.

    Args:
        contamination: Proporción esperada de anomalías (0.05 = 5%)
    """
    # Preparar datos
    X = df[features].dropna()

    # Entrenar modelo
    iso_forest = IsolationForest(
        contamination=contamination,
        random_state=42,
        n_estimators=100
    )

    # Predecir (-1 = anomaly, 1 = normal)
    predictions = iso_forest.fit_predict(X)

    # Scores (más negativo = más anómalo)
    scores = iso_forest.score_samples(X)

    # Agregar al df
    df_copy = df.loc[X.index].copy()
    df_copy['anomaly'] = predictions
    df_copy['anomaly_score'] = scores

    anomalies = df_copy[df_copy['anomaly'] == -1]

    print(f"Features: {features}")
    print(f"Contamination: {contamination}")
    print(f"Anomalies found: {len(anomalies)} ({len(anomalies)/len(df_copy)*100:.2f}%)")

    return anomalies

# Uso - Detección multivariada
anomalies = detect_anomalies_isolation_forest(
    transactions,
    features=['amount', 'quantity', 'total'],
    contamination=0.05
)
```

**Task 2.2: Local Outlier Factor (LOF)**

```python
from sklearn.neighbors import LocalOutlierFactor

def detect_anomalies_lof(df: pd.DataFrame,
                        features: list,
                        n_neighbors: int = 20,
                        contamination: float = 0.05) -> pd.DataFrame:
    """
    Detecta anomalías usando Local Outlier Factor.

    LOF identifica puntos con densidad local baja comparada con vecinos.
    """
    # Preparar datos
    X = df[features].dropna()

    # Entrenar modelo
    lof = LocalOutlierFactor(
        n_neighbors=n_neighbors,
        contamination=contamination
    )

    # Predecir
    predictions = lof.fit_predict(X)

    # Scores (más negativo = más anómalo)
    scores = lof.negative_outlier_factor_

    df_copy = df.loc[X.index].copy()
    df_copy['anomaly'] = predictions
    df_copy['lof_score'] = scores

    anomalies = df_copy[df_copy['anomaly'] == -1]

    print(f"Features: {features}")
    print(f"Neighbors: {n_neighbors}")
    print(f"Anomalies found: {len(anomalies)} ({len(anomalies)/len(df_copy)*100:.2f}%)")

    return anomalies

# Uso
anomalies = detect_anomalies_lof(
    transactions,
    features=['amount', 'quantity', 'total'],
    n_neighbors=20
)
```

**Task 2.3: PyOD Library (multiple algorithms)**

```python
from pyod.models.knn import KNN
from pyod.models.iforest import IForest
from pyod.models.lof import LOF
from pyod.models.ocsvm import OCSVM

class EnsembleAnomalyDetector:
    """Detector de anomalías con ensemble de modelos."""

    def __init__(self, contamination=0.05):
        self.contamination = contamination
        self.models = {
            'IForest': IForest(contamination=contamination),
            'LOF': LOF(contamination=contamination),
            'KNN': KNN(contamination=contamination),
            'OCSVM': OCSVM(contamination=contamination)
        }
        self.results = {}

    def fit_predict(self, X):
        """Entrena todos los modelos y predice."""
        for name, model in self.models.items():
            model.fit(X)
            predictions = model.predict(X)  # 0=normal, 1=anomaly
            scores = model.decision_scores_

            self.results[name] = {
                'predictions': predictions,
                'scores': scores,
                'n_anomalies': np.sum(predictions)
            }

        return self

    def get_consensus(self, threshold=2):
        """
        Anomalías detectadas por al menos 'threshold' modelos.
        """
        predictions_array = np.array([
            r['predictions'] for r in self.results.values()
        ])

        # Contar cuántos modelos detectaron cada punto como anomalía
        votes = np.sum(predictions_array, axis=0)
        consensus_anomalies = votes >= threshold

        return consensus_anomalies

    def print_summary(self):
        """Imprime resumen de detecciones."""
        print("=" * 60)
        print("ANOMALY DETECTION SUMMARY")
        print("=" * 60)

        for name, result in self.results.items():
            n_anomalies = result['n_anomalies']
            print(f"{name:15} : {n_anomalies:6} anomalies")

        consensus = self.get_consensus(threshold=2)
        print(f"{'Consensus (2+)':15} : {np.sum(consensus):6} anomalies")
        print("=" * 60)

# Uso
detector = EnsembleAnomalyDetector(contamination=0.05)
X = transactions[['amount', 'quantity', 'total']].dropna()
detector.fit_predict(X)
detector.print_summary()

# Obtener anomalías de consenso
consensus_mask = detector.get_consensus(threshold=2)
anomalies = transactions.loc[X.index][consensus_mask]
```

---

### Parte 3: Series Temporales

**Task 3.1: Moving Average Method**

```python
def detect_anomalies_moving_average(df: pd.DataFrame,
                                   date_col: str,
                                   value_col: str,
                                   window: int = 7,
                                   std_threshold: float = 3) -> pd.DataFrame:
    """
    Detecta anomalías en serie temporal usando media móvil.
    """
    df = df.sort_values(date_col).copy()

    # Calcular media y desviación móvil
    df['rolling_mean'] = df[value_col].rolling(window=window, center=True).mean()
    df['rolling_std'] = df[value_col].rolling(window=window, center=True).std()

    # Bounds
    df['upper_bound'] = df['rolling_mean'] + std_threshold * df['rolling_std']
    df['lower_bound'] = df['rolling_mean'] - std_threshold * df['rolling_std']

    # Detectar anomalías
    df['is_anomaly'] = (
        (df[value_col] > df['upper_bound']) |
        (df[value_col] < df['lower_bound'])
    )

    anomalies = df[df['is_anomaly'] == True]

    # Visualizar
    plt.figure(figsize=(15, 6))
    plt.plot(df[date_col], df[value_col], label='Value', alpha=0.7)
    plt.plot(df[date_col], df['rolling_mean'], label=f'{window}-day MA', color='blue')
    plt.fill_between(df[date_col], df['lower_bound'], df['upper_bound'],
                     alpha=0.2, label=f'{std_threshold}σ bounds')
    plt.scatter(anomalies[date_col], anomalies[value_col],
               color='red', s=100, label='Anomalies', zorder=5)
    plt.xlabel('Date')
    plt.ylabel(value_col)
    plt.title(f'Anomaly Detection - {value_col}')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('timeseries_anomalies.png', dpi=300, bbox_inches='tight')
    plt.show()

    print(f"Anomalies found: {len(anomalies)}")
    return anomalies

# Agregar transacciones por día
daily_transactions = transactions.groupby('transaction_date').agg({
    'amount': 'sum',
    'transaction_id': 'count'
}).reset_index()
daily_transactions.columns = ['date', 'total_amount', 'n_transactions']

# Detectar anomalías
anomalies = detect_anomalies_moving_average(
    daily_transactions,
    date_col='date',
    value_col='total_amount',
    window=7,
    std_threshold=3
)
```

**Task 3.2: Seasonal Decomposition**

```python
from statsmodels.tsa.seasonal import seasonal_decompose

def detect_anomalies_seasonal(df: pd.DataFrame,
                              date_col: str,
                              value_col: str,
                              period: int = 7) -> pd.DataFrame:
    """
    Detecta anomalías usando descomposición seasonal.
    """
    df = df.sort_values(date_col).set_index(date_col).copy()

    # Decompose
    decomposition = seasonal_decompose(
        df[value_col],
        model='additive',
        period=period
    )

    # Residuos (lo que no explica trend + seasonality)
    residuals = decomposition.resid.dropna()

    # Detectar outliers en residuos
    z_scores = np.abs(stats.zscore(residuals))
    anomalies_mask = z_scores > 3

    anomalies = df.loc[anomalies_mask]

    # Visualizar
    fig, axes = plt.subplots(4, 1, figsize=(15, 10))

    decomposition.observed.plot(ax=axes[0], title='Observed')
    decomposition.trend.plot(ax=axes[1], title='Trend')
    decomposition.seasonal.plot(ax=axes[2], title='Seasonal')
    decomposition.resid.plot(ax=axes[3], title='Residuals')
    axes[3].scatter(anomalies.index, residuals[anomalies_mask],
                   color='red', s=100, zorder=5, label='Anomalies')
    axes[3].legend()

    plt.tight_layout()
    plt.savefig('seasonal_decomposition.png', dpi=300, bbox_inches='tight')
    plt.show()

    print(f"Anomalies found: {len(anomalies)}")
    return anomalies.reset_index()
```

---

### Part 4: Detection System

**Task 4.1: Anomaly Detection pipeline**

```python
from dataclasses import dataclass
from typing import List, Dict, Callable

@dataclass
class AnomalyDetectionRule:
    """Regla de detección de anomalías."""
    name: str
    detector: Callable
    features: List[str]
    severity: str  # 'high', 'medium', 'low'

class AnomalyDetectionPipeline:
    """Pipeline de detección de anomalías."""

    def __init__(self):
        self.rules = []
        self.results = []

    def add_rule(self, rule: AnomalyDetectionRule):
        """Agrega regla de detección."""
        self.rules.append(rule)
        return self

    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ejecuta todas las reglas de detección."""
        df_flagged = df.copy()
        df_flagged['anomaly_flags'] = ''
        df_flagged['anomaly_count'] = 0

        for rule in self.rules:
            print(f"\nRunning: {rule.name}")

            try:
                # Ejecutar detector
                anomalies = rule.detector(df)

                # Flagear anomalías
                anomaly_ids = anomalies.index.tolist()

                for idx in anomaly_ids:
                    if idx in df_flagged.index:
                        current_flags = df_flagged.loc[idx, 'anomaly_flags']
                        df_flagged.loc[idx, 'anomaly_flags'] = (
                            f"{current_flags},{rule.name}" if current_flags else rule.name
                        )
                        df_flagged.loc[idx, 'anomaly_count'] += 1

                # Guardar resultado
                self.results.append({
                    'rule': rule.name,
                    'severity': rule.severity,
                    'n_anomalies': len(anomalies),
                    'percentage': len(anomalies) / len(df) * 100
                })

                print(f"  Found {len(anomalies)} anomalies ({len(anomalies)/len(df)*100:.2f}%)")

            except Exception as e:
                print(f"  Error: {e}")
                self.results.append({
                    'rule': rule.name,
                    'severity': 'error',
                    'error': str(e)
                })

        return df_flagged

    def get_summary(self) -> pd.DataFrame:
        """Retorna resumen de detecciones."""
        return pd.DataFrame(self.results)

    def get_high_risk_anomalies(self, df_flagged: pd.DataFrame, min_flags: int = 2):
        """Retorna anomalías de alto riesgo (detectadas por múltiples reglas)."""
        high_risk = df_flagged[df_flagged['anomaly_count'] >= min_flags]
        return high_risk.sort_values('anomaly_count', ascending=False)

# Uso
pipeline = AnomalyDetectionPipeline()

# Regla 1: IQR en amount
pipeline.add_rule(AnomalyDetectionRule(
    name="amount_iqr_outlier",
    detector=lambda df: detect_outliers_iqr(df, 'amount', multiplier=1.5),
    features=['amount'],
    severity='medium'
))

# Regla 2: Z-score en quantity
pipeline.add_rule(AnomalyDetectionRule(
    name="quantity_zscore_outlier",
    detector=lambda df: detect_outliers_zscore(df, 'quantity', threshold=3),
    features=['quantity'],
    severity='medium'
))

# Regla 3: Isolation Forest multivariado
pipeline.add_rule(AnomalyDetectionRule(
    name="multivariate_isolation_forest",
    detector=lambda df: detect_anomalies_isolation_forest(
        df, ['amount', 'quantity', 'total'], contamination=0.05
    ),
    features=['amount', 'quantity', 'total'],
    severity='high'
))

# Ejecutar pipeline
flagged_transactions = pipeline.detect(transactions)

# Ver resumen
summary = pipeline.get_summary()
print("\n" + "="*70)
print(summary)

# Anomalías de alto riesgo
high_risk = pipeline.get_high_risk_anomalies(flagged_transactions, min_flags=2)
print(f"\nHigh-risk anomalies (flagged by 2+ rules): {len(high_risk)}")
print(high_risk[['transaction_id', 'amount', 'quantity', 'anomaly_count', 'anomaly_flags']].head(10))
```

---

## ✅ Success Criteria

- [ ] You implemented statistical methods (IQR, Z-score)
- [ ] You implemented ML methods (Isolation Forest, LOF)
- [ ] Usaste ensemble de detectores
- [ ] You detected anomalies in time series
- [ ] You created automatic detection pipeline
- [ ] You displayed detected anomalies

## 🎓 Conceptos Aprendidos

- Anomaly detection techniques
- Statistical methods (IQR, Z-score, MAD)
- ML methods (Isolation Forest, LOF, OCSVM)
- Time series anomalies
- Ensemble detection
- Anomaly scoring

## 📚 resources

- **PyOD**: https://pyod.readthedocs.io/
- **Scikit-learn Outlier Detection**: https://scikit-learn.org/stable/modules/outlier_detection.html
- **Time Series Anomaly Detection**: https://neptune.ai/blog/anomaly-detection-in-time-series

## ➡️ Next Exercise

**Exercise 05: Quality Monitoring** - monitor quality in real time
