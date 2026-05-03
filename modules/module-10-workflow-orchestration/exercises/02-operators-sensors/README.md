# Exercise 02: Operators & Sensors

## 🎯 Objective

Master different types of Airflow operators (Python, Bash, HTTP, Database, S3) and learn to use sensors for waiting on conditions.

## 📚 Prerequisites

- Completed [Exercise 01](../01-first-dag/README.md)
- Airflow instance with connections configured
- PostgreSQL connection (`postgres_default`)
- AWS connection (`aws_default`) or LocalStack
- HTTP connection for API testing

## 📋 Tasks

### Task 1: Comprehensive Operator Usage

Create a DAG using multiple operator types:

1. **BashOperator**: Create directory and files
2. **PythonOperator**: Process data
3. **SimpleHttpOperator**: Fetch data from API
4. **PostgresOperator**: Create table and insert data
5. **EmailOperator**: Send report

**Requirements:**
- Use 5 different operator types
- Proper error handling
- Log all operations
- Template usage in operators

**API Endpoint** (for testing): `https://jsonplaceholder.typicode.com/users`

---

### Task 2: File Sensor Pipeline

Create a DAG that waits for a file before processing:

1. **FileSensor**: Wait for `/tmp/input_data.csv`
2. **PythonOperator**: Read and process file
3. **BashOperator**: Move file to `/tmp/processed/`
4. **PythonOperator**: Generate report

**Requirements:**
- Sensor timeout: 10 minutes
- Poke interval: 30 seconds
- Sensor mode: `poke`
- Handle file not found scenario

**Test File Creation:**
```bash
echo "id,name,value\n1,Alice,100\n2,Bob,200" > /tmp/input_data.csv
```

---

### Task 3: S3 Operations

Create a DAG for S3 operations (use LocalStack for local testing):

1. **S3CreateObjectOperator**: Upload data to S3
2. **S3KeySensor**: Wait for file in another bucket
3. **PythonOperator**: Download and process S3 file
4. **S3ListOperator**: List all files in bucket

**Requirements:**
- S3 bucket: `airflow-exercise-bucket`
- Key prefix: `data/`
- Use `aws_conn_id`
- Handle S3 errors

**LocalStack Setup:**
```bash
# Start LocalStack
docker run -d -p 4566:4566 localstack/localstack

# Create bucket
aws --endpoint-url=http://localhost:4566 s3 mb s3://airflow-exercise-bucket
```

---

### Task 4: Database Pipeline

Create ETL pipeline with PostgreSQL:

1. **PostgresOperator**: Create staging table
2. **PythonOperator**: Extract data from API
3. **PostgresOperator**: Insert data into staging
4. **PostgresOperator**: Transform (aggregate, clean)
5. **PostgresOperator**: Load into final table
6. **SqlSensor**: Wait for data in final table

**Requirements:**
- Create 3 tables: staging, intermediate, final
- Use SQL templating ({{ ds }})
- Transaction handling
- Check row counts

**Schema:**
```sql
CREATE TABLE user_staging (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_final (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100),
    domain VARCHAR(50),
    date DATE
);
```

---

### Task 5: HTTP API Sensor

Create a DAG that waits for API readiness:

1. **HttpSensor**: Wait for API `/health` endpoint to return 200
2. **SimpleHttpOperator**: POST request to create resource
3. **SimpleHttpOperator**: GET request to fetch resource
4. **PythonOperator**: Process API response
5. **HttpSensor**: Wait for async job completion

**Requirements:**
- HTTP connection with retry logic
- Response validation
- Parse JSON responses
- Handle API errors (4xx, 5xx)

**Mock API** (for testing): Use `https://jsonplaceholder.typicode.com`

---

### Task 6: Multi-Sensor Coordination

Create a DAG combining multiple sensors:

1. **TimeDeltaSensor**: Wait 2 minutes
2. **FileSensor**: Wait for file A
3. **S3KeySensor**: Wait for file B
4. **ExternalTaskSensor**: Wait for another DAG to complete
5. **PythonOperator**: Process when all conditions met

**Requirements:**
- All sensors in parallel
- Join point after all sensors complete
- Use trigger_rule: `all_success`
- Sensor timeout handling

**Dependency Graph:**
```
  start
    |
  wait_2min
    |
  ┌──────┬───────┬──────────┐
  │      │       │          │
 file   s3    external    custom
sensor sensor  sensor    sensor
  │      │       │          │
  └──────┴───────┴──────────┘
          |
      process_all
```

