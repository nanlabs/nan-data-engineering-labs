# DAGs and Operators

## 📋 Table of Contents

1. [DAG Creation Patterns](#dag-creation-patterns)
2. [Task Dependencies](#task-dependencies)
3. [Operators Deep Dive](#operators-deep-dive)
4. [Sensors](#sensors)
5. [XComs](#xcoms)
6. [Variables and Connections](#variables-and-connections)
7. [Branching](#branching)
8. [Dynamic DAGs](#dynamic-dags)
9. [TaskFlow API](#taskflow-api)
10. [Templating](#templating)

---

## DAG Creation Patterns

### Classic Pattern

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

# Define default args
default_args = {
    'owner': 'datateam',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Create DAG instance
dag = DAG(
    dag_id='data_pipeline',
    default_args=default_args,
    schedule='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
)

# Define tasks
def extract():
    print("Extracting data...")

task1 = PythonOperator(
    task_id='extract',
    python_callable=extract,
    dag=dag,
)
```text

### Context Manager Pattern

```python
with DAG(
    dag_id='data_pipeline',
    default_args=default_args,
    schedule='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:

    task1 = PythonOperator(
        task_id='extract',
        python_callable=extract,
    )

    task2 = PythonOperator(
        task_id='transform',
        python_callable=transform,
    )

    task1 >> task2
```text

### Decorator Pattern (TaskFlow API)

```python
from airflow.decorators import dag, task
from datetime import datetime

@dag(
    dag_id='data_pipeline',
    schedule='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
)
def data_pipeline_taskflow():

    @task
    def extract():
        print("Extracting data...")
        return {"records": 100}

    @task
    def transform(data):
        records = data['records']
        print(f"Transforming {records} records")
        return records * 2

    @task
    def load(processed_records):
        print(f"Loading {processed_records} records")

    # Define flow
    data = extract()
    processed = transform(data)
    load(processed)

# Instantiate DAG
dag = data_pipeline_taskflow()
```text

### DAG Parameters

```python
dag = DAG(
    # === REQUIRED ===
    dag_id='my_dag',                    # Unique identifier
    start_date=datetime(2024, 1, 1),   # When DAG starts

    # === SCHEDULE ===
    schedule='@daily',                  # How often to run
    # schedule='0 0 * * *',            # Cron expression
    # schedule=timedelta(hours=2),     # Timedelta
    # schedule=None,                   # Manual only

    # === CATCH-UP ===
    catchup=False,                      # Run missed runs?

    # === DEFAULT ARGS ===
    default_args={
        'owner': 'datateam',
        'depends_on_past': False,       # Wait for previous run?
        'email': ['team@example.com'],
        'email_on_failure': True,
        'email_on_retry': False,
        'retries': 2,
        'retry_delay': timedelta(minutes=5),
        'execution_timeout': timedelta(hours=2),
    },

    # === CONCURRENCY ===
    max_active_runs=3,                  # Max concurrent runs
    concurrency=16,                     # Max tasks per DAG run

    # === DOCUMENTATION ===
    description='ETL pipeline for customer data',
    doc_md="""
    # Customer Data Pipeline

    ## Purpose
    Extract, transform, and load customer data daily.

    ## Dependencies
    - Source: PostgreSQL database
    - Destination: S3 bucket
    """,

    # === TAGS ===
    tags=['etl', 'customer', 'daily'],

    # === ADVANCED ===
    dagrun_timeout=timedelta(hours=4), # Max DAG run duration
    sla_miss_callback=notify_sla_miss,
    on_failure_callback=notify_failure,
    on_success_callback=notify_success,
    params={'env': 'prod'},             # User-defined params
)
```

---

## Task Dependencies

### Basic Dependencies

```python
# Method 1: Bitshift operators (recommended)
task1 >> task2  # task1 runs before task2
task2 << task1  # Same as above

# Method 2: set_downstream/set_upstream
task1.set_downstream(task2)
task2.set_upstream(task1)

# Method 3: set_upstream/downstream with list
task1.set_downstream([task2, task3, task4])
```text

### Linear Dependencies

```python
# Sequential chain
task1 >> task2 >> task3 >> task4

# Equivalent to:
task1.set_downstream(task2)
task2.set_downstream(task3)
task3.set_downstream(task4)
```text

### Fan-Out / Fan-In

```python
# Fan-out: One task triggers multiple
start >> [task1, task2, task3] >> end

# Equivalent to:
start >> task1 >> end
start >> task2 >> end
start >> task3 >> end
```text

### Complex Dependencies

```python
#     start
#    /  |  \
#   t1  t2  t3
#    \  |  /
#     join
#      |
#     end

start >> [task1, task2, task3] >> join >> end
```

### Cross-Dependencies

```python
#   t1 ----\
#    |     |
#   t2     t4
#    |     |
#   t3 ----/

task1 >> task2 >> task3
task1 >> task4
task3 >> task4
```text

### Trigger Rules

**Trigger Rule** determina cuándo un task ejecuta basado en upstream tasks.

```python
from airflow.utils.trigger_rule import TriggerRule

task = PythonOperator(
    task_id='my_task',
    python_callable=my_function,
    trigger_rule=TriggerRule.ALL_SUCCESS,  # Default
)
```text

**Available Rules:**

| Rule | Description | Use Case |
|------|-------------|----------|
| `ALL_SUCCESS` | All upstream tasks succeeded | Default |
| `ALL_FAILED` | All upstream tasks failed | Cleanup after failures |
| `ALL_DONE` | All upstream tasks finished (any state) | Always run regardless |
| `ONE_SUCCESS` | At least one upstream succeeded | OR logic |
| `ONE_FAILED` | At least one upstream failed | Alert on any failure |
| `NONE_FAILED` | No upstream tasks failed (success or skipped) | Continue unless failure |
| `NONE_SKIPPED` | No upstream tasks skipped | Require all data |
| `DUMMY` | Always run | Start/end markers |

**Example: Cleanup Task**

```python
# Run cleanup even if pipeline fails
cleanup = PythonOperator(
    task_id='cleanup',
    python_callable=cleanup_function,
    trigger_rule=TriggerRule.ALL_DONE,  # Runs regardless
)

[extract, transform, load] >> cleanup
```text

---

## Operators Deep Dive

### PythonOperator

Execute función Python.

```python
from airflow.operators.python import PythonOperator

def my_function(x, y):
    result = x + y
    print(f"Result: {result}")
    return result

task = PythonOperator(
    task_id='run_calculation',
    python_callable=my_function,
    op_args=[10, 20],          # Positional args
    op_kwargs={'y': 30},       # Keyword args
)
```

**With Context:**

```python
def my_function_with_context(**context):
    execution_date = context['execution_date']
    dag_run = context['dag_run']
    task_instance = context['ti']

    print(f"Execution date: {execution_date}")
    print(f"Run ID: {dag_run.run_id}")

    # Push value to XCom
    task_instance.xcom_push(key='result', value=42)

task = PythonOperator(
    task_id='with_context',
    python_callable=my_function_with_context,
    provide_context=True,  # Not needed in Airflow 2.0+
)
```text

**Context Variables:**

- `execution_date`: Logical date
- `dag`: DAG instance
- `dag_run`: DagRun instance
- `ti`: TaskInstance
- `task`: Task instance
- `run_id`: Unique run ID
- `conf`: DAG run configuration
- `params`: User-defined params
- `var`: Access to Variables
- `conn`: Access to Connections

### BashOperator

Execute comando bash.

```python
from airflow.operators.bash import BashOperator

task = BashOperator(
    task_id='run_script',
    bash_command='python /path/to/script.py',
)

# With environment variables
task = BashOperator(
    task_id='with_env',
    bash_command='echo "Hello $NAME"',
    env={'NAME': 'Airflow'},
)

# Multi-line script
task = BashOperator(
    task_id='multi_line',
    bash_command="""
        cd /tmp
        echo "Starting process..."
        python script.py
        echo "Done!"
    """,
)

# With templating
task = BashOperator(
    task_id='templated',
    bash_command='echo "Execution date: {{ ds }}"',
)
```text

### PythonVirtualenvOperator

Execute código en virtualenv aislado.

```python
from airflow.operators.python import PythonVirtualenvOperator

def my_function():
    import pandas as pd  # Will install in venv
    df = pd.DataFrame({'a': [1, 2, 3]})
    print(df)

task = PythonVirtualenvOperator(
    task_id='virtualenv_task',
    python_callable=my_function,
    requirements=['pandas==2.0.0', 'numpy==1.24.0'],
    system_site_packages=False,  # Isolate from system packages
)
```text

### EmailOperator

Envía email.

```python
from airflow.operators.email import EmailOperator

task = EmailOperator(
    task_id='send_email',
    to=['recipient@example.com'],
    subject='Pipeline Completed',
    html_content="""
        <h3>ETL Pipeline Successful</h3>
        <p>Processed {{ ti.xcom_pull(task_ids='count_records') }} records</p>
    """,
    files=['/tmp/report.pdf'],  # Attachments
)
```

### SimpleHttpOperator

HTTP request.

```python
from airflow.providers.http.operators.http import SimpleHttpOperator

task = SimpleHttpOperator(
    task_id='api_call',
    http_conn_id='my_api',  # Connection in Airflow UI
    endpoint='/api/v1/data',
    method='POST',
    data={'key': 'value'},
    headers={'Authorization': 'Bearer token'},
    response_check=lambda response: response.status_code == 200,
    log_response=True,
)
```text

### PostgresOperator

Execute SQL en PostgreSQL.

```python
from airflow.providers.postgres.operators.postgres import PostgresOperator

task = PostgresOperator(
    task_id='create_table',
    postgres_conn_id='postgres_default',
    sql="""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            created_at TIMESTAMP DEFAULT NOW()
        );
    """,
)

# From SQL file
task = PostgresOperator(
    task_id='run_sql_file',
    postgres_conn_id='postgres_default',
    sql='queries/transform.sql',
)

# With parameters
task = PostgresOperator(
    task_id='insert_data',
    postgres_conn_id='postgres_default',
    sql="""
        INSERT INTO users (name)
        VALUES (%(name)s);
    """,
    parameters={'name': 'John Doe'},
)
```text

### S3Operators

**S3CreateObjectOperator:**

```python
from airflow.providers.amazon.aws.operators.s3 import S3CreateObjectOperator

task = S3CreateObjectOperator(
    task_id='create_s3_object',
    s3_bucket='my-bucket',
    s3_key='data/output.json',
    data='{"key": "value"}',
    replace=True,
    aws_conn_id='aws_default',
)
```text

**S3ListOperator:**

```python
from airflow.providers.amazon.aws.operators.s3 import S3ListOperator

task = S3ListOperator(
    task_id='list_s3_files',
    bucket='my-bucket',
    prefix='data/',
    delimiter='/',
    aws_conn_id='aws_default',
)
```

### DockerOperator

Execute código en Docker container.

```python
from airflow.providers.docker.operators.docker import DockerOperator

task = DockerOperator(
    task_id='docker_task',
    image='python:3.11',
    command='python -c "print(\'Hello from Docker\')"',
    docker_url='unix://var/run/docker.sock',
    network_mode='bridge',
    auto_remove=True,  # Remove container after execution
    mount_tmp_dir=False,
)

# With volume mounts
task = DockerOperator(
    task_id='docker_with_volumes',
    image='python:3.11',
    command='python /scripts/process.py',
    mounts=[
        {'source': '/local/path', 'target': '/scripts', 'type': 'bind'},
    ],
)
```text

### KubernetesPodOperator

Execute task en Kubernetes Pod.

```python
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator

task = KubernetesPodOperator(
    task_id='k8s_task',
    name='airflow-k8s-task',
    namespace='airflow',
    image='python:3.11',
    cmds=['python'],
    arguments=['-c', 'print("Hello from K8s")'],
    get_logs=True,
    is_delete_operator_pod=True,
    resources={
        'request_memory': '512Mi',
        'request_cpu': '500m',
        'limit_memory': '2Gi',
        'limit_cpu': '2000m',
    },
)
```text

---

## Sensors

**Sensors** esperan por condición antes de continuar.

### FileSensor

Espera archivo.

```python
from airflow.sensors.filesystem import FileSensor

sensor = FileSensor(
    task_id='wait_for_file',
    filepath='/data/input.csv',
    poke_interval=30,  # Check every 30 seconds
    timeout=600,       # Fail after 10 minutes
    mode='poke',       # poke or reschedule
)
```text

**Modes:**

- **poke**: Holds worker slot while waiting
- **reschedule**: Releases slot, reschedules sensor

### S3KeySensor

Espera archivo en S3.

```python
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor

sensor = S3KeySensor(
    task_id='wait_for_s3_file',
    bucket_name='my-bucket',
    bucket_key='data/input.csv',
    aws_conn_id='aws_default',
    poke_interval=60,
    timeout=3600,
)

# With wildcard
sensor = S3KeySensor(
    task_id='wait_for_s3_pattern',
    bucket_name='my-bucket',
    bucket_key='data/*.csv',
    wildcard_match=True,
)
```

### HttpSensor

Espera respuesta HTTP exitosa.

```python
from airflow.providers.http.sensors.http import HttpSensor

sensor = HttpSensor(
    task_id='wait_for_api',
    http_conn_id='my_api',
    endpoint='/api/v1/status',
    request_params={'check': 'ready'},
    response_check=lambda response: response.json()['status'] == 'ready',
    poke_interval=30,
    timeout=600,
)
```text

### SqlSensor

Espera condición SQL.

```python
from airflow.providers.common.sql.sensors.sql import SqlSensor

sensor = SqlSensor(
    task_id='wait_for_data',
    conn_id='postgres_default',
    sql="SELECT COUNT(*) FROM orders WHERE date = '{{ ds }}'",
    success=lambda result: result[0][0] > 0,  # True if records exist
    poke_interval=60,
    timeout=3600,
)
```text

### ExternalTaskSensor

Espera task en otro DAG.

```python
from airflow.sensors.external_task import ExternalTaskSensor

sensor = ExternalTaskSensor(
    task_id='wait_for_upstream_dag',
    external_dag_id='upstream_dag',
    external_task_id='final_task',
    execution_delta=timedelta(hours=1),  # Offset if schedules differ
    poke_interval=60,
    timeout=3600,
)
```text

### TimeDeltaSensor

Espera tiempo específico.

```python
from airflow.sensors.time_delta import TimeDeltaSensor

sensor = TimeDeltaSensor(
    task_id='wait_5_minutes',
    delta=timedelta(minutes=5),
)
```

### Custom Sensor

```python
from airflow.sensors.base import BaseSensorOperator

class MyCustomSensor(BaseSensorOperator):
    def __init__(self, threshold, **kwargs):
        super().__init__(**kwargs)
        self.threshold = threshold

    def poke(self, context):
        # Return True if condition met, False otherwise
        value = self.check_condition()
        return value > self.threshold

    def check_condition(self):
        # Custom logic
        return 42

sensor = MyCustomSensor(
    task_id='custom_sensor',
    threshold=50,
    poke_interval=30,
    timeout=600,
)
```text

---

## XComs

**XCom** (cross-communication) permite pasar datos entre tasks.

### Push & Pull

```python
# Task 1: Push value
def push_function(**context):
    ti = context['ti']
    ti.xcom_push(key='my_key', value={'data': 100})

task1 = PythonOperator(
    task_id='push_task',
    python_callable=push_function,
)

# Task 2: Pull value
def pull_function(**context):
    ti = context['ti']
    value = ti.xcom_pull(key='my_key', task_ids='push_task')
    print(f"Received: {value}")  # {'data': 100}

task2 = PythonOperator(
    task_id='pull_task',
    python_callable=pull_function,
)

task1 >> task2
```text

### Return Value (Automatic Push)

```python
def extract():
    data = [1, 2, 3, 4, 5]
    return data  # Automatically pushed to XCom

def transform(**context):
    ti = context['ti']
    data = ti.xcom_pull(task_ids='extract')  # Pull returned value
    transformed = [x * 2 for x in data]
    return transformed

extract_task = PythonOperator(task_id='extract', python_callable=extract)
transform_task = PythonOperator(task_id='transform', python_callable=transform)

extract_task >> transform_task
```text

### Multiple Values

```python
def push_multiple(**context):
    ti = context['ti']
    ti.xcom_push(key='count', value=100)
    ti.xcom_push(key='status', value='success')
    ti.xcom_push(key='data', value=[1, 2, 3])

def pull_multiple(**context):
    ti = context['ti']
    count = ti.xcom_pull(key='count', task_ids='push_task')
    status = ti.xcom_pull(key='status', task_ids='push_task')
    data = ti.xcom_pull(key='data', task_ids='push_task')

    print(f"Count: {count}, Status: {status}, Data: {data}")
```

### Pull from Multiple Tasks

```python
def aggregate(**context):
    ti = context['ti']

    # Pull from multiple tasks
    results = ti.xcom_pull(task_ids=['task1', 'task2', 'task3'])
    # Returns: [result1, result2, result3]

    total = sum(results)
    print(f"Total: {total}")
```text

### XCom Limitations

⚠️ **Size**: XComs stored in metadata DB, keep small (< 1MB)
⚠️ **Serialization**: Must be JSON-serializable
⚠️ **Performance**: Large XComs slow down DAG

**Alternative for Large Data:**

```python
# Don't pass large data in XCom
def extract():
    data = get_large_dataset()  # 100MB
    return data  # ❌ Bad

# Instead, pass reference
def extract():
    data = get_large_dataset()
    path = '/tmp/data.parquet'
    data.to_parquet(path)
    return path  # ✅ Good

def transform(**context):
    ti = context['ti']
    path = ti.xcom_pull(task_ids='extract')
    data = pd.read_parquet(path)
    # Process data...
```text

---

## Variables and Connections

### Variables

**Variables** son key-value store para configuration.

**Set via UI:**

- Admin → Variables → Add

**Set via CLI:**

```bash
airflow variables set my_variable my_value
airflow variables get my_variable
airflow variables delete my_variable
```text

**In DAG:**

```python
from airflow.models import Variable

# Get variable
env = Variable.get('environment')  # 'production'
api_key = Variable.get('api_key')

# With default
timeout = Variable.get('timeout', default_var=300)

# JSON variable
config = Variable.get('config', deserialize_json=True)
# Returns: {'host': 'localhost', 'port': 5432}

# In operator
task = PythonOperator(
    task_id='my_task',
    python_callable=my_function,
    op_kwargs={'env': Variable.get('environment')},
)
```

**Environment Variables:**

```python
import os

# Priority: Env var > Airflow variable
api_key = os.getenv('API_KEY') or Variable.get('api_key')
```text

### Connections

**Connections** almacenan credenciales para sistemas externos.

**Set via UI:**

- Admin → Connections → Add

Fields:

- **Conn Id**: Unique identifier
- **Conn Type**: postgres, mysql, http, s3, etc.
- **Host**: Server address
- **Schema**: Database name
- **Login**: Username
- **Password**: Password
- **Port**: Port number
- **Extra**: JSON config

**Example: PostgreSQL Connection**

UI fields:

```text
Conn Id: postgres_prod
Conn Type: Postgres
Host: db.example.com
Schema: analytics
Login: airflow_user
Password: ************
Port: 5432
Extra: {"sslmode": "require"}
```text

**Use in Operator:**

```python
task = PostgresOperator(
    task_id='query_db',
    postgres_conn_id='postgres_prod',  # References connection
    sql='SELECT * FROM users',
)
```

**Programmatic Access:**

```python
from airflow.hooks.base import BaseHook

conn = BaseHook.get_connection('postgres_prod')
print(conn.host)      # db.example.com
print(conn.schema)    # analytics
print(conn.login)     # airflow_user
print(conn.password)  # ************
```text

---

## Branching

**Branching** permite decisiones condicionales en DAG.

### BranchPythonOperator

```python
from airflow.operators.python import BranchPythonOperator

def choose_branch(**context):
    execution_date = context['execution_date']

    if execution_date.weekday() < 5:  # Weekday
        return 'weekday_task'
    else:  # Weekend
        return 'weekend_task'

branch = BranchPythonOperator(
    task_id='branch',
    python_callable=choose_branch,
)

weekday_task = PythonOperator(task_id='weekday_task', python_callable=process_weekday)
weekend_task = PythonOperator(task_id='weekend_task', python_callable=process_weekend)
join = PythonOperator(task_id='join', python_callable=final_task, trigger_rule='none_failed')

branch >> [weekday_task, weekend_task] >> join
```text

### Multiple Branches

```python
def choose_processing_type(**context):
    ti = context['ti']
    data_size = ti.xcom_pull(key='data_size', task_ids='check_data')

    if data_size < 1000:
        return 'small_processing'
    elif data_size < 100000:
        return 'medium_processing'
    else:
        return 'large_processing'

branch = BranchPythonOperator(
    task_id='choose_processing',
    python_callable=choose_processing_type,
)

small = PythonOperator(task_id='small_processing', ...)
medium = PythonOperator(task_id='medium_processing', ...)
large = PythonOperator(task_id='large_processing', ...)

branch >> [small, medium, large]
```text

### Return Multiple Tasks

```python
def choose_branches(**context):
    # Can return list of task_ids
    return ['task1', 'task3']  # Skips task2

branch = BranchPythonOperator(
    task_id='branch',
    python_callable=choose_branches,
)

branch >> [task1, task2, task3]
```

### ShortCircuitOperator

Stops pipeline if condition False.

```python
from airflow.operators.python import ShortCircuitOperator

def check_condition(**context):
    # Return True to continue, False to stop
    data_available = check_data_exists()
    return data_available

short_circuit = ShortCircuitOperator(
    task_id='check_data',
    python_callable=check_condition,
)

# If check_condition returns False, downstream tasks are skipped
short_circuit >> task1 >> task2 >> task3
```text

---

## Dynamic DAGs

### Generate Tasks Dynamically

```python
from airflow import DAG
from airflow.operators.python import PythonOperator

dag = DAG('dynamic_tasks', ...)

# Create 10 tasks dynamically
for i in range(10):
    task = PythonOperator(
        task_id=f'task_{i}',
        python_callable=process_item,
        op_kwargs={'item_id': i},
        dag=dag,
    )
```text

### Generate from Configuration

```python
# config.yaml
datasets:
  - name: users
    table: users
    columns: [id, name, email]
  - name: orders
    table: orders
    columns: [id, user_id, amount]

# DAG
import yaml

with open('/path/to/config.yaml') as f:
    config = yaml.safe_load(f)

dag = DAG('dynamic_from_config', ...)

for dataset in config['datasets']:
    task = PythonOperator(
        task_id=f"process_{dataset['name']}",
        python_callable=process_dataset,
        op_kwargs={'dataset': dataset},
        dag=dag,
    )
```text

### Generate DAGs Dynamically

```python
# Generate multiple DAGs from config

DATASETS = ['users', 'orders', 'products']

for dataset in DATASETS:
    dag_id = f'etl_{dataset}'

    dag = DAG(
        dag_id=dag_id,
        schedule='@daily',
        start_date=datetime(2024, 1, 1),
    )

    extract = PythonOperator(
        task_id='extract',
        python_callable=extract_data,
        op_kwargs={'dataset': dataset},
        dag=dag,
    )

    transform = PythonOperator(
        task_id='transform',
        python_callable=transform_data,
        dag=dag,
    )

    load = PythonOperator(
        task_id='load',
        python_callable=load_data,
        dag=dag,
    )

    extract >> transform >> load

    # Register DAG
    globals()[dag_id] = dag
```

---

## TaskFlow API

**TaskFlow API** (Airflow 2.0+) simplifica DAG creation con decorators.

### Basic Example

```python
from airflow.decorators import dag, task
from datetime import datetime

@dag(
    dag_id='taskflow_example',
    schedule='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
)
def etl_pipeline():

    @task
    def extract():
        data = [1, 2, 3, 4, 5]
        return data

    @task
    def transform(data):
        transformed = [x * 2 for x in data]
        return transformed

    @task
    def load(data):
        print(f"Loading {len(data)} records")
        for record in data:
            print(record)

    # Define flow
    data = extract()
    transformed_data = transform(data)
    load(transformed_data)

# Instantiate DAG
dag = etl_pipeline()
```text

### Multiple Inputs/Outputs

```python
@dag(...)
def multi_input_output():

    @task
    def extract_users():
        return [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]

    @task
    def extract_orders():
        return [{'user_id': 1, 'amount': 100}, {'user_id': 2, 'amount': 200}]

    @task
    def join_data(users, orders):
        # Join users and orders
        result = []
        for user in users:
            user_orders = [o for o in orders if o['user_id'] == user['id']]
            result.append({'user': user, 'orders': user_orders})
        return result

    @task
    def calculate_total(data):
        for item in data:
            total = sum(order['amount'] for order in item['orders'])
            print(f"{item['user']['name']}: ${total}")

    users = extract_users()
    orders = extract_orders()
    joined = join_data(users, orders)
    calculate_total(joined)

dag = multi_input_output()
```text

### TaskFlow with Traditional Operators

```python
from airflow.operators.bash import BashOperator

@dag(...)
def mixed_operators():

    @task
    def extract():
        return {'records': 100}

    # Traditional operator
    transform_bash = BashOperator(
        task_id='transform',
        bash_command='echo "Transforming..."',
    )

    @task
    def load(data):
        print(f"Loading {data['records']} records")

    data = extract()
    data >> transform_bash  # TaskFlow output to traditional
    transform_bash >> load(data)  # Traditional to TaskFlow

dag = mixed_operators()
```text

### TaskFlow Benefits

✅ **Automatic XCom**: Return values automatically pushed/pulled
✅ **Type Hints**: Better IDE support, documentation
✅ **Less Boilerplate**: No manual context handling
✅ **Cleaner Code**: More Pythonic syntax

---

## Templating

**Jinja Templating** permite valores dinámicos en operators.

### Template Variables

```python
# Use {{ }} for Jinja templates

task = BashOperator(
    task_id='templated_task',
    bash_command='''
        echo "Execution date: {{ ds }}"
        echo "DAG ID: {{ dag.dag_id }}"
        echo "Task ID: {{ task.task_id }}"
        echo "Run ID: {{ run_id }}"
    ''',
)
```

### Common Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{ ds }}` | Execution date (YYYY-MM-DD) | 2024-01-15 |
| `{{ ds_nodash }}` | Execution date (YYYYMMDD) | 20240115 |
| `{{ ts }}` | Timestamp (ISO 8601) | 2024-01-15T00:00:00+00:00 |
| `{{ dag }}` | DAG object | |
| `{{ task }}` | Task object | |
| `{{ ti }}` | TaskInstance object | |
| `{{ run_id }}` | DagRun ID | scheduled__2024-01-15T00:00:00+00:00 |
| `{{ execution_date }}` | Execution datetime | 2024-01-15 00:00:00 |
| `{{ prev_execution_date }}` | Previous execution | 2024-01-14 00:00:00 |
| `{{ next_execution_date }}` | Next execution | 2024-01-16 00:00:00 |

### Templated Fields

**Not all operator fields are templated!** Check operator source.

```python
# PostgresOperator: sql is templated
task = PostgresOperator(
    task_id='query',
    sql="""
        SELECT * FROM orders
        WHERE date = '{{ ds }}'
    """,
)

# BashOperator: bash_command, env are templated
task = BashOperator(
    task_id='run_script',
    bash_command='./process.sh {{ ds }}',
    env={
        'DATE': '{{ ds }}',
        'RUN_ID': '{{ run_id }}',
    },
)
```text

### Macros

```python
# Date arithmetic
task = BashOperator(
    task_id='with_macros',
    bash_command='''
        echo "Yesterday: {{ macros.ds_add(ds, -1) }}"
        echo "Next week: {{ macros.ds_add(ds, 7) }}"
        echo "Format: {{ macros.datetime.strptime(ds, '%Y-%m-%d').strftime('%d/%m/%Y') }}"
    ''',
)
```text

### User-Defined Macros

```python
def custom_macro(value):
    return value.upper()

dag = DAG(
    'with_macros',
    user_defined_macros={
        'my_macro': custom_macro,
    },
)

task = BashOperator(
    task_id='use_macro',
    bash_command='echo "{{ my_macro("hello") }}"',  # HELLO
    dag=dag,
)
```text

---

## Summary

**Key Takeaways:**

✅ **DAG Creation**: Classic, context manager, TaskFlow API
✅ **Dependencies**: `>>`, `<<`, trigger rules
✅ **Operators**: Python, Bash, Database, Cloud, Docker, K8s
✅ **Sensors**: Wait for conditions
✅ **XComs**: Pass small data between tasks
✅ **Variables/Connections**: Configuration and credentials
✅ **Branching**: Conditional logic
✅ **Dynamic DAGs**: Generate tasks/DAGs programmatically
✅ **TaskFlow API**: Modern, Pythonic syntax
✅ **Templating**: Dynamic values with Jinja

**Next**: [03-production-patterns.md](03-production-patterns.md)

---

**Document**: 02-dags-and-operators.md
**Words**: ~5,500
**Level**: Intermediate-Advanced
**Prerequisites**: 01-airflow-fundamentals.md
