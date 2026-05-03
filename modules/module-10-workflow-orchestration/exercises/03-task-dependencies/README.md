# Exercise 03: Task Dependencies & Branching

## 🎯 Objective

Master complex task dependencies, conditional branching, trigger rules, and data flow with XComs.

## 📚 Prerequisites

- Completed [Exercise 01](../01-first-dag/README.md) and [Exercise 02](../02-operators-sensors/README.md)
- Understanding of DAG structure and operators
- Knowledge of [02-dags-and-operators.md](../../theory/02-dags-and-operators.md)

## 📋 Tasks

### Task 1: Complex Dependency Graph

Create a DAG with a complex dependency structure:

```
        start
          |
       extract
       /  |  \
      /   |   \
  clean  validate  stats
      \   |   /
       \  |  /
       aggregate
          |
       ┌──┴──┐
       |     |
    report  archive
       └──┬──┘
          |
         end
```

**Requirements:**
- Fan-out after extract
- Fan-in before aggregate
- Parallel final tasks
- Use `>>` operator for dependencies

---

### Task 2: Branching with BranchPythonOperator

Create a DAG that routes based on data size:

1. **check_data_size**: Determine data volume
2. **branch**: Choose processing path based on size
   - Small (<1000 records) → `small_processing`
   - Medium (1000-100K) → `medium_processing`
   - Large (>100K) → `large_processing`
3. **join**: Consolidate results (trigger_rule: `none_failed`)
4. **notify**: Send completion notification

**Requirements:**
- Use `BranchPythonOperator`
- Return appropriate task_id from branch function
- Handle skipped tasks correctly
- Use proper trigger rule for join

---

### Task 3: Trigger Rules Showcase

Create a DAG demonstrating all trigger rules:

```
   start
     |
   ┌─┴─┐
   |   |
task_a task_b (may fail)
   |   |
   └─┬─┘
     |
  all_success (TriggerRule.ALL_SUCCESS)
  all_failed (TriggerRule.ALL_FAILED)
  all_done (TriggerRule.ALL_DONE)
  one_success (TriggerRule.ONE_SUCCESS)
  one_failed (TriggerRule.ONE_FAILED)
  none_failed (TriggerRule.NONE_FAILED)
  none_skipped (TriggerRule.NONE_SKIPPED)
```

**Requirements:**
- Implement all 7 trigger rules
- task_b fails 50% of the time (random)
- Log which trigger rules execute
- Demonstrate practical use cases

---

### Task 4: Advanced XCom Patterns

Create a DAG demonstrating XCom patterns:

1. **extract_multiple**: Return dict with multiple values
2. **task_a**: Pull specific key from XCom
3. **task_b**: Pull different key
4. **task_c**: Pull from multiple upstream tasks
5. **aggregate**: Combine all XComs
6. **store_results**: Push large data reference (not data itself)

**Requirements:**
- Push multiple values to XCom
- Pull with `key` parameter
- Pull from multiple `task_ids`
- Demonstrate large data handling (store path, not data)

---

### Task 5: ShortCircuitOperator

Create a DAG that stops execution if condition not met:

1. **check_prerequisites**: Verify data availability
2. **short_circuit**: Stop if prerequisites not met
3. **expensive_task_1**: Only run if short_circuit passes
4. **expensive_task_2**: Only run if short_circuit passes
5. **cleanup**: Always runs (trigger_rule: `all_done`)

**Requirements:**
- Use `ShortCircuitOperator`
- Return True/False from function
- Downstream tasks skipped if False
- Cleanup task always executes

---

### Task 6: Multi-Path Conditional DAG

Create a DAG with multiple decision points:

```
        start
          |
      check_day
    /    |    \
weekday weekend holiday
   |       |      |
 process_wd process_we process_hol
   |       |      |
   └───────┴──────┘
          |
      consolidate
          |
    check_quality
      /      \
   good     bad
     |       |
  publish  notify
     └───────┘
        |
       end
```

