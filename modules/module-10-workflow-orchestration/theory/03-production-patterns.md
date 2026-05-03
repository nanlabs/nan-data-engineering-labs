# Production Patterns

## 📋 Table of Contents

1. [Production Deployment](#production-deployment)
2. [High Availability](#high-availability)
3. [Scaling Strategies](#scaling-strategies)
4. [Secrets Management](#secrets-management)
5. [Monitoring & Observability](#monitoring--observability)
6. [Alerting](#alerting)
7. [Performance Optimization](#performance-optimization)
8. [Security Best Practices](#security-best-practices)
9. [CI/CD for DAGs](#cicd-for-dags)
10. [Common Anti-Patterns](#common-anti-patterns)

---

## Production Deployment

### Deployment Architecture

**Recommended Production Setup:**

```
┌──────────────────────────────────────────────────────────┐
│                    Load Balancer                         │
└────────────┬──────────────────────────────┬──────────────┘
             │                              │
    ┌────────▼────────┐          ┌─────────▼────────┐
    │  Web Server #1  │          │  Web Server #2   │
    │   (Gunicorn)    │          │   (Gunicorn)     │
    └─────────────────┘          └──────────────────┘
                 │                        │
                 └────────────┬───────────┘
                              │
                    ┌─────────▼─────────┐
                    │   PostgreSQL HA   │
                    │  (Master-Replica) │
                    └─────────┬─────────┘
                              │
                 ┌────────────┴──────────────┐
                 │                           │
        ┌────────▼────────┐        ┌────────▼────────┐
        │  Scheduler #1   │        │  Scheduler #2   │
        │   (Active)      │        │   (Standby)     │
        └────────┬────────┘        └─────────────────┘
                 │
           ┌─────▼──────┐
           │   Redis    │
           │  (Broker)  │
           └─────┬──────┘
                 │
     ┌───────────┼───────────┐
     │           │           │
┌────▼────┐ ┌───▼────┐ ┌───▼────┐
│ Worker  │ │ Worker │ │ Worker │
│  Pool   │ │  Pool  │ │  Pool  │
└─────────┘ └────────┘ └────────┘
```

### Infrastructure as Code

**Docker Compose (Development/Small Prod):**

```yaml
# docker-compose.yml
version: '3.8'

x-airflow-common: &airflow-common
  image: apache/airflow:2.8.1
  environment: &airflow-common-env
    AIRFLOW__CORE__EXECUTOR: CeleryExecutor
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
    AIRFLOW__CELERY__RESULT_BACKEND: db+postgresql://airflow:airflow@postgres/airflow
    AIRFLOW__CELERY__BROKER_URL: redis://:@redis:6379/0
    AIRFLOW__CORE__FERNET_KEY: ''
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'true'
    AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
    AIRFLOW__API__AUTH_BACKENDS: 'airflow.api.auth.backend.basic_auth'
  volumes:
    - ./dags:/opt/airflow/dags
    - ./logs:/opt/airflow/logs
    - ./plugins:/opt/airflow/plugins
  user: "${AIRFLOW_UID:-50000}:0"
  depends_on: &airflow-common-depends-on
    redis:
      condition: service_healthy
    postgres:
      condition: service_healthy

services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    volumes:
      - postgres-db-volume:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 5s
      retries: 5
    restart: always

  redis:
    image: redis:latest
    expose:
      - 6379
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 30s
      retries: 50
    restart: always

  airflow-webserver:
    <<: *airflow-common
    command: webserver
    ports:
      - 8080:8080
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8080/health"]
      interval: 10s
      timeout: 10s
      retries: 5
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-scheduler:
    <<: *airflow-common
    command: scheduler
    healthcheck:
      test: ["CMD-SHELL", 'airflow jobs check --job-type SchedulerJob --hostname "$${HOSTNAME}"']
      interval: 10s
      timeout: 10s
      retries: 5
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-worker:
    <<: *airflow-common
    command: celery worker
    healthcheck:
      test:
        - "CMD-SHELL"
        - 'celery --app airflow.executors.celery_executor.app inspect ping -d "celery@$${HOSTNAME}"'
      interval: 10s
      timeout: 10s
      retries: 5
    environment:
      <<: *airflow-common-env
      DUMB_INIT_SETSID: "0"
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-triggerer:
    <<: *airflow-common
    command: triggerer
    healthcheck:
      test: ["CMD-SHELL", 'airflow jobs check --job-type TriggererJob --hostname "$${HOSTNAME}"']
      interval: 10s
      timeout: 10s
      retries: 5
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-init:
    <<: *airflow-common
    entrypoint: /bin/bash
    command:
      - -c
      - |
        mkdir -p /sources/logs /sources/dags /sources/plugins
        chown -R "${AIRFLOW_UID}:0" /sources/{logs,dags,plugins}
        exec /entrypoint airflow version
    environment:
      <<: *airflow-common-env
      _AIRFLOW_DB_UPGRADE: 'true'
      _AIRFLOW_WWW_USER_CREATE: 'true'
      _AIRFLOW_WWW_USER_USERNAME: ${_AIRFLOW_WWW_USER_USERNAME:-airflow}
      _AIRFLOW_WWW_USER_PASSWORD: ${_AIRFLOW_WWW_USER_PASSWORD:-airflow}
    user: "0:0"
    volumes:
      - .:/sources

  airflow-cli:
    <<: *airflow-common
    profiles:
      - debug
    environment:
      <<: *airflow-common-env
      CONNECTION_CHECK_MAX_COUNT: "0"
    command:
      - bash
      - -c
      - airflow

  flower:
    <<: *airflow-common
    command: celery flower
    ports:
      - 5555:5555
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:5555/"]
      interval: 10s
      timeout: 10s
      retries: 5
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

volumes:
  postgres-db-volume:
```

**Kubernetes (Large Production):**

```bash
# Install Airflow with Helm
helm repo add apache-airflow https://airflow.apache.org
helm repo update

helm install airflow apache-airflow/airflow \
    --namespace airflow \
    --create-namespace \
    --set executor=KubernetesExecutor \
    --set postgresql.enabled=true \
    --set redis.enabled=false \
    --values values.yaml
```

```yaml
# values.yaml
defaultAirflowRepository: apache/airflow
defaultAirflowTag: "2.8.1"

executor: "KubernetesExecutor"

fernetKey: "YOUR_FERNET_KEY"
webserverSecretKey: "YOUR_SECRET_KEY"

postgresql:
  enabled: true
  postgresqlUsername: airflow
  postgresqlPassword: airflow
  postgresqlDatabase: airflow

dags:
  persistence:
    enabled: true
    storageClassName: standard
    accessMode: ReadWriteMany
    size: 10Gi
  gitSync:
    enabled: true
    repo: https://github.com/your-org/airflow-dags.git
    branch: main
    rev: HEAD
    depth: 1
    wait: 60

webserver:
  replicas: 2
  resources:
    limits:
      cpu: 2000m
      memory: 4Gi
    requests:
      cpu: 500m
      memory: 1Gi

scheduler:
  replicas: 2
  resources:
    limits:
      cpu: 2000m
      memory: 4Gi
    requests:
      cpu: 500m
      memory: 1Gi

workers:
  replicas: 3
  resources:
    limits:
      cpu: 4000m
      memory: 8Gi
    requests:
      cpu: 1000m
      memory: 2Gi
```

---

## High Availability

### Database HA

**PostgreSQL Master-Replica:**

```yaml
# Patroni for PostgreSQL HA
apiVersion: v1
kind: Service
metadata:
  name: postgres-ha
spec:
  selector:
    app: postgres
  ports:
    - port: 5432
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres-ha
spec:
  serviceName: postgres-ha
  replicas: 3
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:13
          # Patroni configuration for automatic failover
```

### Scheduler HA

**Active-Standby with Health Checks:**

```python
# airflow.cfg
[scheduler]
scheduler_health_check_threshold = 30

# Multiple schedulers (Airflow 2.0+)
# Run multiple scheduler instances
# They coordinate via database locks
```

```bash
# Start multiple schedulers
airflow scheduler --daemon
airflow scheduler --daemon
```

### Web Server HA

**Load Balancer + Multiple Instances:**

```yaml
# K8s Service with multiple replicas
apiVersion: v1
kind: Service
metadata:
  name: airflow-webserver
spec:
  type: LoadBalancer
  selector:
    component: webserver
  ports:
    - port: 8080
      targetPort: 8080
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: airflow-webserver
spec:
  replicas: 3  # Multiple instances
  selector:
    matchLabels:
      component: webserver
  template:
    # ...webserver pod spec
```

---

## Scaling Strategies

### Horizontal Scaling (Celery)

**Add More Workers:**

```bash
# Start additional worker with specific queue
airflow celery worker --queues default,high_priority

# Start worker on different machine
airflow celery worker --hostname worker-02
```

**Queue-Based Routing:**

```python
# Assign tasks to specific queues
high_priority_task = PythonOperator(
    task_id='urgent_task',
    python_callable=urgent_function,
    queue='high_priority',  # Dedicated queue
    priority_weight=10,     # Higher priority
)

low_priority_task = PythonOperator(
    task_id='background_task',
    python_callable=background_function,
    queue='low_priority',
    priority_weight=1,
)
```

**Worker Pools:**

```python
# airflow.cfg
[core]
parallelism = 128  # Max tasks simultaneously

[celery]
worker_concurrency = 16  # Tasks per worker
```

### Auto-Scaling (Kubernetes)

**Kubernetes HPA (Horizontal Pod Autoscaler):**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: airflow-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: airflow-worker
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

### KubernetesExecutor Auto-Scaling

```python
# Each task = ephemeral pod
# Kubernetes auto-scales based on pod requests

from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator

task = KubernetesPodOperator(
    task_id='k8s_task',
    namespace='airflow',
    image='python:3.11',
    cmds=['python', '-c', 'print("Hello")'],
    resources={
        'request_memory': '512Mi',
        'request_cpu': '500m',
        'limit_memory': '2Gi',
        'limit_cpu': '2000m',
    },
    # Pod auto-created and auto-deleted
    is_delete_operator_pod=True,
)
```

---

## Secrets Management

### Environment Variables

```bash
# .env file (not committed to git)
AIRFLOW__CORE__FERNET_KEY=your_fernet_key
AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://user:pass@host/db
AIRFLOW__CELERY__BROKER_URL=redis://redis:6379/0
API_KEY=your_api_key
DB_PASSWORD=your_db_password
```

```python
# Use in DAG
import os

api_key = os.getenv('API_KEY')
```

### Airflow Variables (Encrypted)

```python
# Set sensitive variable (encrypted in DB)
airflow variables set api_key "your_secret_key"

# Use in DAG
from airflow.models import Variable

api_key = Variable.get('api_key')
```

### Airflow Connections (Encrypted)

```bash
# Set connection via CLI
airflow connections add 'my_db' \
    --conn-type 'postgres' \
    --conn-host 'db.example.com' \
    --conn-schema 'mydb' \
    --conn-login 'user' \
    --conn-password 'password' \
    --conn-port '5432'
```

### Secrets Backend

**AWS Secrets Manager:**

```python
# airflow.cfg
[secrets]
backend = airflow.providers.amazon.aws.secrets.secrets_manager.SecretsManagerBackend
backend_kwargs = {"connections_prefix": "airflow/connections", "variables_prefix": "airflow/variables"}
```

```python
# Store in AWS Secrets Manager
aws secretsmanager create-secret \
    --name airflow/variables/api_key \
    --secret-string "your_secret_key"

# Airflow automatically fetches from AWS
api_key = Variable.get('api_key')  # Retrieved from Secrets Manager
```

**HashiCorp Vault:**

```python
# airflow.cfg
[secrets]
backend = airflow.providers.hashicorp.secrets.vault.VaultBackend
backend_kwargs = {
    "url": "http://vault:8200",
    "token": "your_vault_token",
    "connections_path": "airflow/connections",
    "variables_path": "airflow/variables"
}
```

**Google Secret Manager:**

```python
# airflow.cfg
[secrets]
backend = airflow.providers.google.cloud.secrets.secret_manager.CloudSecretManagerBackend
backend_kwargs = {"connections_prefix": "airflow-connections", "variables_prefix": "airflow-variables", "sep": "-"}
```

### Fernet Key

```bash
# Generate Fernet key for encryption
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Set in airflow.cfg
[core]
fernet_key = YOUR_GENERATED_KEY
```

---

## Monitoring & Observability

### Airflow Metrics

**StatsD Integration:**

```python
# airflow.cfg
[scheduler]
statsd_on = True
statsd_host = localhost
statsd_port = 8125
statsd_prefix = airflow
```

**Key Metrics:**

- `airflow.dagrun.duration.<dag_id>` - DAG duration
- `airflow.dagrun.schedule_delay.<dag_id>` - Scheduling delay
- `airflow.task_instance.duration.<dag_id>.<task_id>` - Task duration
- `airflow.scheduler.heartbeat` - Scheduler health
- `airflow.executor.open_slots` - Available slots
- `airflow.executor.queued_tasks` - Queued tasks
- `airflow.executor.running_tasks` - Running tasks

**Prometheus Integration:**

```python
# Install prometheus exporter
pip install apache-airflow[statsd]

# Use prometheus_client
from prometheus_client import Counter, Histogram

task_counter = Counter('airflow_task_executions', 'Total task executions')
task_duration = Histogram('airflow_task_duration_seconds', 'Task duration')

def my_function():
    task_counter.inc()
    with task_duration.time():
        # Task logic
        pass
```

### Logging

**Centralized Logging:**

```python
# airflow.cfg
[logging]
remote_logging = True
remote_base_log_folder = s3://my-airflow-logs
remote_log_conn_id = aws_default

# Or Google Cloud Storage
# remote_base_log_folder = gs://my-airflow-logs
# remote_log_conn_id = google_cloud_default
```

**Structured Logging:**

```python
import logging

def my_function(**context):
    logger = logging.getLogger(__name__)
    logger.info('Processing started', extra={
        'dag_id': context['dag'].dag_id,
        'task_id': context['task'].task_id,
        'execution_date': str(context['execution_date']),
    })
```

**Log Aggregation (ELK Stack):**

```yaml
# Logstash config
input {
  file {
    path => "/opt/airflow/logs/**/*.log"
    type => "airflow"
  }
}

filter {
  grok {
    match => { "message" => "%{TIMESTAMP_ISO8601:timestamp} - %{LOGLEVEL:level} - %{GREEDYDATA:message}" }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "airflow-logs-%{+YYYY.MM.dd}"
  }
}
```

### Health Checks

**Scheduler Health:**

```bash
# Check scheduler is running
airflow jobs check --job-type SchedulerJob --hostname "$HOSTNAME"
```

**Web Server Health:**

```bash
# Health endpoint
curl http://localhost:8080/health
```

**Database Connection Pool:**

```python
# airflow.cfg
[core]
sql_alchemy_pool_size = 5
sql_alchemy_max_overflow = 10
sql_alchemy_pool_recycle = 3600
```

---

## Alerting

### SLA (Service Level Agreement)

```python
from datetime import timedelta

task = PythonOperator(
    task_id='sla_task',
    python_callable=my_function,
    sla=timedelta(hours=2),  # Alert if not done in 2 hours
)

def sla_miss_callback(dag, task_list, blocking_task_list, slas, blocking_tis):
    # Send alert
    send_slack_notification(
        f"SLA miss for tasks: {[t.task_id for t in task_list]}"
    )

dag = DAG(
    'with_sla',
    sla_miss_callback=sla_miss_callback,
    ...
)
```

### Email Alerts

```python
# airflow.cfg
[smtp]
smtp_host = smtp.gmail.com
smtp_starttls = True
smtp_ssl = False
smtp_user = your_email@gmail.com
smtp_password = your_password
smtp_port = 587
smtp_mail_from = airflow@example.com

# In DAG
default_args = {
    'email': ['team@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
}
```

### Custom Callbacks

```python
def task_failure_callback(context):
    task_instance = context['task_instance']
    exception = context.get('exception')

    # Send to Slack
    send_slack_message(
        f"❌ Task Failed: {task_instance.task_id}\n"
        f"DAG: {task_instance.dag_id}\n"
        f"Error: {exception}"
    )

def dag_success_callback(context):
    dag_run = context['dag_run']
    send_slack_message(f"✅ DAG {dag_run.dag_id} completed successfully")

task = PythonOperator(
    task_id='monitored_task',
    python_callable=my_function,
    on_failure_callback=task_failure_callback,
)

dag = DAG(
    'monitored_dag',
    on_success_callback=dag_success_callback,
    on_failure_callback=task_failure_callback,
    ...
)
```

### Slack Integration

```python
from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator

def notify_slack(context):
    slack_msg = """
    :red_circle: Task Failed.
    *Task*: {task}
    *Dag*: {dag}
    *Execution Time*: {exec_date}
    *Log Url*: {log_url}
    """.format(
        task=context.get('task_instance').task_id,
        dag=context.get('task_instance').dag_id,
        exec_date=context.get('execution_date'),
        log_url=context.get('task_instance').log_url,
    )

    slack_alert = SlackWebhookOperator(
        task_id='slack_notification',
        http_conn_id='slack_webhook',
        message=slack_msg,
    )
    return slack_alert.execute(context=context)

task = PythonOperator(
    task_id='important_task',
    python_callable=my_function,
    on_failure_callback=notify_slack,
)
```

### PagerDuty Integration

```python
from airflow.providers.pagerduty.hooks.pagerduty import PagerdutyHook

def pagerduty_alert(context):
    hook = PagerdutyHook(token='YOUR_PAGERDUTY_TOKEN')
    hook.create_event(
        summary=f"Airflow Task Failed: {context['task_instance'].task_id}",
        severity='error',
        source='airflow',
        action='trigger',
    )

task = PythonOperator(
    task_id='critical_task',
    python_callable=critical_function,
    on_failure_callback=pagerduty_alert,
)
```

---

## Performance Optimization

### DAG File Optimization

**Avoid Top-Level Code:**

```python
# ❌ Bad: Executed every scheduler cycle
import requests

response = requests.get('http://api.example.com/data')
data = response.json()

dag = DAG('my_dag', ...)

# ✅ Good: Move to task
def fetch_data():
    response = requests.get('http://api.example.com/data')
    return response.json()

dag = DAG('my_dag', ...)
task = PythonOperator(task_id='fetch', python_callable=fetch_data)
```

**Use `.airflowignore`:**

```
# .airflowignore
__pycache__
*.pyc
tests/
docs/
```

### Database Optimization

```python
# airflow.cfg
[core]
sql_alchemy_pool_size = 10
sql_alchemy_max_overflow = 20
sql_alchemy_pool_recycle = 1800

[scheduler]
dag_dir_list_interval = 300  # Parse DAGs every 5 min
min_file_process_interval = 60
```

**Connection Pooling:**

```python
# Use connection pooling for external DBs
from airflow.hooks.base import BaseHook
from sqlalchemy import create_engine

def get_db_engine():
    conn = BaseHook.get_connection('my_db')
    engine = create_engine(
        conn.get_uri(),
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
    )
    return engine
```

### Task Parallelism

```python
# airflow.cfg
[core]
parallelism = 64  # Max tasks across all DAGs
dag_concurrency = 16  # Max tasks per DAG
max_active_runs_per_dag = 4  # Max active DagRuns

# Per-DAG override
dag = DAG(
    'parallel_dag',
    max_active_runs=10,
    concurrency=32,
    ...
)
```

### Resource Management

**Task Pools:**

```python
# Create pool via UI or CLI
airflow pools set db_pool 5 "Database connection pool"

# Assign tasks to pool
task = PythonOperator(
    task_id='db_task',
    python_callable=query_database,
    pool='db_pool',  # Limited to 5 concurrent
)
```

**Task Priority:**

```python
# Higher priority tasks execute first
high_priority = PythonOperator(
    task_id='urgent',
    python_callable=urgent_task,
    priority_weight=10,
    pool='shared_pool',
)

low_priority = PythonOperator(
    task_id='background',
    python_callable=background_task,
    priority_weight=1,
    pool='shared_pool',
)
```

---

## Security Best Practices

### RBAC (Role-Based Access Control)

```python
# airflow.cfg
[webserver]
rbac = True
auth_backend = airflow.contrib.auth.backends.password_auth

# Or use OAuth/LDAP
# auth_backend = airflow.contrib.auth.backends.google_auth
```

**Create Roles:**

```bash
# Via CLI
airflow roles create DataScientist

# Assign permissions
airflow roles add-perms DataScientist \
    can_read on DAGs \
    can_edit on DAG:my_dag \
    can_read on Task Instances
```

### Network Security

**Restrict Web Server Access:**

```python
# airflow.cfg
[webserver]
web_server_host = 127.0.0.1  # Localhost only
web_server_port = 8080

# Use reverse proxy (nginx) for external access
```

**SSL/TLS:**

```python
# airflow.cfg
[webserver]
web_server_ssl_cert = /path/to/cert.pem
web_server_ssl_key = /path/to/key.pem
```

### Secrets Rotation

**Automate Secret Rotation:**

```python
from airflow.models import Variable
import boto3

def rotate_api_key():
    # Generate new key
    new_key = generate_new_api_key()

    # Update in Secrets Manager
    client = boto3.client('secretsmanager')
    client.update_secret(
        SecretId='airflow/variables/api_key',
        SecretString=new_key
    )

    # Clear cached variable
    Variable.set('api_key', new_key)

rotate_task = PythonOperator(
    task_id='rotate_secrets',
    python_callable=rotate_api_key,
)
```

### Audit Logging

```python
# Enable audit logs
# airflow.cfg
[core]
expose_config = False  # Don't expose config in UI

# Log all API calls
[api]
auth_backend = airflow.api.auth.backend.basic_auth
```

---

## CI/CD for DAGs

### DAG Testing

```python
# tests/test_dags.py
import pytest
from airflow.models import DagBag

def test_no_import_errors():
    """Test that all DAGs can be imported without errors"""
    dag_bag = DagBag()
    assert len(dag_bag.import_errors) == 0, f"Import errors: {dag_bag.import_errors}"

def test_dag_integrity():
    """Test DAG integrity"""
    dag_bag = DagBag()

    for dag_id, dag in dag_bag.dags.items():
        # No cycles
        assert dag.test_cycle() is None, f"Cycle detected in {dag_id}"

        # Has tags
        assert len(dag.tags) > 0, f"DAG {dag_id} missing tags"

        # Has owner
        assert dag.default_args.get('owner') is not None

def test_specific_dag():
    """Test specific DAG structure"""
    dag_bag = DagBag()
    dag = dag_bag.get_dag('my_dag')

    assert dag is not None
    assert len(dag.tasks) == 5
    assert 'extract' in dag.task_ids
```

### Integration Testing

```python
# tests/test_integration.py
from airflow.models import DagBag
from airflow.utils.dates import days_ago

def test_dag_run():
    """Test full DAG execution"""
    dag_bag = DagBag()
    dag = dag_bag.get_dag('my_dag')

    # Create test DagRun
    dag.test(execution_date=days_ago(1))

def test_task_execution():
    """Test individual task"""
    from airflow.operators.python import PythonOperator

    def mock_function():
        return "test_result"

    task = PythonOperator(
        task_id='test_task',
        python_callable=mock_function,
    )

    result = task.execute(context={})
    assert result == "test_result"
```

### CI Pipeline (GitHub Actions)

```yaml
# .github/workflows/test-dags.yml
name: Test DAGs

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install apache-airflow==2.8.1
          pip install pytest pytest-cov
          pip install -r requirements.txt

      - name: Initialize Airflow DB
        run: airflow db init

      - name: Run Tests
        run: |
          pytest tests/ -v --cov=dags --cov-report=xml

      - name: Lint DAGs
        run: |
          pip install flake8
          flake8 dags/ --max-line-length=120

      - name: Upload Coverage
        uses: codecov/codecov-action@v2
        with:
          file: ./coverage.xml
```

### CD Pipeline

```yaml
# .github/workflows/deploy-dags.yml
name: Deploy DAGs

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Deploy to Airflow
        run: |
          # Sync DAGs to S3 (or other storage)
          aws s3 sync dags/ s3://my-airflow-dags/dags/

          # Or: Git sync (if using GitSync)
          # Git push triggers automatic sync in Airflow

      - name: Notify Slack
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK }}
          payload: |
            {
              "text": "DAGs deployed to production successfully"
            }
```

---

## Common Anti-Patterns

### ❌ Anti-Pattern 1: Top-Level Code

**Bad:**

```python
# Executed every scheduler cycle!
import pandas as pd

df = pd.read_csv('large_file.csv')  # Don't do this
processed = df.groupby('col').sum()

dag = DAG('my_dag', ...)
```

**Good:**

```python
dag = DAG('my_dag', ...)

def process_data():
    df = pd.read_csv('large_file.csv')
    return df.groupby('col').sum()

task = PythonOperator(task_id='process', python_callable=process_data)
```

### ❌ Anti-Pattern 2: Dynamic DAG IDs

**Bad:**

```python
import random

dag = DAG(
    dag_id=f'my_dag_{random.randint(1, 100)}',  # Different every time!
    ...
)
```

**Good:**

```python
dag = DAG(
    dag_id='my_dag',  # Static ID
    ...
)
```

### ❌ Anti-Pattern 3: Large XComs

**Bad:**

```python
def extract():
    data = fetch_100mb_dataset()
    return data  # XCom stores in DB!
```

**Good:**

```python
def extract():
    data = fetch_100mb_dataset()
    path = '/tmp/data.parquet'
    data.to_parquet(path)
    return path  # Store path, not data
```

### ❌ Anti-Pattern 4: Sequential Tasks (could be parallel)

**Bad:**

```python
task1 >> task2 >> task3 >> task4  # All sequential
```

**Good:**

```python
start >> [task1, task2, task3, task4] >> end  # Parallel
```

### ❌ Anti-Pattern 5: No Error Handling

**Bad:**

```python
def my_function():
    result = api_call()  # No error handling
    return result
```

**Good:**

```python
def my_function():
    try:
        result = api_call()
        return result
    except APIException as e:
        logger.error(f"API call failed: {e}")
        raise  # Let Airflow handle retry
```

---

## Summary

**Production Checklist:**

✅ **Deployment**
- [ ] Use Docker Compose or Kubernetes
- [ ] PostgreSQL for metadata DB
- [ ] Redis for Celery broker
- [ ] Multiple web servers (HA)
- [ ] Multiple schedulers (HA)

✅ **Scaling**
- [ ] Celery workers or KubernetesExecutor
- [ ] Queue-based task routing
- [ ] Auto-scaling for workers
- [ ] Connection pools

✅ **Secrets**
- [ ] Environment variables for config
- [ ] Secrets backend (AWS/Vault/GCP)
- [ ] Encrypted Variables/Connections
- [ ] Fernet key rotation

✅ **Monitoring**
- [ ] StatsD/Prometheus metrics
- [ ] Centralized logging (S3/GCS/ELK)
- [ ] Health checks
- [ ] Dashboards (Grafana)

✅ **Alerting**
- [ ] SLA monitoring
- [ ] Email/Slack notifications
- [ ] Custom callbacks
- [ ] PagerDuty for critical

✅ **Performance**
- [ ] Optimized DAG files
- [ ] Database tuning
- [ ] Task parallelism
- [ ] Resource pools

✅ **Security**
- [ ] RBAC enabled
- [ ] SSL/TLS for web server
- [ ] Network restrictions
- [ ] Audit logging

✅ **CI/CD**
- [ ] DAG tests
- [ ] Linting
- [ ] Automated deployment
- [ ] Rollback strategy

---

**Document**: 03-production-patterns.md
**Words**: ~4,500
**Level**: Advanced
**Prerequisites**: 01-airflow-fundamentals.md, 02-dags-and-operators.md
