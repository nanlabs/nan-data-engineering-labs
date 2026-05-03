# Exercise 06: Production Quality Gates

⏱️ **Estimated duration:** 3-4 hours
⭐⭐⭐⭐⭐ **Difficulty:** Advanced

## 🎯 Goals

- Implement quality gates in data pipelines
- Integrar validaciones con Airflow/Prefect
- Create quarantine strategy for bad data
- Implement automatic rollback
- Configurar circuit breakers
- Establish quality policies

## 📚 Conceptos Clave

- **Quality Gate**: Validation point that blocks progress if quality is insufficient
- **Quarantine Zone**: Isolation area for data that fails validation
- **Circuit Breaker**: Pattern that stops processing when errors exceed threshold
- **Rollback**: Revert to previous version when new data has problems
- **Data SLA**: Service level agreements for data quality

## 📝 Exercises

### Parte 1: Quality Gates

**Task 1.1: Implementar Quality Gate**

```python
from dataclasses import dataclass
from typing import Callable, List
from enum import Enum

class QualityGateAction(Enum):
    """Acciones cuando gate falla."""
    BLOCK = "block"          # Detener pipeline
    WARN = "warn"            # Continuar con warning
    QUARANTINE = "quarantine" # Aislar datos malos

@dataclass
class QualityGate:
    """Define un quality gate."""
    name: str
    description: str
    validator: Callable
    threshold: float
    action: QualityGateAction
    severity: str = "high"

class QualityGateEngine:
    """Motor de quality gates."""

    def __init__(self, pipeline_name: str):
        self.pipeline_name = pipeline_name
        self.gates = []
        self.results = []

    def add_gate(self, gate: QualityGate):
        """Agrega quality gate."""
        self.gates.append(gate)
        return self

    def validate(self, df, stage_name: str):
        """
        Ejecuta validaciones y aplica acciones.

        Returns:
            tuple: (passed: bool, df_clean, df_quarantined)
        """
        print(f"\n{'='*70}")
        print(f"QUALITY GATE: {stage_name}")
        print(f"{'='*70}")

        df_clean = df.copy()
        df_quarantined = pd.DataFrame()
        all_passed = True

        for gate in self.gates:
            print(f"\n🔍 Checking: {gate.name}")

            try:
                # Ejecutar validation
                result = gate.validator(df_clean)

                passed = result['passed']
                score = result.get('score', 100 if passed else 0)

                # Registrar resultado
                gate_result = {
                    'stage': stage_name,
                    'gate': gate.name,
                    'passed': passed,
                    'score': score,
                    'threshold': gate.threshold,
                    'action': gate.action.value,
                    'severity': gate.severity
                }
                self.results.append(gate_result)

                # Verificar threshold
                if score < gate.threshold:
                    print(f"  ❌ FAILED: {score:.2f}% < {gate.threshold}%")
                    print(f"  Action: {gate.action.value.upper()}")

                    if gate.action == QualityGateAction.BLOCK:
                        all_passed = False
                        print(f"  🚫 PIPELINE BLOCKED")
                        break

                    elif gate.action == QualityGateAction.QUARANTINE:
                        # Separar datos malos
                        violation_mask = result.get('violation_mask', pd.Series([False] * len(df_clean)))
                        df_bad = df_clean[violation_mask]
                        df_clean = df_clean[~violation_mask]

                        df_quarantined = pd.concat([df_quarantined, df_bad], ignore_index=True)

                        print(f"  ⚠️ {len(df_bad)} rows quarantined")
                        print(f"  ✅ {len(df_clean)} rows remaining")

                    elif gate.action == QualityGateAction.WARN:
                        print(f"  ⚠️ WARNING: Continuing with caution")

                else:
                    print(f"  ✅ PASSED: {score:.2f}% >= {gate.threshold}%")

            except Exception as e:
                print(f"  ❌ ERROR: {e}")
                gate_result = {
                    'stage': stage_name,
                    'gate': gate.name,
                    'passed': False,
                    'error': str(e)
                }
                self.results.append(gate_result)
                all_passed = False
                break

        print(f"\n{'='*70}")
        if all_passed:
            print(f"✅ All gates passed - {len(df_clean)} rows processed")
        else:
            print(f"❌ Quality gates failed - Pipeline halted")
        print(f"{'='*70}\n")

        return all_passed, df_clean, df_quarantined

# Validators para usar con gates

def completeness_validator(df, required_columns: list, threshold: float = 95):
    """Valida completitud de columnas requeridas."""
    scores = {}
    for col in required_columns:
        if col in df.columns:
            scores[col] = (1 - df[col].isna().sum() / len(df)) * 100

    avg_score = np.mean(list(scores.values()))
    passed = avg_score >= threshold

    return {
        'passed': passed,
        'score': avg_score,
        'details': scores
    }

def uniqueness_validator(df, unique_columns: list):
    """Valida unicidad."""
    duplicates = df.duplicated(subset=unique_columns, keep=False)
    violation_mask = duplicates

    score = (1 - duplicates.sum() / len(df)) * 100

    return {
        'passed': score >= 99,
        'score': score,
        'violation_mask': violation_mask
    }

def validity_validator(df, column: str, validator_func: callable):
    """Valida valores válidos."""
    valid_mask = df[column].apply(validator_func)
    score = (valid_mask.sum() / len(df)) * 100

    return {
        'passed': score >= 95,
        'score': score,
        'violation_mask': ~valid_mask
    }

# Uso
engine = QualityGateEngine("ETL Pipeline")

# Gate 1: Completeness (BLOCK si falla)
engine.add_gate(QualityGate(
    name="Required Fields Completeness",
    description="Critical fields must be 95%+ complete",
    validator=lambda df: completeness_validator(df, ['customer_id', 'amount', 'transaction_date'], 95),
    threshold=95,
    action=QualityGateAction.BLOCK,
    severity="critical"
))

# Gate 2: Uniqueness (QUARANTINE duplicados)
engine.add_gate(QualityGate(
    name="Transaction ID Uniqueness",
    description="transaction_id must be unique",
    validator=lambda df: uniqueness_validator(df, ['transaction_id']),
    threshold=99,
    action=QualityGateAction.QUARANTINE,
    severity="high"
))

# Gate 3: Validity (QUARANTINE inválidos)
engine.add_gate(QualityGate(
    name="Amount Validity",
    description="Amount must be positive",
    validator=lambda df: validity_validator(df, 'amount', lambda x: x > 0),
    threshold=98,
    action=QualityGateAction.QUARANTINE,
    severity="high"
))

# Ejecutar validation
passed, df_clean, df_quarantined = engine.validate(transactions, "Raw Data Ingestion")

if not passed:
    raise ValueError("Quality gates failed! Pipeline stopped.")
```