**Requirements:**
- First branch based on day of week
- Second branch based on data quality
- Use `BranchPythonOperator` twice
- Proper trigger rules for joins

---

## 🚀 Implementation Guides

### Task 1: Complex Dependencies

```python
# dags/ex03_task1_complex_deps.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

with DAG(
    dag_id='ex03_complex_dependencies',
    description='Complex dependency graph',
    schedule='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['exercise', 'dependencies', 'ex03'],
) as dag:

    def start_task():
        logger.info("Starting pipeline")
        return "started"

    def extract_data():
        logger.info("Extracting data")
        data = list(range(1, 101))
        return data

    def clean_data(**context):
        ti = context['ti']
        data = ti.xcom_pull(task_ids='extract')
        cleaned = [x for x in data if x % 2 == 0]  # Even numbers only
        logger.info(f"Cleaned: {len(cleaned)} records")
        return cleaned

    def validate_data(**context):
        ti = context['ti']
        data = ti.xcom_pull(task_ids='extract')
        valid = all(isinstance(x, int) for x in data)
        logger.info(f"Validation: {'PASSED' if valid else 'FAILED'}")
        return valid

    def calculate_stats(**context):
        ti = context['ti']
        data = ti.xcom_pull(task_ids='extract')
        stats = {
            'count': len(data),
            'sum': sum(data),
            'avg': sum(data) / len(data),
            'min': min(data),
            'max': max(data)
        }
        logger.info(f"Stats: {stats}")
        return stats

    def aggregate_results(**context):
        ti = context['ti']
        cleaned = ti.xcom_pull(task_ids='clean')
        validated = ti.xcom_pull(task_ids='validate')
        stats = ti.xcom_pull(task_ids='stats')

        logger.info(f"Aggregating: {len(cleaned)} records, valid={validated}, stats={stats}")
        return {'cleaned': len(cleaned), 'valid': validated, 'stats': stats}

    def generate_report(**context):
        ti = context['ti']
        results = ti.xcom_pull(task_ids='aggregate')
        logger.info(f"Report: {results}")
        return "Report generated"

    def archive_data(**context):
        ti = context['ti']
        results = ti.xcom_pull(task_ids='aggregate')
        logger.info(f"Archiving: {results}")
        return "Archived"

    def end_task(**context):
        ti = context['ti']
        report = ti.xcom_pull(task_ids='report')
        archive = ti.xcom_pull(task_ids='archive')
        logger.info(f"Pipeline completed: {report}, {archive}")

    # Create tasks
    start = PythonOperator(task_id='start', python_callable=start_task)
    extract = PythonOperator(task_id='extract', python_callable=extract_data)
    clean = PythonOperator(task_id='clean', python_callable=clean_data)
    validate = PythonOperator(task_id='validate', python_callable=validate_data)
    stats = PythonOperator(task_id='stats', python_callable=calculate_stats)
    aggregate = PythonOperator(task_id='aggregate', python_callable=aggregate_results)
    report = PythonOperator(task_id='report', python_callable=generate_report)
    archive = PythonOperator(task_id='archive', python_callable=archive_data)
    end = PythonOperator(task_id='end', python_callable=end_task)

    # Define dependencies
    start >> extract
    extract >> [clean, validate, stats]
    [clean, validate, stats] >> aggregate
    aggregate >> [report, archive]
    [report, archive] >> end
```

---

### Task 2: Branching

