# Exercise 06: Production Deployment

## 🎯 Objective

Deploy Airflow to production with Docker Compose, implement CI/CD, DAG testing, and monitoring.

## 📚 Prerequisites

- Completed Exercises 01-05
- Docker and Docker Compose installed
- Git repository
- Understanding of [03-production-patterns.md](../../theory/03-production-patterns.md)

## 📋 Tasks

### Task 1: Docker Compose Deployment

Create production-ready Docker Compose setup:

1. **Services:**
   - PostgreSQL (metadata DB)
   - Redis (Celery broker)
   - Airflow Webserver (2 replicas)
   - Airflow Scheduler (2 replicas)
   - Airflow Worker (3 replicas)
   - Flower (Celery monitoring)

2. **Volumes:**
   - DAGs (shared)
   - Logs (persistent)
   - PostgreSQL data (persistent)

3. **Networks:**
   - Backend network
   - Frontend network

**Requirements:**
- CeleryExecutor configuration
- Health checks for all services
- Resource limits (CPU, memory)
- Auto-restart policies
- Environment variables from .env file

---

### Task 2: DAG Testing

Implement comprehensive tests:

**Test Suite:**
```python
# tests/test_dags.py
import pytest
from airflow.models import DagBag

def test_no_import_errors():
    dag_bag = DagBag()
    assert len(dag_bag.import_errors) == 0

def test_dag_integrity():
    dag_bag = DagBag()
    for dag_id, dag in dag_bag.dags.items():
        # No cycles
        assert dag.test_cycle() is None

        # Has owner
        assert dag.default_args.get('owner') is not None

        # Has tags
        assert len(dag.tags) > 0

def test_task_count():
    dag_bag = DagBag()
    dag = dag_bag.get_dag('my_dag')
    assert len(dag.tasks) == 5
```

**Requirements:**
- pytest configuration
- Test all DAGs
- Test individual tasks
- Mock external dependencies
- CI integration

---

### Task 3: CI/CD Pipeline

Implement GitHub Actions workflow:

**Workflow (.github/workflows/test.yml):**
```yaml
name: Test DAGs

on:
  push:
    branches: [main, develop]
  pull_request:

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
        run: pytest tests/ -v --cov=dags

      - name: Lint DAGs
        run: |
          pip install flake8
          flake8 dags/ --max-line-length=120
```

**Requirements:**
- Automated testing on PR
- Linting (flake8, black)
- Code coverage reporting
- Block merge if tests fail

---

### Task 4: Secrets Management

Implement secure secrets handling:

1. **Environment Variables:**
```bash
# .env (not in git)
AIRFLOW__CORE__FERNET_KEY=...
AIRFLOW__CORE__SQL_ALCHEMY_CONN=...
AIRFLOW__CELERY__BROKER_URL=...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

2. **Airflow Connections:**
```python
# Via CLI
airflow connections add 'prod_db' \
    --conn-type 'postgres' \
    --conn-host 'prod-db.example.com' \
    --conn-schema 'prod' \
    --conn-login 'user' \
    --conn-password 'secret'
```

3. **Secrets Backend (AWS Secrets Manager):**
```python
# airflow.cfg
[secrets]
backend = airflow.providers.amazon.aws.secrets.secrets_manager.SecretsManagerBackend
backend_kwargs = {"connections_prefix": "airflow/connections"}
```

---

### Task 5: Monitoring & Logging

Set up production monitoring:

1. **StatsD + Prometheus:**
```python
# airflow.cfg
[scheduler]
statsd_on = True
statsd_host = localhost
statsd_port = 8125
```

2. **Centralized Logging (S3):**
```python
# airflow.cfg
[logging]
remote_logging = True
remote_base_log_folder = s3://airflow-logs
```

3. **Alerting:**
- Email on failure
- Slack for critical alerts
- PagerDuty for production issues

---

### Task 6: Production Checklist

**Pre-Deployment:**
- [ ] All tests passing
- [ ] DAGs validated
- [ ] Secrets configured
- [ ] Resource limits set
- [ ] Monitoring enabled
- [ ] Backup strategy defined

**Post-Deployment:**
- [ ] Health checks passing
- [ ] Scheduler running
- [ ] Workers available
- [ ] DAGs visible in UI
- [ ] Test DAG run successful
- [ ] Logs accessible
- [ ] Alerts working

---

## 🚀 Complete Setup

### 1. Clone Repository
```bash
git clone <your-repo>
cd airflow-production
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your values
```

### 3. Start Services
```bash
docker-compose up -d
```

### 4. Verify Deployment
```bash
# Check services
docker-compose ps

# Check logs
docker-compose logs -f webserver

# Access UI
open http://localhost:8080
```

### 5. Run Tests
```bash
docker-compose exec webserver pytest tests/
```

---

## ✅ Validation

### System Health
```bash
# Scheduler health
curl http://localhost:8080/health

# Database
docker-compose exec postgres psql -U airflow -c "SELECT COUNT(*) FROM dag;"

# Redis
docker-compose exec redis redis-cli ping

# Flower (Celery)
open http://localhost:5555
```

### DAG Tests
```bash
# Run all tests
pytest tests/ -v

# Test specific DAG
airflow dags test my_dag 2024-01-01

# Validate DAG structure
airflow dags list
airflow tasks list my_dag
```

---

## 🎓 Learning Objectives

✅ Docker Compose production setup
✅ CeleryExecutor configuration
✅ DAG testing strategies
✅ CI/CD pipeline implementation
✅ Secrets management
✅ Production monitoring
✅ Deployment best practices
✅ Health checks and validation

---

## 📚 Additional Resources

- [Docker Compose Production](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html)
- [Testing DAGs](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html#testing)
- [Production Deployment](https://airflow.apache.org/docs/apache-airflow/stable/production-deployment.html)

---

**Congratulations!** You've completed all Airflow exercises. You're now ready to build production data pipelines!
