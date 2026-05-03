# Exercise 01: First DAG

## 🎯 Objective

Create your first Apache Airflow DAG with basic tasks, understand scheduling, and learn to interact with the Airflow UI.

## 📚 Prerequisites

- Apache Airflow instance running
- Access to Airflow UI (http://localhost:8080)
- Basic Python knowledge
- Understanding of [01-airflow-fundamentals.md](../../theory/01-airflow-fundamentals.md)

## 📋 Tasks

### Task 1: Simple Hello World DAG

Create a DAG that:
- Prints "Hello from Airflow!"
- Has a unique DAG ID
- Runs daily
- Has proper default arguments

**Requirements:**
- Use `PythonOperator`
- Set start date to yesterday
- Disable catchup
- Add owner and tags

**Expected Output:**
- DAG visible in UI
- Task executes successfully
- Log shows "Hello from Airflow!"

---

### Task 2: Multi-Task Pipeline

Create a DAG with 3 sequential tasks:
1. **extract**: Print "Extracting data..." and return a list
2. **transform**: Receive list, transform it (multiply by 2), return result
3. **load**: Receive transformed data and "load" it (print)

**Requirements:**
- Use **PythonOperator** for all tasks
- Use **XCom** to pass data between tasks
- Set proper task dependencies
- Add logging statements

**Expected Output:**
```
[INFO] Extracting data...
[INFO] Extracted: [1, 2, 3, 4, 5]
[INFO] Transforming data...
[INFO] Transformed: [2, 4, 6, 8, 10]
[INFO] Loading data...
[INFO] Loaded 5 records
```

---

### Task 3: Mixed Operators

Create a DAG combining Python and Bash operators:
1. **start**: BashOperator - Print current date
2. **python_task**: PythonOperator - Calculate sum of numbers
3. **check_file**: BashOperator - Check if /tmp exists
4. **end**: PythonOperator - Print completion message

**Requirements:**
- Mix `PythonOperator` and `BashOperator`
- Use templating in `BashOperator` ({{ ds }}, {{ run_id }})
- Set dependencies: start → [python_task, check_file] → end

**Expected Flow:**
```
       start
      /     \
python_task  check_file
      \     /
       end
```

---

### Task 4: Scheduling & Context

Create a DAG that:
- Runs **every 6 hours**
- Uses context variables (execution_date, dag_run, etc.)
- Logs detailed execution information
- Uses retry logic (2 retries, 5 min delay)

**Requirements:**
- Schedule: `schedule=timedelta(hours=6)`
- Access context via `**context`
- Print execution_date, run_id, task_id, dag_id
- Configure retries and retry_delay

**Expected Output:**
```
[INFO] Execution Date: 2024-01-15 00:00:00
[INFO] Run ID: scheduled__2024-01-15T00:00:00+00:00
[INFO] Task ID: log_context
[INFO] DAG ID: context_dag
[INFO] Try Number: 1
```

---

### Task 5: DAG with Email Notification

Create a DAG that:
- Sends email on task failure
- Uses `EmailOperator` for success notification
- Has proper error handling

**Requirements:**
- Configure email in default_args
- Add `EmailOperator` task at end
- Test failure scenario (divide by zero)
- Use `on_failure_callback`

⚠️ **Note:** Email requires SMTP configuration in `airflow.cfg`

---

### Task 6: Dynamic Task Generation

Create a DAG that generates 5 tasks dynamically:
- Each task processes a different dataset
- Use for-loop to create tasks
- Set dependencies: start → [task1, task2, task3, task4, task5] → end

**Requirements:**
- Generate tasks in loop
- Each task has unique task_id
- Parallel execution (all tasks independent)
- Use `op_kwargs` to pass different parameters

**Expected Structure:**
```
         start
        / | | | \
       t1 t2 t3 t4 t5
        \ | | | /
          end
```

---

## 🚀 Getting Started

### 1. Create DAG File

```bash
cd /opt/airflow/dags
touch ex01_hello_world.dag
```

### 2. Write Your First DAG

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'student',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    dag_id='ex01_hello_world',
    default_args=default_args,
    description='My first Airflow DAG',
    schedule=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['exercise', 'beginner', 'ex01'],
)

def print_hello():
    print("Hello from Airflow!")
    return "Success"

task = PythonOperator(
    task_id='hello_task',
    python_callable=print_hello,
    dag=dag,
)
```

### 3. Test DAG Locally

```bash
# Test that DAG can be parsed
python dags/ex01_hello_world.py

# List DAGs (should see ex01_hello_world)
airflow dags list

# Test specific task
airflow tasks test ex01_hello_world hello_task 2024-01-01
```

### 4. Trigger DAG in UI

1. Open http://localhost:8080
2. Find "ex01_hello_world" DAG
3. Toggle to "On" (unpause)
4. Click "Trigger DAG" button
5. View "Graph" to see task status
6. Click task → "Log" to see output

---

## 📝 Solution Templates

### Task 1: Hello World (Solution)

<details>
<summary>Click to reveal solution</summary>

```python
# dags/ex01_task1_hello.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'student',
    'depends_on_past': False,
    'email': ['student@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='ex01_hello_world',
    default_args=default_args,
    description='My first Airflow DAG',
    schedule=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['exercise', 'beginner', 'ex01'],
) as dag:

    def print_hello():
        print("Hello from Airflow!")
        return "Success"

    hello_task = PythonOperator(
        task_id='hello_task',
        python_callable=print_hello,
    )
