# Exercise 05: Quality Monitoring

⏱️ **Estimated duration:** 2-3 hours
⭐⭐⭐⭐ **Difficulty:** Advanced

## 🎯 Goals

- Implement data quality metrics
- Crear sistema de monitoreo continuo
- Set up automatic alerts
- Track historical metrics
- Generate quality dashboards
- Establish quality SLAs

## 📚 Conceptos Clave

- **Data Quality Metrics**: Quantifiable quality metrics
- **Quality Monitoring**: Continuous quality monitoring
- **SLA (Service Level Agreement)**: Acuerdos de level de service
- **Quality Drift**: Gradual degradation of quality
- **Data Observability**: Complete visibility of data status

## 📝 Exercises

### Part 1: Quality Metrics

**Task 1.1: Calculate Basic Metrics**

```python
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict

class DataQualityMetrics:
    """Calculador de métricas de calidad."""

    @staticmethod
    def completeness(df: pd.DataFrame, column: str = None) -> float:
        """
        Completeness = (non-null values / total values) * 100
        """
        if column:
            return (1 - df[column].isna().sum() / len(df)) * 100
        else:
            # Overall completeness
            total_cells = df.shape[0] * df.shape[1]
            non_null_cells = total_cells - df.isna().sum().sum()
            return (non_null_cells / total_cells) * 100

    @staticmethod
    def uniqueness(df: pd.DataFrame, column: str) -> float:
        """
        Uniqueness = (unique values / total values) * 100
        """
        return (df[column].nunique() / len(df)) * 100

    @staticmethod
    def validity(df: pd.DataFrame, column: str, validation_func: callable) -> float:
        """
        Validity = (valid values / total values) * 100

        Example:
            validity(df, 'email', lambda x: '@' in str(x))
        """
        valid = df[column].apply(validation_func).sum()
        return (valid / len(df)) * 100

    @staticmethod
    def consistency(df: pd.DataFrame, check_func: callable) -> float:
        """
        Consistency = (consistent rows / total rows) * 100

        Example:
            consistency(df, lambda row: row['total'] == row['amount'] * row['quantity'])
        """
        consistent = df.apply(check_func, axis=1).sum()
        return (consistent / len(df)) * 100

    @staticmethod
    def timeliness(df: pd.DataFrame, date_column: str, max_age_hours: int) -> float:
        """
        Timeliness = (records within SLA / total records) * 100
        """
        df_copy = df.copy()
        df_copy[date_column] = pd.to_datetime(df_copy[date_column])

        age_hours = (datetime.now() - df_copy[date_column]).dt.total_seconds() / 3600
        timely = (age_hours <= max_age_hours).sum()

        return (timely / len(df)) * 100

    @staticmethod
    def accuracy(df: pd.DataFrame, column: str, reference_values: dict) -> float:
        """
        Accuracy = (accurate values / total values) * 100

        Compara con valores de referencia conocidos.
        """
        accurate = df[column].isin(reference_values.keys()).sum()
        return (accurate / len(df)) * 100

# Uso
metrics = DataQualityMetrics()

# Completeness
completeness_score = metrics.completeness(transactions, 'amount')
print(f"Completeness (amount): {completeness_score:.2f}%")

# Uniqueness
uniqueness_score = metrics.uniqueness(transactions, 'transaction_id')
print(f"Uniqueness (transaction_id): {uniqueness_score:.2f}%")

# Validity - emails válidos
validity_score = metrics.validity(
    customers,
    'email',
    lambda x: '@' in str(x) and '.' in str(x)
)
print(f"Validity (email): {validity_score:.2f}%")

# Consistency - total = amount * quantity
consistency_score = metrics.consistency(
    transactions,
    lambda row: abs(row['total'] - row['amount'] * row['quantity']) < 0.01
)
print(f"Consistency (total): {consistency_score:.2f}%")
```

**Task 1.2: Quality Score Agregado**