---

### Parte 2: Airflow Integration

**Task 2.1: Airflow DAG con Quality Gates**

```python
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.dates import days_ago
from airflow.exceptions import AirflowException
import great_expectations as gx

def extract_data(**context):
    """Extrae datos de source."""
    # Simulate extraction
    df = pd.read_csv('/data/raw/transactions.csv')

    # Save to XCom
    context['task_instance'].xcom_push(key='row_count', value=len(df))

    # Save to staging
    df.to_parquet('/data/staging/transactions.parquet')

    return "extract_complete"

def validate_raw_data(**context):
    """Quality gate: Validar datos raw."""
    df = pd.read_parquet('/data/staging/transactions.parquet')

    # Create quality gate engine
    engine = QualityGateEngine("Raw Data Validation")

    engine.add_gate(QualityGate(
        name="Completeness Check",
        description="Required fields complete",
        validator=lambda df: completeness_validator(df, ['id', 'amount', 'date'], 95),
        threshold=95,
        action=QualityGateAction.BLOCK
    ))

    engine.add_gate(QualityGate(
        name="Uniqueness Check",
        description="IDs must be unique",
        validator=lambda df: uniqueness_validator(df, ['id']),
        threshold=99,
        action=QualityGateAction.QUARANTINE
    ))

    # Execute validation
    passed, df_clean, df_quarantined = engine.validate(df, "Raw Data")

    # Save results
    df_clean.to_parquet('/data/validated/transactions_clean.parquet')

    if len(df_quarantined) > 0:
        df_quarantined.to_parquet('/data/quarantine/transactions_bad.parquet')
        context['task_instance'].xcom_push(key='quarantined_count', value=len(df_quarantined))

    if not passed:
        raise AirflowException("Quality validation failed!")

    return "validation_passed"

def transform_data(**context):
    """Transforma datos."""
    df = pd.read_parquet('/data/validated/transactions_clean.parquet')

    # Apply transformations
    df['amount_usd'] = df['amount'] * 1.0  # Currency conversion
    df['year'] = pd.to_datetime(df['date']).dt.year
    df['month'] = pd.to_datetime(df['date']).dt.month

    df.to_parquet('/data/transformed/transactions.parquet')

    return "transform_complete"

def validate_transformed_data(**context):
    """Quality gate: Validar datos transformados."""
    df = pd.read_parquet('/data/transformed/transactions.parquet')

    # Use Great Expectations
    ge_context = gx.get_context()

    results = ge_context.run_checkpoint(
        checkpoint_name="transformed_data_checkpoint",
        batch_request={
            "runtime_parameters": {"batch_data": df},
            "batch_identifiers": {"default_identifier_name": "transformed"},
        }
    )

    if not results["success"]:
        raise AirflowException("Transformed data validation failed!")

    return "validation_passed"

def load_data(**context):
    """Carga datos al warehouse."""
    df = pd.read_parquet('/data/transformed/transactions.parquet')

    # Load to warehouse (simulate)
    print(f"Loading {len(df)} rows to warehouse...")

    return "load_complete"

def send_quarantine_alert(**context):
    """Alerta sobre datos en quarantine."""
    quarantined_count = context['task_instance'].xcom_pull(
        task_ids='validate_raw_data',
        key='quarantined_count'
    )

    if quarantined_count:
        print(f"⚠️ ALERT: {quarantined_count} rows quarantined")
        # Send email/Slack notification

    return "alert_sent"

# Define DAG
dag = DAG(
    'etl_with_quality_gates',
    default_args={
        'owner': 'data-engineering',
        'depends_on_past': False,
        'email_on_failure': True,
        'email_on_retry': False,
        'retries': 1,
    },
    description='ETL pipeline with quality gates',
    schedule_interval='@daily',
    start_date=days_ago(1),
    catchup=False,
    tags=['etl', 'quality'],
)

with dag:
    start = DummyOperator(task_id='start')

    extract = PythonOperator(
        task_id='extract_data',
        python_callable=extract_data
    )

    validate_raw = PythonOperator(
        task_id='validate_raw_data',
        python_callable=validate_raw_data
    )

    transform = PythonOperator(
        task_id='transform_data',
        python_callable=transform_data
    )

    validate_transformed = PythonOperator(
        task_id='validate_transformed_data',
        python_callable=validate_transformed_data
    )

    load = PythonOperator(
        task_id='load_data',
        python_callable=load_data
    )

    quarantine_alert = PythonOperator(
        task_id='send_quarantine_alert',
        python_callable=send_quarantine_alert,
        trigger_rule='all_done'  # Execute even if upstream fails
    )

    end = DummyOperator(task_id='end')

    # Define dependencies
    start >> extract >> validate_raw >> transform >> validate_transformed >> load >> end
    validate_raw >> quarantine_alert >> end
```