```

</details>

---

### Task 2: Multi-Task Pipeline (Solution)

<details>
<summary>Click to reveal solution</summary>

```python
# dags/ex01_task2_pipeline.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'student',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    dag_id='ex01_etl_pipeline',
    default_args=default_args,
    description='Simple ETL pipeline with XCom',
    schedule='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['exercise', 'etl', 'ex01'],
)

def extract(**context):
    logger.info("Extracting data...")
    data = [1, 2, 3, 4, 5]
    logger.info(f"Extracted: {data}")
    return data

def transform(**context):
    ti = context['ti']
    data = ti.xcom_pull(task_ids='extract')
    logger.info("Transforming data...")
    transformed = [x * 2 for x in data]
    logger.info(f"Transformed: {transformed}")
    return transformed

def load(**context):
    ti = context['ti']
    data = ti.xcom_pull(task_ids='transform')
    logger.info("Loading data...")
    logger.info(f"Loaded {len(data)} records: {data}")
    return f"Loaded {len(data)} records"

extract_task = PythonOperator(
    task_id='extract',
    python_callable=extract,
    dag=dag,
)

transform_task = PythonOperator(
    task_id='transform',
    python_callable=transform,
    dag=dag,
)

load_task = PythonOperator(
    task_id='load',
    python_callable=load,
    dag=dag,
)

# Set dependencies
extract_task >> transform_task >> load_task
```

</details>

---

### Task 3: Mixed Operators (Solution)

<details>
<summary>Click to reveal solution</summary>

```python
# dags/ex01_task3_mixed.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    dag_id='ex01_mixed_operators',
    description='Mix of Python and Bash operators',
    schedule='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['exercise', 'mixed', 'ex01'],
) as dag:

    start = BashOperator(
        task_id='start',
        bash_command='echo "Starting pipeline on {{ ds }}"',
    )

    def calculate_sum():
        numbers = list(range(1, 11))
        total = sum(numbers)
        print(f"Sum of {numbers} = {total}")
        return total

    python_task = PythonOperator(
        task_id='python_task',
        python_callable=calculate_sum,
    )

    check_file = BashOperator(
        task_id='check_file',
        bash_command='''
            echo "Run ID: {{ run_id }}"
            if [ -d /tmp ]; then
                echo "/tmp exists"
            else
                echo "/tmp does not exist"
            fi
        ''',
    )

    def completion_message(**context):
        run_id = context['run_id']
        execution_date = context['execution_date']
        print(f"Pipeline completed!")
        print(f"Run ID: {run_id}")
        print(f"Execution Date: {execution_date}")

    end = PythonOperator(
        task_id='end',
        python_callable=completion_message,
    )

    # Dependencies: Fan-out and Fan-in
    start >> [python_task, check_file] >> end
```

</details>

---

## ✅ Validation

### Check DAG Integrity

```bash
# No import errors
python dags/ex01_*.py

# DAG appears in list
airflow dags list | grep ex01

# No cycles
airflow dags test ex01_hello_world 2024-01-01
```

### Verify in UI

1. **DAGs List**: All ex01 DAGs visible
2. **Graph View**: Correct task dependencies
3. **Tree View**: Successful runs (green)
4. **Logs**: Expected output in task logs

---

## 🎓 Learning Objectives

After completing this exercise, you should understand:

✅ How to create a basic DAG
✅ DAG scheduling (daily, hourly, custom)
✅ PythonOperator and BashOperator usage
✅ Setting task dependencies (>>, <<)
✅ Using XCom for data passing
✅ Accessing context variables
✅ Testing DAGs locally
✅ Navigating Airflow UI
✅ Reading task logs
✅ Dynamic task generation

---

## 📚 Additional Resources

- [Airflow Core Concepts](https://airflow.apache.org/docs/apache-airflow/stable/concepts/index.html)
- [PythonOperator Documentation](https://airflow.apache.org/docs/apache-airflow/stable/howto/operator/python.html)
- [Scheduling & Execution](https://airflow.apache.org/docs/apache-airflow/stable/scheduling-and-execution.html)

---

## 🆘 Troubleshooting

**Issue**: DAG not appearing in UI
- Check for syntax errors: `python dags/your_dag.py`
- Check scheduler is running: `airflow scheduler`
- Wait for scheduler to parse (default: 5 minutes)

**Issue**: Task failing
- Check logs in UI (click task → Log)
- Test locally: `airflow tasks test <dag_id> <task_id> <date>`
- Check Python dependencies installed

**Issue**: XCom not working
- Ensure task returns value
- Use correct task_id in xcom_pull
- Check XComs in UI (Admin → XComs)

---

**Next Exercise**: [02-operators-sensors](../02-operators-sensors/README.md)