```python
class DataQualityScorer:
    """Calcula score agregado de calidad."""

    def __init__(self):
        self.dimension_weights = {
            'completeness': 0.25,
            'uniqueness': 0.20,
            'validity': 0.25,
            'consistency': 0.20,
            'timeliness': 0.10
        }
        self.scores = {}

    def add_score(self, dimension: str, score: float):
        """Agrega score de una dimensión."""
        self.scores[dimension] = score
        return self

    def calculate_overall_score(self) -> float:
        """Calcula score ponderado."""
        weighted_sum = sum(
            self.scores.get(dim, 0) * weight
            for dim, weight in self.dimension_weights.items()
        )
        return weighted_sum

    def get_grade(self, score: float) -> str:
        """Convierte score a grado."""
        if score >= 95:
            return "A (Excellent)"
        elif score >= 85:
            return "B (Good)"
        elif score >= 75:
            return "C (Fair)"
        elif score >= 60:
            return "D (Poor)"
        else:
            return "F (Critical)"

    def print_report(self):
        """Imprime reporte de calidad."""
        print("=" * 70)
        print("DATA QUALITY SCORE REPORT")
        print("=" * 70)

        for dimension, score in self.scores.items():
            weight = self.dimension_weights.get(dimension, 0)
            weighted = score * weight
            print(f"{dimension:20} : {score:6.2f}% (weight: {weight:.2f}, weighted: {weighted:.2f})")

        overall = self.calculate_overall_score()
        grade = self.get_grade(overall)

        print("-" * 70)
        print(f"{'OVERALL SCORE':20} : {overall:6.2f}%")
        print(f"{'GRADE':20} : {grade}")
        print("=" * 70)

# Uso
scorer = DataQualityScorer()
scorer.add_score('completeness', 97.5)
scorer.add_score('uniqueness', 99.2)
scorer.add_score('validity', 94.8)
scorer.add_score('consistency', 96.1)
scorer.add_score('timeliness', 89.3)
scorer.print_report()
```

---

### Parte 2: Monitoreo Continuo

**Task 2.1: Quality Monitor**

```python
from datetime import datetime, timedelta
import json

class QualityMonitor:
    """Monitor de calidad de datos."""

    def __init__(self, name: str):
        self.name = name
        self.history = []
        self.alerts = []
        self.thresholds = {
            'completeness': 95.0,
            'uniqueness': 98.0,
            'validity': 95.0,
            'consistency': 90.0,
            'timeliness': 85.0
        }

    def check_quality(self, df: pd.DataFrame, checks: dict):
        """
        Execute checks de calidad y registra resultados.

        Args:
            checks: dict con format {'dimension': score}
        """
        timestamp = datetime.now()
        results = {
            'timestamp': timestamp,
            'dataset': self.name,
            'row_count': len(df),
            'scores': checks,
            'alerts': []
        }

        # Verificar thresholds
        for dimension, score in checks.items():
            threshold = self.thresholds.get(dimension)

            if threshold and score < threshold:
                alert = {
                    'dimension': dimension,
                    'score': score,
                    'threshold': threshold,
                    'severity': self._get_severity(score, threshold)
                }
                results['alerts'].append(alert)
                self.alerts.append({**alert, 'timestamp': timestamp})

        self.history.append(results)
        return results

    def _get_severity(self, score: float, threshold: float) -> str:
        """Determina severidad de la alerta."""
        diff = threshold - score
        if diff >= 10:
            return 'critical'
        elif diff >= 5:
            return 'warning'
        else:
            return 'info'

    def get_history(self, hours: int = 24) -> list:
        """Retorna historial de últimas N hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [h for h in self.history if h['timestamp'] >= cutoff]

    def get_active_alerts(self, hours: int = 24) -> list:
        """Retorna alertas activas."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [a for a in self.alerts if a['timestamp'] >= cutoff]

    def export_metrics(self, filepath: str):
        """Exporta métricas para análisis externo."""
        with open(filepath, 'w') as f:
            json.dump(self.history, f, default=str, indent=2)

# Uso
monitor = QualityMonitor("transactions")

# Simular checks periódicos
import time

for i in range(5):
    print(f"\n--- Check {i+1} ---")

    # Calcular métricas actuales
    checks = {
        'completeness': np.random.uniform(90, 100),
        'uniqueness': np.random.uniform(95, 100),
        'validity': np.random.uniform(85, 100),
        'consistency': np.random.uniform(88, 100),
        'timeliness': np.random.uniform(80, 100)
    }

    # Ejecutar check
    results = monitor.check_quality(transactions, checks)

    # Mostrar resultados
    print(f"Scores: {results['scores']}")
    if results['alerts']:
        print(f"⚠️ Alerts: {len(results['alerts'])}")
        for alert in results['alerts']:
            print(f"  - {alert['dimension']}: {alert['score']:.2f}% < {alert['threshold']}% ({alert['severity']})")

    time.sleep(1)  # Esperar 1 segundo

# Ver historial
print("\n--- Monitor History ---")
print(f"Total checks: {len(monitor.history)}")
print(f"Active alerts: {len(monitor.get_active_alerts())}")
```