---

## 🚀 Implementation Guides

### Task 1: Multi-Operator DAG

```python
# dags/ex02_task1_operators.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.email import EmailOperator
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'student',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='ex02_multi_operators',
    default_args=default_args,
    description='Using multiple operator types',
    schedule='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['exercise', 'operators', 'ex02'],
) as dag:

    # 1. BashOperator: Setup
    setup = BashOperator(
        task_id='setup',
        bash_command='''
            mkdir -p /tmp/ex02
            echo "Setup completed on {{ ds }}" > /tmp/ex02/setup.txt
            date
        ''',
    )

    # 2. PythonOperator: Process
    def process_data(**context):
        import pandas as pd

        data = {'id': [1, 2, 3], 'value': [10, 20, 30]}
        df = pd.DataFrame(data)

        logger.info(f"Processing {len(df)} records")
        summary = df['value'].sum()

        # Push to XCom
        context['ti'].xcom_push(key='summary', value=summary)
        return summary

    process = PythonOperator(
        task_id='process',
        python_callable=process_data,
    )

    # 3. HttpOperator: Fetch API data
    fetch_api = SimpleHttpOperator(
        task_id='fetch_api',
        http_conn_id='http_default',
        endpoint='/users/1',
        method='GET',
        response_filter=lambda response: json.loads(response.text),
        log_response=True,
    )

    # 4. PostgresOperator: Database operations
    create_table = PostgresOperator(
        task_id='create_table',
        postgres_conn_id='postgres_default',
        sql='''
            CREATE TABLE IF NOT EXISTS ex02_data (
                id SERIAL PRIMARY KEY,
                date DATE,
                value INTEGER,
                created_at TIMESTAMP DEFAULT NOW()
            );
        ''',
    )

    insert_data = PostgresOperator(
        task_id='insert_data',
        postgres_conn_id='postgres_default',
        sql='''
            INSERT INTO ex02_data (date, value)
            VALUES ('{{ ds }}', 42);
        ''',
    )

    # 5. EmailOperator: Notify (configure SMTP in airflow.cfg)
    # Commented out if SMTP not configured
    # send_email = EmailOperator(
    #     task_id='send_email',
    #     to=['student@example.com'],
    #     subject='DAG ex02 Completed',
    #     html_content='Pipeline completed successfully on {{ ds }}',
    # )

    # Dependencies
    setup >> [process, fetch_api]
    fetch_api >> create_table >> insert_data
    # [process, insert_data] >> send_email
```

---

### Task 2: File Sensor

```python
# dags/ex02_task2_file_sensor.py
from airflow import DAG
from airflow.sensors.filesystem import FileSensor
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

with DAG(
    dag_id='ex02_file_sensor',
    description='Wait for file and process',
    schedule='@hourly',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['exercise', 'sensor', 'ex02'],
) as dag:

    # Wait for file
    wait_for_file = FileSensor(
        task_id='wait_for_file',
        filepath='/tmp/input_data.csv',
        poke_interval=30,  # Check every 30 seconds
        timeout=600,       # 10 minutes timeout
        mode='poke',       # poke vs reschedule
    )

    # Process file
    def process_file():
        import pandas as pd

        try:
            df = pd.read_csv('/tmp/input_data.csv')
            logger.info(f"Read {len(df)} rows")
            logger.info(f"Columns: {df.columns.tolist()}")
            logger.info(f"Summary:\n{df.describe()}")

            # Save processed
            df['processed'] = True
            df.to_csv('/tmp/output_data.csv', index=False)

            return len(df)
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            raise

    process = PythonOperator(
        task_id='process',
        python_callable=process_file,
    )

    # Move to processed folder
    move_file = BashOperator(
        task_id='move_file',
        bash_command='''
            mkdir -p /tmp/processed
            mv /tmp/input_data.csv /tmp/processed/input_data_{{ ts_nodash }}.csv
            echo "File moved to processed/"
        ''',
    )

    # Generate report
    def generate_report(**context):
        ti = context['ti']
        row_count = ti.xcom_pull(task_ids='process')

        report = f"""
        Processing Report
        =================
        Date: {context['ds']}
        Rows Processed: {row_count}
        Status: Success
        """

        logger.info(report)

        with open('/tmp/report.txt', 'w') as f:
            f.write(report)

    report = PythonOperator(
        task_id='report',
        python_callable=generate_report,
    )

    # Pipeline
    wait_for_file >> process >> move_file >> report
```