```python
# dags/ex03_task2_branching.py
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.utils.trigger_rule import TriggerRule
from datetime import datetime, timedelta
import logging
import random

logger = logging.getLogger(__name__)

with DAG(
    dag_id='ex03_branching',
    description='Conditional branching based on data size',
    schedule='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['exercise', 'branching', 'ex03'],
) as dag:

    def check_data_size(**context):
        # Simulate checking data size
        size = random.randint(10, 200000)
        logger.info(f"Data size: {size} records")
        context['ti'].xcom_push(key='data_size', value=size)
        return size

    check_size = PythonOperator(
        task_id='check_data_size',
        python_callable=check_data_size,
    )

    def branch_based_on_size(**context):
        ti = context['ti']
        size = ti.xcom_pull(key='data_size', task_ids='check_data_size')

        if size < 1000:
            logger.info(f"Small dataset ({size}), using small processing")
            return 'small_processing'
        elif size < 100000:
            logger.info(f"Medium dataset ({size}), using medium processing")
            return 'medium_processing'
        else:
            logger.info(f"Large dataset ({size}), using large processing")
            return 'large_processing'

    branch = BranchPythonOperator(
        task_id='branch',
        python_callable=branch_based_on_size,
    )

    def small_processing(**context):
        ti = context['ti']
        size = ti.xcom_pull(key='data_size', task_ids='check_data_size')
        logger.info(f"Processing {size} records with small strategy (single-threaded)")
        return {'method': 'small', 'time': 1}

    def medium_processing(**context):
        ti = context['ti']
        size = ti.xcom_pull(key='data_size', task_ids='check_data_size')
        logger.info(f"Processing {size} records with medium strategy (multi-threaded)")
        return {'method': 'medium', 'time': 5}

    def large_processing(**context):
        ti = context['ti']
        size = ti.xcom_pull(key='data_size', task_ids='check_data_size')
        logger.info(f"Processing {size} records with large strategy (distributed)")
        return {'method': 'large', 'time': 20}

    small = PythonOperator(task_id='small_processing', python_callable=small_processing)
    medium = PythonOperator(task_id='medium_processing', python_callable=medium_processing)
    large = PythonOperator(task_id='large_processing', python_callable=large_processing)

    def join_results(**context):
        ti = context['ti']

        # Try to pull from all branches (only executed one will have data)
        results = []
        for task_id in ['small_processing', 'medium_processing', 'large_processing']:
            try:
                result = ti.xcom_pull(task_ids=task_id)
                if result:
                    results.append(result)
            except:
                pass

        logger.info(f"Results: {results}")
        return results[0] if results else None

    join = PythonOperator(
        task_id='join',
        python_callable=join_results,
        trigger_rule=TriggerRule.NONE_FAILED,  # Run even if some upstream are skipped
    )

    def notify(**context):
        ti = context['ti']
        result = ti.xcom_pull(task_ids='join')
        logger.info(f"Pipeline completed: {result}")

    notify_task = PythonOperator(
        task_id='notify',
        python_callable=notify,
    )

    # Dependencies
    check_size >> branch >> [small, medium, large] >> join >> notify_task
```

---

### Task 3: Trigger Rules

