# Airflow Fundamentals

## 📋 Table of Contents

1. [What is Apache Airflow?](#what-is-apache-airflow)
2. [Core Concepts](#core-concepts)
3. [Architecture](#architecture)
4. [Components Deep Dive](#components-deep-dive)
5. [Scheduling & Execution](#scheduling--execution)
6. [Setup & Configuration](#setup--configuration)
7. [First Steps](#first-steps)

---

## What is Apache Airflow?

### Overview

**Apache Airflow** es una plataforma open-source para **authoring, scheduling y monitoring** de workflows programáticamente. Fue creado por Airbnb en 2014 y se convirtió en proyecto de Apache en 2016.

### Key Features

✅ **Dynamic Pipeline Generation**: DAGs son definidos en Python, lo que permite generación dinámica
✅ **Extensible**: Rico conjunto de operadores y fácil creación de custom operators
✅ **Elegant UI**: Web interface para visualizar, monitorear y troubleshoot pipelines
✅ **Scalable**: Arquitectura modular que escala horizontalmente
✅ **Rich Scheduling**: Expresiones cron, intervals, backfilling
✅ **Dependency Management**: Define dependencias complejas entre tasks

### When to Use Airflow

**✅ Use Airflow for:**
- Batch data processing pipelines
- ETL/ELT workflows
- Machine Learning pipelines
- Data warehouse maintenance
- Scheduled reports
- Complex dependency management

**❌ Don't use Airflow for:**
- streaming data (use Kafka, Flink, Spark Streaming)
- Event-driven workflows (consider AWS Step Functions, Temporal)
- Simple cron jobs (overkill)
- Real-time processing

### Airflow vs Others

| Feature | Airflow | Luigi | Prefect | Dagster |
|---------|---------|-------|---------|---------|
| UI | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Scheduling | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Community | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Learning Curve | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Cloud Native | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## Core Concepts

### DAG (Directed Acyclic Graph)

Un **DAG** es la unidad fundamental en Airflow que representa un workflow.

**Características:**
- **Directed**: Tasks tienen orden específico
- **Acyclic**: No loops/cycles
- **Graph**: Conjunto de tasks y sus dependencias

**Ejemplo Conceptual:**

```
    start
      ↓
  extract_data
      ↓
  transform_data
      ↓
   load_data
      ↓
     end
```

### Tasks

**Task** es una unidad de trabajo dentro de un DAG.

**Tipos:**
- **Operator**: Realiza acción específica (PythonOperator, BashOperator)
- **Sensor**: Espera por condición (FileSensor, HttpSensor)
- **TaskFlow**: Decorador `@task` (Airflow 2.0+)

**Task Instance**: Ejecución específica de un task en un momento dado.

### Operators

**Operators** determinan qué hace cada task.

**Categorías:**

1. **Action Operators** - Ejecutan acciones
   - `PythonOperator`: Ejecuta función Python
   - `BashOperator`: Ejecuta comando bash
   - `EmailOperator`: Envía email
   - `SimpleHttpOperator`: HTTP request

2. **Transfer Operators** - Mueven datos
   - `S3ToRedshiftOperator`
   - `MySqlToS3Operator`
   - `LocalFilesystemToS3Operator`

3. **Sensors** - Esperan por evento
   - `FileSensor`: Espera archivo
   - `HttpSensor`: Espera respuesta HTTP
   - `ExternalTaskSensor`: Espera otro task
   - `TimeDeltaSensor`: Espera tiempo

### Scheduler

**Scheduler** es el corazón de Airflow que:

1. Monitorea DAGs y tasks
2. Dispara task instances cuando dependencias se cumplen
3. Respeta schedule intervals
4. Maneja backfilling

**Execution Date vs Run Date:**
- **Execution Date**: Fecha lógica del periodo de datos (ej: 2024-01-01)
- **Run Date**: Fecha real cuando el DAG ejecuta (ej: 2024-01-02 00:05)

### Executor

**Executor** determina cómo tasks son ejecutados.

**Tipos:**

1. **SequentialExecutor** (default)
   - Ejecuta tasks secuencialmente
   - Solo para testing/desarrollo
   - SQLite backend

2. **LocalExecutor**
   - Ejecuta tasks en paralelo localmente
   - Usa multiprocessing
   - PostgreSQL/MySQL required

3. **CeleryExecutor**
   - Distribuido, escala horizontalmente
   - Workers en múltiples máquinas
   - Redis/RabbitMQ message broker

4. **KubernetesExecutor**
   - Cada task en pod separado
   - Auto-scaling
   - Resource isolation

5. **DaskExecutor**
   - Usa Dask para distribución
   - Good for data science workflows

**Comparison:**

| Executor | Parallelism | Scaling | Use Case |
|----------|-------------|---------|----------|
| Sequential | No | - | Dev/Testing |
| Local | Yes (limited) | Vertical | Small prod |
| Celery | Yes | Horizontal | Large prod |
| Kubernetes | Yes | Auto | Cloud-native |

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Web Server (UI)                     │
│                   (Flask Application)                   │
└─────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────┐
│                   Metadata Database                     │
│              (PostgreSQL / MySQL)                       │
│  - DAG definitions, task states, logs, users, etc.     │
└─────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────┐
│                      Scheduler                          │
│  1. Parse DAG files                                     │
│  2. Monitor task dependencies                           │
│  3. Trigger task instances                              │
│  4. Update metadata database                            │
└─────────────────────────────────────────────────────────┘
                            ↓
                      ┌──────────┐
                      │ Executor │
                      └──────────┘
                            ↓
           ┌─────────────┬──────────────┬──────────────┐
           ↓             ↓              ↓              ↓
      ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐
      │ Worker │    │ Worker │    │ Worker │    │ Worker │
      │   #1   │    │   #2   │    │   #3   │    │   #N   │
      └────────┘    └────────┘    └────────┘    └────────┘
```

### Components Interaction

**1. DAG Authoring:**
```python
# Developer writes DAG in Python
# File stored in: $AIRFLOW_HOME/dags/my_dag.py

from airflow import DAG
from airflow.operators.python import PythonOperator

dag = DAG('my_dag', schedule='@daily')
task1 = PythonOperator(task_id='task1', python_callable=my_function, dag=dag)
```

**2. Scheduler Parsing:**
- Scheduler scans `dags/` folder
- Parses Python files to find DAGs
- Stores DAG metadata in database
- Creates DagRun instances based on schedule

**3. Task Execution:**
- Scheduler checks task dependencies
- Submits task to Executor
- Executor assigns task to Worker
- Worker executes task
- Results stored in metadata DB

**4. Monitoring:**
- Web server reads metadata DB
- Displays DAG runs, task states
- Shows logs, metrics, graphs

### Metadata Database Schema

**Key Tables:**

**`dag`**
- DAG definitions
- Schedule interval, default args

**`dag_run`**
- Instances of DAG executions
- State: running, success, failed
- Execution date

**`task_instance`**
- Instances of task executions
- State: queued, running, success, failed, skipped
- Start/end time, duration
- Tries/retries

**`task_fail`**
- Failed task attempts details

**`log`**
- Task execution logs

**`connection`**
- External connection configs
- Databases, APIs, cloud services

**`variable`**
- Key-value store for config

**`xcom`**
- Cross-communication between tasks

### DAG Processing Flow

```
1. DAG File Created
        ↓
2. Scheduler Scans dags/ Folder
        ↓
3. Parse Python Files (DagBag)
        ↓
4. Validate DAG Structure
        ↓
5. Store in Metadata DB
        ↓
6. Create DagRun (based on schedule)
        ↓
7. Create TaskInstances
        ↓
8. Queue Tasks (executor)
        ↓
9. Workers Execute Tasks
        ↓
10. Update Task States
        ↓
11. Web UI Displays Status
```

---

## Components Deep Dive

### Web Server

**Purpose**: Provide UI for monitoring and managing DAGs.

**Features:**
- **DAG View**: List of all DAGs, states, schedules
- **Tree View**: Hierarchical task execution view
- **Graph View**: Visual DAG dependencies
- **Gantt View**: Task execution timeline
- **Task Instance Details**: Logs, duration, retries
- **Variables Management**: CRUD operations
- **Connections Management**: External system configs
- **Admin Panel**: Users, roles, permissions

**Technologies:**
- Built on Flask
- Gunicorn WSGI server
- Authentication: LDAP, OAuth, Basic Auth, etc.

**Configuration:**

```python
# airflow.cfg
[webserver]
web_server_port = 8080
workers = 4
worker_class = sync
secret_key = my_secret_key
authenticate = True
auth_backend = airflow.contrib.auth.backends.password_auth
```

### Scheduler

**Responsibilities:**

1. **DAG Parsing**
   - Scan `dags/` folder every `dag_dir_list_interval` seconds
   - Parse Python files
   - Build DAG objects

2. **DagRun Creation**
   - Based on `schedule_interval`
   - Create DagRun for each execution date
   - Mark as "running"

3. **Task Scheduling**
   - Check task dependencies (upstream tasks)
   - Check task state (not already running/complete)
   - Submit to executor queue

4. **State Management**
   - Update task instance states
   - Mark DagRun as success/failed
   - Trigger callbacks (on_success, on_failure)

**Key Configuration:**

```python
# airflow.cfg
[scheduler]
scheduler_heartbeat_sec = 5
dag_dir_list_interval = 300  # 5 minutes
max_threads = 2
catchup_by_default = True
```

**Scheduler Loop:**

```python
while True:
    # 1. Heartbeat (check if scheduler is alive)
    record_heartbeat()

    # 2. Parse DAGs
    dag_bag = DagBag(dag_folder)

    # 3. Create DagRuns for each DAG
    for dag in dag_bag.dags:
        create_dag_run_if_needed(dag)

    # 4. Schedule tasks
    task_instances = get_schedulable_task_instances()
    for ti in task_instances:
        executor.queue_task(ti)

    # 5. Update task states
    executor.heartbeat()

    # 6. Process executor feedback
    process_executor_events()

    time.sleep(scheduler_heartbeat_sec)
```

### Executor

#### LocalExecutor

**How it works:**
- Uses Python `multiprocessing.Pool`
- Each task = subprocess
- Parallelism limited by CPU cores

**Configuration:**

```python
# airflow.cfg
[core]
executor = LocalExecutor
parallelism = 32
dag_concurrency = 16
max_active_runs_per_dag = 16

[celery]
# Not used with LocalExecutor
```

**Pros:**
- Simple setup
- Good for small/medium workloads
- No additional services needed

**Cons:**
- Limited scaling (single machine)
- No task isolation (shared resources)

#### CeleryExecutor

**How it works:**
- Distributed task queue
- Workers on multiple machines
- Message broker (Redis/RabbitMQ) for task distribution

**Architecture:**

```
Scheduler → Celery Broker (Redis) → Celery Workers
              ↓
        (Task Queue)
              ↓
   [Worker 1] [Worker 2] [Worker N]
```

**Setup:**

1. **Install Celery:**
```bash
pip install 'apache-airflow[celery]'
```

2. **Configure Broker:**
```python
# airflow.cfg
[celery]
broker_url = redis://localhost:6379/0
result_backend = db+postgresql://user:pass@localhost/airflow
```

3. **Start Workers:**
```bash
airflow celery worker
```

4. **Monitor:**
```bash
airflow celery flower  # Web UI on port 5555
```

**Pros:**
- Horizontal scaling
- Good for large workloads
- Task isolation

**Cons:**
- Complex setup
- Additional services (Redis/RabbitMQ)
- Network overhead

#### KubernetesExecutor

**How it works:**
- Each task = Kubernetes Pod
- Pod created just-in-time
- Pod deleted after task completes

**Configuration:**

```python
# airflow.cfg
[kubernetes]
namespace = airflow
kube_config = /path/to/kubeconfig
worker_container_repository = apache/airflow
worker_container_tag = 2.8.1
delete_worker_pods = True
```

**Pod Template:**

```yaml
# pod_template.yaml
apiVersion: v1
kind: Pod
metadata:
  name: airflow-worker
spec:
  containers:
    - name: base
      image: apache/airflow:2.8.1
      resources:
        requests:
          memory: "512Mi"
          cpu: "500m"
        limits:
          memory: "2Gi"
          cpu: "2000m"
```

**Pros:**
- Auto-scaling
- Resource isolation
- Cloud-native
- No worker management

**Cons:**
- Kubernetes knowledge required
- Pod startup overhead
- Complex debugging

### Workers

**Worker** ejecuta las tareas.

**LocalExecutor Worker:**
```python
# Subprocess executing task
import subprocess

subprocess.run([
    'airflow', 'tasks', 'run',
    'my_dag', 'my_task', '2024-01-01'
])
```

**Celery Worker:**
```bash
# Start worker
airflow celery worker --queues default,high_priority

# Worker polls broker for tasks
# Executes task
# Returns result to result_backend
```

**Kubernetes Worker:**
```yaml
# Ephemeral pod created per task
apiVersion: v1
kind: Pod
metadata:
  name: my-dag-my-task-20240101
spec:
  containers:
    - name: airflow-worker
      image: apache/airflow:2.8.1
      command: ['airflow', 'tasks', 'run', 'my_dag', 'my_task', '2024-01-01']
  restartPolicy: Never
```

---

## Scheduling & Execution

### Schedule Interval

**schedule_interval** determina cuándo un DAG ejecuta.

**Formatos:**

1. **Cron Expression:**
```python
dag = DAG(
    'my_dag',
    schedule='0 0 * * *',  # Daily at midnight
)
```

2. **Preset:**
```python
from airflow.timetables.interval import CronDataIntervalTimetable

dag = DAG(
    'my_dag',
    schedule='@daily',  # Same as '0 0 * * *'
)

# Presets:
# @once - Run once
# @hourly - 0 * * * *
# @daily - 0 0 * * *
# @weekly - 0 0 * * 0
# @monthly - 0 0 1 * *
# @yearly - 0 0 1 1 *
```

3. **Timedelta:**
```python
from datetime import timedelta

dag = DAG(
    'my_dag',
    schedule=timedelta(hours=2),  # Every 2 hours
)
```

4. **None (Manual Trigger):**
```python
dag = DAG(
    'my_dag',
    schedule=None,  # Manual only
)
```

### Execution Date

**Execution Date** (data_interval_start) representa el **periodo de datos** no el tiempo de ejecución.

**Example:**

```
Schedule: @daily
Start Date: 2024-01-01

Execution Timeline:
- Execution Date: 2024-01-01 → Runs: 2024-01-02 00:00:00
- Execution Date: 2024-01-02 → Runs: 2024-01-03 00:00:00
- Execution Date: 2024-01-03 → Runs: 2024-01-04 00:00:00
```

**Why?** El DAG procesa datos del día anterior.

### Catchup & Backfilling

**Catchup**: Si DAG empieza tarde o estuvo pausado, ¿debe ejecutar runs perdidos?

```python
dag = DAG(
    'my_dag',
    start_date=datetime(2024, 1, 1),
    schedule='@daily',
    catchup=True,  # Run all missed runs
)

# If today is 2024-01-10 and DAG never ran:
# Will create 9 DagRuns (2024-01-01 through 2024-01-09)
```

**Backfilling** (manual):

```bash
# Backfill specific range
airflow dags backfill \
    --start-date 2024-01-01 \
    --end-date 2024-01-10 \
    my_dag
```

### Task States

**Lifecycle:**

```
None (not created)
    ↓
Scheduled (queued)
    ↓
Queued (in executor queue)
    ↓
Running (worker executing)
    ↓
┌──────┬────────┬──────────┐
│      │        │          │
Success  Failed  Skipped  UpForRetry
        ↓
    Retry → Running
        ↓
    Failed (max retries)
```

**States:**

- **`success`**: Task completed successfully
- **`running`**: Currently executing
- **`failed`**: Task failed (will not retry)
- **`up_for_retry`**: Failed, will retry
- **`skipped`**: Skipped (branching, trigger rules)
- **`upstream_failed`**: Upstream task failed
- **`queued`**: Waiting in executor queue
- **`scheduled`**: Scheduled but not yet queued
- **`none`**: Not yet created

### Task Retries

```python
from airflow.operators.python import PythonOperator

task = PythonOperator(
    task_id='my_task',
    python_callable=my_function,
    retries=3,  # Retry up to 3 times
    retry_delay=timedelta(minutes=5),  # Wait 5 min between retries
    retry_exponential_backoff=True,  # 5min, 10min, 20min
    max_retry_delay=timedelta(hours=1),  # Max delay
)
```

---

## Setup & Configuration

### Installation

#### Method 1: pip (Local Development)

```bash
# Install Airflow
AIRFLOW_VERSION=2.8.1
PYTHON_VERSION=3.11
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"

# Initialize database
airflow db init

# Create admin user
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com
```

#### Method 2: Docker Compose (Recommended)

```yaml
# docker-compose.yaml
version: '3.8'
services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow

  redis:
    image: redis:latest

  airflow-webserver:
    image: apache/airflow:2.8.1
    depends_on:
      - postgres
      - redis
    environment:
      AIRFLOW__CORE__EXECUTOR: CeleryExecutor
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
      AIRFLOW__CELERY__BROKER_URL: redis://redis:6379/0
    ports:
      - "8080:8080"
    command: webserver

  airflow-scheduler:
    image: apache/airflow:2.8.1
    depends_on:
      - postgres
      - redis
    environment:
      AIRFLOW__CORE__EXECUTOR: CeleryExecutor
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
      AIRFLOW__CELERY__BROKER_URL: redis://redis:6379/0
    command: scheduler

  airflow-worker:
    image: apache/airflow:2.8.1
    depends_on:
      - postgres
      - redis
    environment:
      AIRFLOW__CORE__EXECUTOR: CeleryExecutor
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
      AIRFLOW__CELERY__BROKER_URL: redis://redis:6379/0
    command: celery worker
```

```bash
docker-compose up -d
```

### Directory Structure

```
$AIRFLOW_HOME/
├── airflow.cfg           # Main configuration
├── airflow.db           # SQLite DB (dev only)
├── dags/                # DAG files (.py)
│   ├── my_dag.py
│   └── another_dag.py
├── logs/                # Task execution logs
│   └── my_dag/
│       └── my_task/
│           └── 2024-01-01/
│               └── 1.log
├── plugins/             # Custom plugins
│   ├── operators/
│   ├── sensors/
│   └── hooks/
└── webserver_config.py  # Web server config
```

### Key Configuration

```python
# airflow.cfg

[core]
dags_folder = /opt/airflow/dags
base_log_folder = /opt/airflow/logs
executor = LocalExecutor
sql_alchemy_conn = postgresql+psycopg2://airflow:airflow@postgres/airflow
parallelism = 32                    # Max tasks across all DAGs
dag_concurrency = 16                # Max tasks per DAG
max_active_runs_per_dag = 16       # Max active DagRuns per DAG

[scheduler]
scheduler_heartbeat_sec = 5
dag_dir_list_interval = 300
min_file_process_interval = 30
catchup_by_default = True

[webserver]
web_server_port = 8080
workers = 4
authenticate = True
auth_backend = airflow.contrib.auth.backends.password_auth

[celery]
broker_url = redis://redis:6379/0
result_backend = db+postgresql://airflow:airflow@postgres/airflow
worker_concurrency = 16

[smtp]
smtp_host = smtp.gmail.com
smtp_starttls = True
smtp_ssl = False
smtp_user = your_email@gmail.com
smtp_password = your_password
smtp_port = 587
smtp_mail_from = airflow@example.com
```

---

## First Steps

### Your First DAG

```python
# dags/hello_world.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Default args applied to all tasks
default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email': ['team@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define DAG
dag = DAG(
    'hello_world',
    default_args=default_args,
    description='My first DAG',
    schedule=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['example', 'beginner'],
)

# Task 1: Python function
def print_hello():
    print("Hello from Airflow!")
    return "Hello World"

task1 = PythonOperator(
    task_id='print_hello',
    python_callable=print_hello,
    dag=dag,
)

# Task 2: Bash command
task2 = BashOperator(
    task_id='print_date',
    bash_command='date',
    dag=dag,
)

# Task 3: Python with context
def print_context(**context):
    print(f"Execution date: {context['execution_date']}")
    print(f"DAG run ID: {context['run_id']}")
    return "Context printed"

task3 = PythonOperator(
    task_id='print_context',
    python_callable=print_context,
    provide_context=True,
    dag=dag,
)

# Set dependencies
task1 >> task2 >> task3
# Equivalent to:
# task1.set_downstream(task2)
# task2.set_downstream(task3)
```

### Run Your DAG

```bash
# Test task locally (no scheduler)
airflow tasks test hello_world print_hello 2024-01-01

# Trigger DAG manually
airflow dags trigger hello_world

# Backfill
airflow dags backfill hello_world --start-date 2024-01-01 --end-date 2024-01-10

# List DAGs
airflow dags list

# Pause/Unpause
airflow dags pause hello_world
airflow dags unpause hello_world
```

### Access UI

```bash
# Start webserver
airflow webserver --port 8080

# In browser: http://localhost:8080
# Login with admin credentials
```

**UI Navigation:**
1. **DAGs List**: See all DAGs, states, schedules
2. **Click DAG**: View details
3. **Graph View**: Visualize task dependencies
4. **Tree View**: See historical runs
5. **Click Task**: View logs, details

---

## Summary

**Key Takeaways:**

✅ Airflow = Workflow orchestration platform
✅ DAG = Directed Acyclic Graph (workflow)
✅ Task = Unit of work (Operators, Sensors)
✅ Scheduler = Monitors and triggers tasks
✅ Executor = Determines how tasks run
✅ Web Server = UI for monitoring

**Architecture:**
```
Web Server ⟷ Metadata DB ⟷ Scheduler → Executor → Workers
```

**Next Steps:**
- Learn DAGs and Operators in depth
- Understand TaskFlow API
- Explore production patterns

---

**Document**: 01-airflow-fundamentals.md
**Words**: ~5,000
**Level**: Beginner-Intermediate
**Next**: [02-dags-and-operators.md](02-dags-and-operators.md)