---

### Task 3: S3 Operations (with LocalStack)

```python
# dags/ex02_task3_s3.py
from airflow import DAG
from airflow.providers.amazon.aws.operators.s3 import S3CreateObjectOperator
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import json

with DAG(
    dag_id='ex02_s3_operations',
    description='S3 upload, sensor, and processing',
    schedule='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['exercise', 's3', 'ex02'],
) as dag:

    # Upload data to S3
    upload_to_s3 = S3CreateObjectOperator(
        task_id='upload_to_s3',
        s3_bucket='airflow-exercise-bucket',
        s3_key='data/input_{{ ds_nodash }}.json',
        data=json.dumps({'date': '{{ ds }}', 'value': 42}),
        replace=True,
        aws_conn_id='aws_default',
    )

    # Wait for another file
    wait_for_s3_file = S3KeySensor(
        task_id='wait_for_s3_file',
        bucket_name='airflow-exercise-bucket',
        bucket_key='data/input_{{ ds_nodash }}.json',
        aws_conn_id='aws_default',
        poke_interval=30,
        timeout=300,
    )

    # Process S3 file
    def process_s3_file(**context):
        from airflow.providers.amazon.aws.hooks.s3 import S3Hook

        s3_hook = S3Hook(aws_conn_id='aws_default')

        # Download file
        key = f"data/input_{context['ds_nodash']}.json"
        obj = s3_hook.read_key(
            key=key,
            bucket_name='airflow-exercise-bucket'
        )

        data = json.loads(obj)
        print(f"Downloaded data: {data}")

        # Process
        data['processed'] = True
        data['processed_at'] = str(datetime.now())

        # Upload processed
        s3_hook.load_string(
            string_data=json.dumps(data),
            key=f"data/processed_{context['ds_nodash']}.json",
            bucket_name='airflow-exercise-bucket',
            replace=True
        )

        return data

    process = PythonOperator(
        task_id='process_s3_file',
        python_callable=process_s3_file,
    )

    # Pipeline
    upload_to_s3 >> wait_for_s3_file >> process
```

---

## ✅ Testing & Validation

### Test File Sensor

```bash
# Terminal 1: Trigger DAG
airflow dags trigger ex02_file_sensor

# Terminal 2: Create file after 1 minute
sleep 60
echo "id,name,value
1,Alice,100
2,Bob,200
3,Charlie,300" > /tmp/input_data.csv

# Check DAG continues and succeeds
```

### Test Database Operations

```bash
# Connect to PostgreSQL
psql -U airflow -d airflow

# Check tables created
\dt

# Check data inserted
SELECT * FROM ex02_data;
```

### Test S3 with LocalStack

```bash
# List S3 buckets
aws --endpoint-url=http://localhost:4566 s3 ls

# List objects in bucket
aws --endpoint-url=http://localhost:4566 s3 ls s3://airflow-exercise-bucket/data/

# Download file
aws --endpoint-url=http://localhost:4566 s3 cp s3://airflow-exercise-bucket/data/input_20240101.json .
```

---

## 🎓 Learning Objectives

After completing this exercise, you should understand:

✅ Different operator types and when to use them
✅ How sensors wait for conditions
✅ FileSensor for file-based workflows
✅ S3 operations (upload, sensor, download)
✅ Database operations with PostgresOperator
✅ HTTP API interactions
✅ Sensor timeout and retry configuration
✅ Multi-sensor coordination

---

## 📚 Additional Resources

- [Airflow Operators](https://airflow.apache.org/docs/apache-airflow/stable/operators.html)
- [Sensors](https://airflow.apache.org/docs/apache-airflow/stable/concepts/sensors.html)
- [HTTP Provider](https://airflow.apache.org/docs/apache-airflow-providers-http/stable/index.html)
- [AWS Provider](https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/index.html)

---

## 🆘 Troubleshooting

**Sensor Timeout:**
- Increase `timeout` parameter
- Adjust `poke_interval`
- Check condition is actually met
- Use `mode='reschedule'` for long waits

**S3 Connection Failed:**
- Verify `aws_conn_id` configured
- Check LocalStack running: `docker ps`
- Test AWS CLI: `aws --endpoint-url=http://localhost:4566 s3 ls`

**Database Connection:**
- Check `postgres_conn_id` in Airflow UI
- Test connection: `airflow connections test postgres_default`
- Verify PostgreSQL running

---

**Next Exercise**: [03-task-dependencies](../03-task-dependencies/README.md)