**Task 2.2: Detectar Quality Drift**

```python
class QualityDriftDetector:
    """Detecta degradación de calidad con el tiempo."""

    def __init__(self, window_size: int = 10):
        self.window_size = window_size

    def detect_drift(self, history: list, dimension: str) -> dict:
        """
        Detecta drift comparando promedio reciente vs histórico.
        """
        if len(history) < self.window_size * 2:
            return {'drift_detected': False, 'message': 'Insufficient history'}

        # Extraer scores de la dimensión
        scores = [h['scores'].get(dimension, 0) for h in history]

        # Recent vs historical
        recent_scores = scores[-self.window_size:]
        historical_scores = scores[:-self.window_size]

        recent_mean = np.mean(recent_scores)
        historical_mean = np.mean(historical_scores)

        # Calcular drift
        drift_pct = ((recent_mean - historical_mean) / historical_mean) * 100

        # Threshold: -5% es significativo
        drift_detected = drift_pct < -5

        return {
            'drift_detected': drift_detected,
            'dimension': dimension,
            'recent_mean': recent_mean,
            'historical_mean': historical_mean,
            'drift_percentage': drift_pct,
            'severity': 'high' if drift_pct < -10 else 'medium' if drift_pct < -5 else 'low'
        }

# Uso
drift_detector = QualityDriftDetector(window_size=10)
drift_result = drift_detector.detect_drift(monitor.history, 'completeness')

if drift_result['drift_detected']:
    print(f"⚠️ Quality drift detected in {drift_result['dimension']}!")
    print(f"  Recent: {drift_result['recent_mean']:.2f}%")
    print(f"  Historical: {drift_result['historical_mean']:.2f}%")
    print(f"  Drift: {drift_result['drift_percentage']:.2f}%")
```

---

### Parte 3: Alerting

**Task 3.1: Alert Manager**

```python
from enum import Enum

class AlertSeverity(Enum):
    INFO = 1
    WARNING = 2
    CRITICAL = 3

class AlertManager:
    """Gestor de alertas."""

    def __init__(self):
        self.alert_handlers = []

    def add_handler(self, handler: callable):
        """Agrega handler de alertas."""
        self.alert_handlers.append(handler)
        return self

    def send_alert(self, severity: AlertSeverity, message: str, metadata: dict = None):
        """Envía alerta a todos los handlers."""
        alert = {
            'timestamp': datetime.now(),
            'severity': severity.name,
            'message': message,
            'metadata': metadata or {}
        }

        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                print(f"Error in alert handler: {e}")

# Handlers de ejemplo

def console_alert_handler(alert):
    """Handler que imprime en consola."""
    severity_icons = {
        'INFO': 'ℹ️',
        'WARNING': '⚠️',
        'CRITICAL': '🚨'
    }
    icon = severity_icons.get(alert['severity'], '❓')
    print(f"{icon} [{alert['severity']}] {alert['timestamp']}: {alert['message']}")

def file_alert_handler(alert):
    """Handler que write a archivo."""
    with open('data_quality_alerts.log', 'a') as f:
        f.write(f"{alert['timestamp']} | {alert['severity']} | {alert['message']}\n")

def email_alert_handler(alert):
    """Handler que envía email (simulado)."""
    if alert['severity'] == 'CRITICAL':
        print(f"📧 Email sent to: data-team@company.com")
        print(f"   Subject: [CRITICAL] Data Quality Alert")
        print(f"   Body: {alert['message']}")

# Uso
alert_manager = AlertManager()
alert_manager.add_handler(console_alert_handler)
alert_manager.add_handler(file_alert_handler)
alert_manager.add_handler(email_alert_handler)

# Enviar alertas
alert_manager.send_alert(
    AlertSeverity.WARNING,
    "Completeness dropped below 95%",
    metadata={'dimension': 'completeness', 'score': 93.2}
)

alert_manager.send_alert(
    AlertSeverity.CRITICAL,
    "Multiple quality dimensions failing",
    metadata={'failed_dimensions': ['completeness', 'validity']}
)
```

