# Exercise 05: Monitoring & Alerting

## 🎯 Objective

Implement comprehensive monitoring, alerting, and SLA tracking for production Airflow DAGs.

## 📚 Prerequisites

- Completed Exercises 01-04
- SMTP configured (for email alerts)
- Slack workspace (optional)
- Understanding of [03-production-patterns.md](../../theory/03-production-patterns.md)

## 📋 Tasks

### Task 1: SLA Monitoring

Create a DAG with SLA tracking:

1. Tasks with different SLAs (5 min, 10 min, 30 min)
2. SLA miss callback function
3. SLA tracking report

**Requirements:**
- Set SLA per task
- Global SLA miss callback
- Log SLA violations
- Email notification on SLA miss

### Task 2: Custom Callbacks

Implement all callback types:

1. **on_success_callback**: Log success, send Slack notification
2. **on_failure_callback**: Alert team, create ticket
3. **on_retry_callback**: Log retry attempt
4. **sla_miss_callback**: Escalate to manager

**Requirements:**
- Task-level and DAG-level callbacks
- Different notification channels
- Context information in alerts
- Callback chaining

### Task 3: Slack Integration

Integrate Slack notifications:

1. Success notifications (summary)
2. Failure alerts (with error details)
3. Long-running task warnings
4. Daily summary report

**Requirements:**
- Use SlackWebhookOperator
- Rich message formatting
- Include DAG/task details
- Execution time tracking

### Task 4: Performance Monitoring

Monitor DAG/task performance:

1. Track execution duration
2. Compare with baseline
3. Alert on degradation (>50% slower)
4. Generate performance report

**Requirements:**
- Store metrics in database
- Calculate p50, p95, p99
- Trend analysis
- Performance dashboard data

### Task 5: Health Checks

Implement pre-flight checks:

1. Check database connectivity
2. Verify API availability
3. Validate file system space
4. Check required resources
5. Skip pipeline if checks fail

**Requirements:**
- Multiple health check tasks
- ShortCircuitOperator for early exit
- Detailed health report
- Alert on infrastructure issues

---

## 🚀 Implementation

```python
# dags/ex05_monitoring.py
from airflow import DAG
from airflow.operators.python import PythonOperator, ShortCircuitOperator
from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator
from datetime import datetime, timedelta
import logging
import time

logger = logging.getLogger(__name__)

def sla_miss_callback(dag, task_list, blocking_task_list, slas, blocking_tis):
    """Called when SLA is missed"""
    logger.error(f"SLA MISS: {[t.task_id for t in task_list]}")

    # Send alert
    message = f"""
    🚨 SLA VIOLATION

    DAG: {dag.dag_id}
    Tasks: {[t.task_id for t in task_list]}
    Time: {datetime.now()}
    """

    logger.error(message)
    # send_pagerduty_alert(message)

def task_failure_callback(context):
    """Called when task fails"""
    ti = context['task_instance']
    exception = context.get('exception')

    logger.error(f"Task {ti.task_id} failed: {exception}")

    # Send Slack notification
    message = f"""
    ❌ *Task Failed*

    *DAG*: {ti.dag_id}
    *Task*: {ti.task_id}
    *Execution Date*: {context['execution_date']}
    *Error*: {exception}
    *Log*: {ti.log_url}
    """

    # slack_alert(message)

def task_success_callback(context):
    """Called when task succeeds"""
    ti = context['task_instance']
    duration = (ti.end_date - ti.start_date).total_seconds()

    logger.info(f"Task {ti.task_id} completed in {duration}s")

with DAG(
    dag_id='ex05_monitoring',
    description='Monitoring and alerting demonstration',
    schedule='@hourly',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    sla_miss_callback=sla_miss_callback,
    tags=['exercise', 'monitoring', 'ex05'],
) as dag:

    def task_with_sla():
        """Task that should complete in 5 minutes"""
        logger.info("Processing...")
        time.sleep(2)  # Simulate work
        return "completed"

    monitored_task = PythonOperator(
        task_id='monitored_task',
        python_callable=task_with_sla,
        sla=timedelta(minutes=5),
        on_success_callback=task_success_callback,
        on_failure_callback=task_failure_callback,
    )

    def send_success_summary(**context):
        """Send success notification"""
        dag_run = context['dag_run']
        duration = (dag_run.end_date - dag_run.start_date).total_seconds() if dag_run.end_date else 0

        message = f"✅ DAG {dag_run.dag_id} completed in {duration}s"
        logger.info(message)

    notify = PythonOperator(
        task_id='notify',
        python_callable=send_success_summary,
    )

    monitored_task >> notify
```

---

## ✅ Validation

```bash
# Trigger and monitor
airflow dags trigger ex05_monitoring

# Check SLA misses (if any)
airflow db check

# View logs
airflow tasks logs ex05_monitoring monitored_task 2024-01-01
```

---

## 🎓 Learning Objectives

✅ SLA configuration and monitoring
✅ Callback functions (success, failure, retry, SLA)
✅ Slack integration for alerts
✅ Performance tracking
✅ Health checks and pre-flight validation
✅ Production monitoring patterns

---

**Next Exercise**: [06-production-deployment](../06-production-deployment/README.md)