---

### Parte 3: Circuit Breaker Pattern

**Task 3.1: Implementar Circuit Breaker**

```python
from datetime import datetime, timedelta
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failures exceeded, block requests
    HALF_OPEN = "half_open" # Testing if service recovered

class CircuitBreaker:
    """
    Circuit breaker para detener procesamiento cuando errores son frecuentes.

    States:
    - CLOSED: Everything OK, allow requests
    - OPEN: Too many failures, block all requests
    - HALF_OPEN: Testing recovery, allow limited requests
    """

    def __init__(self,
                 failure_threshold: int = 5,
                 timeout_seconds: int = 60,
                 success_threshold: int = 2):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.success_threshold = success_threshold

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""

        # Si está OPEN, verificar si debemos pasar a HALF_OPEN
        if self.state == CircuitState.OPEN:
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout_seconds):
                print("⚡ Circuit breaker transitioning to HALF_OPEN (testing recovery)")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise Exception(f"Circuit breaker is OPEN. Too many recent failures.")

        try:
            # Ejecutar función
            result = func(*args, **kwargs)

            # Success
            self._on_success()
            return result

        except Exception as e:
            # Failure
            self._on_failure()
            raise e

    def _on_success(self):
        """Handle successful execution."""
        self.failure_count = 0

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1

            # Si hay suficientes éxitos, cerrar circuito
            if self.success_count >= self.success_threshold:
                print("✅ Circuit breaker transitioning to CLOSED (recovered)")
                self.state = CircuitState.CLOSED
                self.success_count = 0

    def _on_failure(self):
        """Handle failed execution."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            print(f"🚨 Circuit breaker transitioning to OPEN ({self.failure_count} failures)")
            self.state = CircuitState.OPEN

    def get_state(self):
        """Get current state."""
        return self.state.value

    def reset(self):
        """Manually reset circuit breaker."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None

# Uso
circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    timeout_seconds=60,
    success_threshold=2
)

def risky_data_operation(data):
    """Operation that might fail."""
    # Simulate data quality check
    if np.random.random() < 0.3:  # 30% failure rate
        raise ValueError("Data quality check failed!")

    return "Success"

# Simulate múltiples llamadas
for i in range(10):
    try:
        print(f"\n--- Attempt {i+1} ---")
        result = circuit_breaker.call(risky_data_operation, "data")
        print(f"✅ {result}")
    except Exception as e:
        print(f"❌ {e}")

    print(f"Circuit state: {circuit_breaker.get_state()}")
    time.sleep(1)
```