```python
# dags/ex03_task3_trigger_rules.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule
from datetime import datetime, timedelta
import logging
import random

logger = logging.getLogger(__name__)

with DAG(
    dag_id='ex03_trigger_rules',
    description='Demonstrating all trigger rules',
    schedule='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['exercise', 'trigger-rules', 'ex03'],
) as dag:

    def start_task():
        logger.info("Starting pipeline")

    start = PythonOperator(task_id='start', python_callable=start_task)

    def task_a():
        logger.info("Task A: Always succeeds")
        return "A_success"

    task_a_op = PythonOperator(task_id='task_a', python_callable=task_a)

    def task_b():
        # Randomly fail 50% of the time
        if random.random() < 0.5:
            logger.info("Task B: Failing")
            raise Exception("Task B failed randomly")
        else:
            logger.info("Task B: Succeeding")
            return "B_success"

    task_b_op = PythonOperator(
        task_id='task_b',
        python_callable=task_b,
        retries=0,  # Don't retry
    )

    # Trigger Rule: ALL_SUCCESS (default)
    def all_success_task():
        logger.info("ALL_SUCCESS: Runs only if all upstream tasks succeeded")

    all_success = PythonOperator(
        task_id='all_success',
        python_callable=all_success_task,
        trigger_rule=TriggerRule.ALL_SUCCESS,
    )

    # Trigger Rule: ALL_FAILED
    def all_failed_task():
        logger.info("ALL_FAILED: Runs only if all upstream tasks failed")

    all_failed = PythonOperator(
        task_id='all_failed',
        python_callable=all_failed_task,
        trigger_rule=TriggerRule.ALL_FAILED,
    )

    # Trigger Rule: ALL_DONE
    def all_done_task():
        logger.info("ALL_DONE: Runs when all upstream tasks done (success or failed)")

    all_done = PythonOperator(
        task_id='all_done',
        python_callable=all_done_task,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    # Trigger Rule: ONE_SUCCESS
    def one_success_task():
        logger.info("ONE_SUCCESS: Runs if at least one upstream task succeeded")

    one_success = PythonOperator(
        task_id='one_success',
        python_callable=one_success_task,
        trigger_rule=TriggerRule.ONE_SUCCESS,
    )

    # Trigger Rule: ONE_FAILED
    def one_failed_task():
        logger.info("ONE_FAILED: Runs if at least one upstream task failed")

    one_failed = PythonOperator(
        task_id='one_failed',
        python_callable=one_failed_task,
        trigger_rule=TriggerRule.ONE_FAILED,
    )

    # Trigger Rule: NONE_FAILED
    def none_failed_task():
        logger.info("NONE_FAILED: Runs if no upstream task failed (success or skipped)")

    none_failed = PythonOperator(
        task_id='none_failed',
        python_callable=none_failed_task,
        trigger_rule=TriggerRule.NONE_FAILED,
    )

    # Trigger Rule: NONE_SKIPPED
    def none_skipped_task():
        logger.info("NONE_SKIPPED: Runs if no upstream task was skipped")

    none_skipped = PythonOperator(
        task_id='none_skipped',
        python_callable=none_skipped_task,
        trigger_rule=TriggerRule.NONE_SKIPPED,
    )

    # Dependencies
    start >> [task_a_op, task_b_op]
    [task_a_op, task_b_op] >> all_success
    [task_a_op, task_b_op] >> all_failed
    [task_a_op, task_b_op] >> all_done
    [task_a_op, task_b_op] >> one_success
    [task_a_op, task_b_op] >> one_failed
    [task_a_op, task_b_op] >> none_failed
    [task_a_op, task_b_op] >> none_skipped
```

---

### Task 4: Advanced XCom