---

### Parte 4: Dashboard & Reporting

**Task 4.1: Generar Dashboard HTML**

```python
def generate_quality_dashboard(monitor: QualityMonitor, output_file: str = 'quality_dashboard.html'):
    """Genera dashboard HTML de calidad."""

    history = monitor.get_history(hours=24)

    if not history:
        print("No history available")
        return

    # Preparar datos para gráficos
    timestamps = [h['timestamp'].strftime('%H:%M') for h in history]

    dimensions = list(history[0]['scores'].keys())
    dimension_data = {
        dim: [h['scores'].get(dim, 0) for h in history]
        for dim in dimensions
    }

    # HTML template
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Data Quality Dashboard</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
            .metrics {{ display: flex; justify-content: space-around; margin: 20px 0; }}
            .metric {{ background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; flex: 1; margin: 0 10px; }}
            .metric-value {{ font-size: 36px; font-weight: bold; color: #3498db; }}
            .metric-label {{ color: #7f8c8d; margin-top: 10px; }}
            .chart {{ background: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .alert {{ background: #e74c3c; color: white; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Data Quality Dashboard - {monitor.name}</h1>
            <p>Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="metrics">
    """

    # Current scores (latest check)
    latest = history[-1]
    for dim, score in latest['scores'].items():
        threshold = monitor.thresholds.get(dim, 0)
        status = "✅" if score >= threshold else "❌"
        html += f"""
            <div class="metric">
                <div class="metric-value">{score:.1f}%</div>
                <div class="metric-label">{dim.capitalize()} {status}</div>
            </div>
        """

    html += """
        </div>
    """

    # Active alerts
    active_alerts = monitor.get_active_alerts(hours=24)
    if active_alerts:
        html += f"""
        <div class="alert">
            🚨 <strong>{len(active_alerts)} Active Alerts</strong>
        """
        for alert in active_alerts[:5]:  # Show max 5
            html += f"<br>• {alert['dimension']}: {alert['score']:.2f}% < {alert['threshold']}% ({alert['severity']})"
        html += """
        </div>
        """

    # Time series chart
    html += """
        <div class="chart">
            <h2>Quality Trends (Last 24 Hours)</h2>
            <div id="trendsChart"></div>
        </div>

        <script>
    """

    # Plot.ly data
    traces = []
    for dim, values in dimension_data.items():
        traces.append({
            'x': timestamps,
            'y': values,
            'name': dim.capitalize(),
            'type': 'scatter',
            'mode': 'lines+markers'
        })

    html += f"""
        var data = {json.dumps(traces)};
        var layout = {{
            xaxis: {{ title: 'Time' }},
            yaxis: {{ title: 'Score (%)', range: [0, 100] }},
            hovermode: 'closest'
        }};
        Plotly.newPlot('trendsChart', data, layout);
        </script>
    </body>
    </html>
    """

    # Write file
    with open(output_file, 'w') as f:
        f.write(html)

    print(f"✅ Dashboard generated: {output_file}")

# Uso
generate_quality_dashboard(monitor, 'quality_dashboard.html')
```

---

## ✅ Success Criteria

- [ ] You calculated quality metrics (6 dimensions)
- [ ] Implementaste sistema de monitoreo continuo
- [ ] Detectaste quality drift
- [ ] You set up automatic alerts
- [ ] You generated quality dashboard
- [ ] You exported historical metrics

## 🎓 Conceptos Aprendidos

- Data quality metrics
- Continuous monitoring
- Quality drift detection
- Alert management
- SLA tracking
- Data observability

## 📚 resources

- **Prometheus**: https://prometheus.io/
- **Grafana**: https://grafana.com/
- **DataDog Data Quality**: https://www.datadoghq.com/

## ➡️ Next Exercise

**Exercise 06: Production Quality Gates** - Implementar gates en pipelines productivos