---

### Parte 4: Data Versioning & Rollback

**Task 4.1: Data Version Manager**

```python
import shutil
import hashlib

class DataVersionManager:
    """Gestor de versiones de datos."""

    def __init__(self, base_path: str):
        self.base_path = base_path
        self.versions = []

    def save_version(self, df: pd.DataFrame, metadata: dict = None) -> str:
        """
        Guarda versión de dataset.

        Returns:
            version_id
        """
        # Generate version ID
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        data_hash = self._calculate_hash(df)
        version_id = f"v_{timestamp}_{data_hash[:8]}"

        # Create version directory
        version_path = f"{self.base_path}/{version_id}"
        os.makedirs(version_path, exist_ok=True)

        # Save data
        df.to_parquet(f"{version_path}/data.parquet")

        # Save metadata
        metadata = metadata or {}
        metadata.update({
            'version_id': version_id,
            'timestamp': timestamp,
            'row_count': len(df),
            'columns': list(df.columns),
            'data_hash': data_hash
        })

        with open(f"{version_path}/metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2, default=str)

        # Register version
        self.versions.append(metadata)

        print(f"✅ Version saved: {version_id}")
        return version_id

    def load_version(self, version_id: str) -> pd.DataFrame:
        """Carga versión específica."""
        version_path = f"{self.base_path}/{version_id}"

        if not os.path.exists(version_path):
            raise ValueError(f"Version {version_id} not found")

        df = pd.read_parquet(f"{version_path}/data.parquet")
        print(f"✅ Version loaded: {version_id} ({len(df)} rows)")

        return df

    def rollback(self, steps: int = 1) -> pd.DataFrame:
        """Rollback a versión anterior."""
        if len(self.versions) < steps + 1:
            raise ValueError(f"Not enough versions for rollback (have {len(self.versions)})")

        target_version = self.versions[-(steps + 1)]
        version_id = target_version['version_id']

        print(f"🔄 Rolling back {steps} version(s) to {version_id}")

        return self.load_version(version_id)

    def list_versions(self):
        """Lista todas las versiones."""
        print(f"\n{'='*70}")
        print("DATA VERSIONS")
        print(f"{'='*70}")

        for i, version in enumerate(self.versions, 1):
            print(f"{i}. {version['version_id']}")
            print(f"   Timestamp: {version['timestamp']}")
            print(f"   Rows: {version['row_count']}")
            print(f"   Quality Score: {version.get('quality_score', 'N/A')}")
            print()

    def _calculate_hash(self, df: pd.DataFrame) -> str:
        """Calcula hash del dataset."""
        return hashlib.md5(pd.util.hash_pandas_object(df).values).hexdigest()

# Uso
version_manager = DataVersionManager('/data/versions/transactions')

# Save initial version
v1 = version_manager.save_version(
    transactions,
    metadata={'stage': 'raw', 'quality_score': 95.5}
)

# Process data (simulate transformation causing quality drop)
transactions_processed = transactions.copy()
# ... transformations ...

# Save processed version
v2 = version_manager.save_version(
    transactions_processed,
    metadata={'stage': 'processed', 'quality_score': 87.2}
)

# Quality check fails - rollback!
if 87.2 < 90:  # SLA threshold
    print("⚠️ Quality below SLA! Rolling back...")
    transactions = version_manager.rollback(steps=1)
```