```python
# dags/ex03_task4_xcom.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)

with DAG(
    dag_id='ex03_advanced_xcom',
    description='Advanced XCom patterns',
    schedule='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['exercise', 'xcom', 'ex03'],
) as dag:

    def extract_multiple(**context):
        ti = context['ti']

        # Push multiple values with different keys
        ti.xcom_push(key='user_count', value=1000)
        ti.xcom_push(key='order_count', value=5000)
        ti.xcom_push(key='revenue', value=50000.50)
        ti.xcom_push(key='metadata', value={'source': 'database', 'timestamp': '2024-01-01'})

        logger.info("Pushed multiple values to XCom")

        # Return value goes to default key
        return "extraction_complete"

    extract = PythonOperator(
        task_id='extract_multiple',
        python_callable=extract_multiple,
    )

    def task_a(**context):
        ti = context['ti']

        # Pull specific key
        user_count = ti.xcom_pull(key='user_count', task_ids='extract_multiple')
        logger.info(f"Task A: Processing {user_count} users")

        # Process and return
        processed = user_count * 1.2
        return processed

    task_a_op = PythonOperator(task_id='task_a', python_callable=task_a)

    def task_b(**context):
        ti = context['ti']

        # Pull different key
        order_count = ti.xcom_pull(key='order_count', task_ids='extract_multiple')
        logger.info(f"Task B: Processing {order_count} orders")

        processed = order_count * 0.8
        return processed

    task_b_op = PythonOperator(task_id='task_b', python_callable=task_b)

    def task_c(**context):
        ti = context['ti']

        # Pull from multiple upstream tasks
        results = ti.xcom_pull(task_ids=['task_a', 'task_b'])
        logger.info(f"Task C: Received from multiple tasks: {results}")

        return sum(results)

    task_c_op = PythonOperator(task_id='task_c', python_callable=task_c)

    def aggregate(**context):
        ti = context['ti']

        # Pull all data from extract
        user_count = ti.xcom_pull(key='user_count', task_ids='extract_multiple')
        order_count = ti.xcom_pull(key='order_count', task_ids='extract_multiple')
        revenue = ti.xcom_pull(key='revenue', task_ids='extract_multiple')
        metadata = ti.xcom_pull(key='metadata', task_ids='extract_multiple')

        # Pull from processing tasks
        task_a_result = ti.xcom_pull(task_ids='task_a')
        task_b_result = ti.xcom_pull(task_ids='task_b')
        task_c_result = ti.xcom_pull(task_ids='task_c')

        summary = {
            'original': {
                'users': user_count,
                'orders': order_count,
                'revenue': revenue
            },
            'processed': {
                'task_a': task_a_result,
                'task_b': task_b_result,
                'task_c': task_c_result
            },
            'metadata': metadata
        }

        logger.info(f"Aggregate summary: {json.dumps(summary, indent=2)}")
        return summary

    aggregate_op = PythonOperator(task_id='aggregate', python_callable=aggregate)

    def store_results(**context):
        ti = context['ti']
        summary = ti.xcom_pull(task_ids='aggregate')

        # ❌ Don't do this: return huge data
        # large_data = generate_100mb_data()
        # return large_data

        # ✅ Do this: store data and return reference
        import json
        path = f"/tmp/results_{context['ds_nodash']}.json"
        with open(path, 'w') as f:
            json.dump(summary, f)

        logger.info(f"Stored results at: {path}")

        # Return path, not data
        return path

    store = PythonOperator(task_id='store_results', python_callable=store_results)

    # Dependencies
    extract >> [task_a_op, task_b_op]
    [task_a_op, task_b_op] >> task_c_op
    [extract, task_c_op] >> aggregate_op >> store
```

---

## ✅ Validation

### Test Branching

```bash
# Trigger multiple times to see different branches
for i in {1..5}; do
    airflow dags trigger ex03_branching
    sleep 2
done

# Check which branch executed each time
airflow tasks list ex03_branching --tree
```

### Test Trigger Rules

```bash
# Run multiple times to see random failures
for i in {1..10}; do
    airflow dags trigger ex03_trigger_rules
    sleep 5
done

# Analyze which trigger rules executed
# Check logs in UI
```

### Verify XCom Data

```bash
# Via Airflow UI: Admin → XComs
# Filter by dag_id: ex03_advanced_xcom

# Or via CLI:
airflow tasks test ex03_advanced_xcom extract_multiple 2024-01-01
# Check database
psql -U airflow -d airflow -c "SELECT * FROM xcom WHERE dag_id='ex03_advanced_xcom';"
```

---

## 🎓 Learning Objectives

After completing this exercise, you should understand:

✅ Complex dependency graphs (fan-out, fan-in)
✅ Conditional branching with BranchPythonOperator
✅ All 7 trigger rules and when to use them
✅ Advanced XCom patterns (multiple keys, multiple sources)
✅ ShortCircuitOperator for early termination
✅ Multi-path conditional DAGs
✅ Handling skipped tasks
✅ Data flow best practices

---

## 📚 Additional Resources

- [Task Dependencies](https://airflow.apache.org/docs/apache-airflow/stable/concepts/tasks.html)
- [Trigger Rules](https://airflow.apache.org/docs/apache-airflow/stable/concepts/tasks.html#trigger-rules)
- [Branching](https://airflow.apache.org/docs/apache-airflow/stable/concepts/dags.html#branching)
- [XComs](https://airflow.apache.org/docs/apache-airflow/stable/concepts/xcoms.html)

---

**Next Exercise**: [04-data-pipelines](../04-data-pipelines/README.md)