---

### Parte 5: Production pipeline Completo

**Task 5.1: pipeline Empresarial**

```python
class ProductionDataPipeline:
    """Pipeline de datos de producción con todos los controles de calidad."""

    def __init__(self, name: str):
        self.name = name
        self.version_manager = DataVersionManager(f'/data/versions/{name}')
        self.quality_gate_engine = QualityGateEngine(name)
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, timeout_seconds=300)
        self.monitor = QualityMonitor(name)

    def run(self, input_data: pd.DataFrame):
        """Ejecuta pipeline completo."""
        print(f"\n{'='*80}")
        print(f"STARTING PIPELINE: {self.name}")
        print(f"{'='*80}\n")

        try:
            # Stage 1: Save initial version
            print("📦 Stage 1: Version Control")
            v1 = self.version_manager.save_version(
                input_data,
                metadata={'stage': 'raw', 'timestamp': datetime.now()}
            )

            # Stage 2: Quality gates (Raw Data)
            print("\n🔍 Stage 2: Quality Gates (Raw Data)")
            self._configure_raw_data_gates()

            passed, df_clean, df_quarantined = self.quality_gate_engine.validate(
                input_data,
                "Raw Data Validation"
            )

            if not passed:
                raise ValueError("Raw data quality gates failed!")

            if len(df_quarantined) > 0:
                print(f"⚠️ {len(df_quarantined)} rows quarantined")
                self._handle_quarantine(df_quarantined, "raw_data")

            # Stage 3: Transform (with circuit breaker)
            print("\n⚙️ Stage 3: Transform Data (with Circuit Breaker)")
            df_transformed = self.circuit_breaker.call(
                self._transform,
                df_clean
            )

            #Stage 4: Save transformed version
            print("\n📦 Stage 4: Version Control (Transformed)")
            v2 = self.version_manager.save_version(
                df_transformed,
                metadata={'stage': 'transformed', 'timestamp': datetime.now()}
            )

            # Stage 5: Quality monitoring
            print("\n📊 Stage 5: Quality Monitoring")
            quality_checks = self._calculate_quality_metrics(df_transformed)
            self.monitor.check_quality(df_transformed, quality_checks)

            # Stage 6: Final quality gate
            print("\n🔍 Stage 6: Final Quality Gate")
            self._configure_final_gates()

            passed, df_final, df_quarantined = self.quality_gate_engine.validate(
                df_transformed,
                "Final Validation"
            )

            if not passed:
                print("❌ Final quality gate failed! Rolling back...")
                df_final = self.version_manager.rollback(steps=1)

            # Stage 7: Load
            print("\n✅ Stage 7: Load to Warehouse")
            self._load(df_final)

            print(f"\n{'='*80}")
            print(f"✅ PIPELINE COMPLETED SUCCESSFULLY")
            print(f"   Rows processed: {len(df_final)}")
            print(f"   Rows quarantined: {len(df_quarantined)}")
            print(f"{'='*80}\n")

            return df_final

        except Exception as e:
            print(f"\n{'='*80}")
            print(f"❌ PIPELINE FAILED: {e}")
            print(f"{'='*80}\n")
            raise

    def _configure_raw_data_gates(self):
        """Configura gates para raw data."""
        self.quality_gate_engine.gates = []  # Reset

        self.quality_gate_engine.add_gate(QualityGate(
            name="Completeness - Critical Fields",
            description="Required fields must be 95%+ complete",
            validator=lambda df: completeness_validator(df, ['transaction_id', 'customer_id', 'amount'], 95),
            threshold=95,
            action=QualityGateAction.BLOCK
        ))

        self.quality_gate_engine.add_gate(QualityGate(
            name="Uniqueness - Transaction ID",
            description="transaction_id must be unique",
            validator=lambda df: uniqueness_validator(df, ['transaction_id']),
            threshold=99,
            action=QualityGateAction.QUARANTINE
        ))

    def _configure_final_gates(self):
        """Configura gates finales."""
        self.quality_gate_engine.gates = []  # Reset

        self.quality_gate_engine.add_gate(QualityGate(
            name="Overall Quality Score",
            description="Overall quality must be >= 90%",
            validator=lambda df: {'passed': True, 'score': 92},  # Simplified
            threshold=90,
            action=QualityGateAction.BLOCK
        ))

    def _transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform data."""
        df = df.copy()

        # Transformations
        df['amount_usd'] = df['amount'] * 1.0
        df['year'] = pd.to_datetime(df['transaction_date']).dt.year

        return df

    def _calculate_quality_metrics(self, df: pd.DataFrame) -> dict:
        """Calculate quality metrics."""
        metrics_calculator = DataQualityMetrics()

        return {
            'completeness': metrics_calculator.completeness(df),
            'uniqueness': metrics_calculator.uniqueness(df, 'transaction_id'),
            'validity': 95.0,  # Simplified
            'consistency': 93.0,
            'timeliness': 88.0
        }

    def _handle_quarantine(self, df: pd.DataFrame, stage: str):
        """Handle quarantined data."""
        # Save to quarantine area
        quarantine_path = f"/data/quarantine/{self.name}/{stage}/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(quarantine_path, exist_ok=True)
        df.to_parquet(f"{quarantine_path}/data.parquet")

        print(f"📁 Quarantined data saved to: {quarantine_path}")

    def _load(self, df: pd.DataFrame):
        """Load to warehouse."""
        # Simulate load
        print(f"Loading {len(df)} rows to warehouse...")

# Uso
pipeline = ProductionDataPipeline("transactions_etl")
result = pipeline.run(transactions)
```

---

## ✅ Success Criteria

- [ ] You implemented quality gates with multiple actions
- [ ] Integraste validaciones en pipeline Airflow
- [ ] Implementaste circuit breaker pattern
- [ ] Creaste sistema de versioning y rollback
- [ ] You managed quarantine zone for bad data
- [ ] You ran the entire production pipeline

## 🎓 Conceptos Aprendidos

- Production quality gates
- pipeline integration (Airflow)
- Circuit breaker pattern
- Data versioning & rollback
- Quarantine strategy
- SLA enforcement

## 🎉 Module Completed!

You have completed the Data Quality module. Now you have:
- Knowledge of 6 dimensions of quality
- Experiencia con Great Expectations
- Habilidades de anomaly detection
- Sistema de monitoreo continuo
- Robust production pipelines

## 📚 Additional Resources

- **Data Quality Book**: "Data Quality: The Accuracy Dimension" by Joseph M. Juran
- **GE in Production**: https://docs.greatexpectations.io/docs/guides/setup/configuring_metadata_stores/
- **Airflow Best Practices**: https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html

## ➡️ Upcoming Modules

- **Module 10: Workflow Orchestration** - Apache Airflow deep dive
- **Module 11: Infrastructure as Code** - Terraform, CloudFormation
