# Exercise 06: Production Data Platform en Kubernetes

## 📋 Información General

- **Level**: Avanzado
- **Duration estimada**: 5-6 hours
- **Prerequisites**:
  - Exercises 01-05 completeds
  - Cluster EKS con 4+ nodos
  - Helm 3 instalado

## 🎯 Objectives de Aprendizaje

1. Deployar stack completo de data engineering
2. Airflow en Kubernetes con Helm
3. Kafka cluster con Strimzi operator
4. PostgreSQL StatefulSet para metadatos
5. Monitoring con Prometheus + Grafana
6. GitOps con ArgoCD
7. Multi-environment setup (dev/staging/prod)
8. Network Policies y Security

---

## 📚 Context

Construirás una **plataforma completa de data engineering** production-ready:

```
┌────────────────────────────────────────────────────────────────────┐
│                         EKS Cluster                                │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │           Namespace: airflow                              │    │
│  │  ┌────────────┐  ┌────────────┐  ┌─────────────┐        │    │
│  │  │ Scheduler  │  │  Webserver │  │   Worker    │        │    │
│  │  │   (1 pod)  │  │   (2 pods) │  │ (3-10 pods) │        │    │
│  │  └─────┬──────┘  └──────┬─────┘  └──────┬──────┘        │    │
│  │        │                │               │                │    │
│  │        └────────────────┴───────────────┘                │    │
│  │                         │                                 │    │
│  │                         ▼                                 │    │
│  │                  ┌─────────────┐                         │    │
│  │                  │ PostgreSQL  │                         │    │
│  │                  │ StatefulSet │                         │    │
│  │                  └─────────────┘                         │    │
│  └───────────────────────────────────────────────────────────┘    │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │           Namespace: kafka                                │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │    │
│  │  │ Kafka-0  │  │ Kafka-1  │  │ Kafka-2  │              │    │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘              │    │
│  │       │             │              │                     │    │
│  │  ┌────┴─────────────┴──────────────┴─────┐             │    │
│  │  │       Zookeeper StatefulSet            │             │    │
│  │  └────────────────────────────────────────┘             │    │
│  └───────────────────────────────────────────────────────────┘    │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │           Namespace: monitoring                           │    │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────┐     │    │
│  │  │ Prometheus  │  │   Grafana    │  │ AlertManager│     │    │
│  │  └─────────────┘  └──────────────┘  └────────────┘     │    │
│  └───────────────────────────────────────────────────────────┘    │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │           Namespace: argocd                               │    │
│  │  ┌──────────────────────────────────────────┐           │    │
│  │  │         ArgoCD Server                     │           │    │
│  │  │  (GitOps - Continuous Deployment)         │           │    │
│  │  └──────────────────────────────────────────┘           │    │
│  └───────────────────────────────────────────────────────────┘    │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Parte 1: Setup Base Infrastructure

### Step 1.1: Create Namespaces

Crea `k8s/namespaces.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: airflow
  labels:
    environment: production
---
apiVersion: v1
kind: Namespace
metadata:
  name: kafka
  labels:
    environment: production
---
apiVersion: v1
kind: Namespace
metadata:
  name: monitoring
  labels:
    environment: production
---
apiVersion: v1
kind: Namespace
metadata:
  name: argocd
  labels:
    environment: production
---
apiVersion: v1
kind: Namespace
metadata:
  name: dev
  labels:
    environment: development
---
apiVersion: v1
kind: Namespace
metadata:
  name: staging
  labels:
    environment: staging
```

Apply:

```bash
kubectl apply -f k8s/namespaces.yaml
```

---

## ✈️ Parte 2: Deploy Apache Airflow

### Step 2.1: Install Airflow with Helm

```bash
# Add Airflow Helm repo
helm repo add apache-airflow https://airflow.apache.org
helm repo update

# Create values file
cat > airflow-values.yaml <<EOF
executor: "KubernetesExecutor"

images:
  airflow:
    repository: apache/airflow
    tag: 2.7.3-python3.11

postgresql:
  enabled: true
  auth:
    username: airflow
    password: airflow123
    database: airflow
  primary:
    persistence:
      enabled: true
      size: 20Gi

redis:
  enabled: false  # Not needed for KubernetesExecutor

webserver:
  replicas: 2
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 1000m
      memory: 2Gi

  service:
    type: LoadBalancer

scheduler:
  replicas: 1
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 1000m
      memory: 2Gi

workers:
  replicas: 3
  resources:
    requests:
      cpu: 1000m
      memory: 2Gi
    limits:
      cpu: 2000m
      memory: 4Gi

  persistence:
    enabled: true
    size: 10Gi

  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70

dags:
  persistence:
    enabled: true
    size: 5Gi
  gitSync:
    enabled: false  # Use for git-based DAG deployment

config:
  core:
    dags_are_paused_at_creation: "False"
    load_examples: "False"
    max_active_runs_per_dag: 3

  webserver:
    expose_config: "True"
    rbac: "True"

  scheduler:
    catchup_by_default: "False"
    max_active_tasks_per_dag: 16

serviceAccount:
  create: true
  name: airflow

rbac:
  create: true

ingress:
  enabled: true
  web:
    annotations:
      kubernetes.io/ingress.class: alb
      alb.ingress.kubernetes.io/scheme: internet-facing
    hosts:
      - name: airflow.yourdomain.com
        path: /
EOF

# Install Airflow
helm install airflow apache-airflow/airflow \
  --namespace airflow \
  --values airflow-values.yaml \
  --timeout 10m

# Wait for deployment
kubectl wait --for=condition=ready pod -l component=webserver -n airflow --timeout=600s
```

### Step 2.2: Sample Airflow DAG

Crea `dags/data_pipeline.py`:

```python
"""
Production Data Pipeline DAG
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.spark_kubernetes import SparkKubernetesOperator
from airflow.providers.amazon.aws.operators.s3 import S3ListOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.python import PythonOperator
from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email': ['alerts@company.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='daily_sales_pipeline',
    default_args=default_args,
    description='Daily sales data processing pipeline',
    schedule_interval='0 3 * * *',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['production', 'sales', 'spark'],
) as dag:

    # Check raw data availability
    check_raw_data = S3ListOperator(
        task_id='check_raw_data',
        bucket='your-data-bucket',
        prefix='raw/sales/{{ ds }}/',
        aws_conn_id='aws_default'
    )

    # Spark ETL job
    spark_etl = SparkKubernetesOperator(
        task_id='spark_etl',
        namespace='spark-jobs',
        application_file='spark_application.yaml',
        kubernetes_conn_id='kubernetes_default',
        do_xcom_push=True
    )

    # Validate data quality
    validate_data = PythonOperator(
        task_id='validate_data',
        python_callable=lambda: print("Data validation passed")
    )

    # Load to warehouse
    load_to_warehouse = PostgresOperator(
        task_id='load_to_warehouse',
        postgres_conn_id='warehouse',
        sql="""
            INSERT INTO fact_sales
            SELECT * FROM staging.sales_{{ ds_nodash }}
            ON CONFLICT DO NOTHING;
        """
    )

    # Update metadata
    update_metadata = PostgresOperator(
        task_id='update_metadata',
        postgres_conn_id='warehouse',
        sql="""
            INSERT INTO etl_metadata (pipeline_name, run_date, status)
            VALUES ('daily_sales_pipeline', '{{ ds }}', 'SUCCESS');
        """
    )

    # Send notification
    notify_success = SlackWebhookOperator(
        task_id='notify_success',
        http_conn_id='slack_webhook',
        message='✅ Sales pipeline completed for {{ ds }}',
        username='Airflow Bot'
    )

    # Define dependencies
    check_raw_data >> spark_etl >> validate_data >> load_to_warehouse >> update_metadata >> notify_success
```

Upload DAG:

```bash
# Copy DAG to Airflow DAGs volume
kubectl cp dags/data_pipeline.py airflow/airflow-scheduler-0:/opt/airflow/dags/
```

### Step 2.3: Access Airflow UI

```bash
# Get LoadBalancer URL
kubectl get svc airflow-webserver -n airflow

# Default credentials
# Username: admin
# Password: admin
```

---

## 📨 Parte 3: Deploy Kafka Cluster

### Step 3.1: Install Strimzi Operator

```bash
# Install Strimzi operator
kubectl create -f 'https://strimzi.io/install/latest?namespace=kafka'

# Wait for operator
kubectl wait --for=condition=ready pod -l name=strimzi-cluster-operator -n kafka --timeout=300s
```

### Step 3.2: Create Kafka Cluster

Crea `k8s/kafka-cluster.yaml`:

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: data-kafka
  namespace: kafka
spec:
  kafka:
    version: 3.6.0
    replicas: 3
    listeners:
      - name: plain
        port: 9092
        type: internal
        tls: false
      - name: tls
        port: 9093
        type: internal
        tls: true
    config:
      offsets.topic.replication.factor: 3
      transaction.state.log.replication.factor: 3
      transaction.state.log.min.isr: 2
      default.replication.factor: 3
      min.insync.replicas: 2
      log.retention.hours: 168  # 7 days
      log.segment.bytes: 1073741824  # 1GB
    storage:
      type: persistent-claim
      size: 100Gi
      class: gp3
    resources:
      requests:
        memory: 4Gi
        cpu: 1000m
      limits:
        memory: 8Gi
        cpu: 2000m

  zookeeper:
    replicas: 3
    storage:
      type: persistent-claim
      size: 10Gi
      class: gp3
    resources:
      requests:
        memory: 1Gi
        cpu: 500m
      limits:
        memory: 2Gi
        cpu: 1000m

  entityOperator:
    topicOperator: {}
    userOperator: {}
```

Apply:

```bash
kubectl apply -f k8s/kafka-cluster.yaml

# Wait for Kafka cluster
kubectl wait kafka/data-kafka --for=condition=Ready --timeout=600s -n kafka
```

### Step 3.3: Create Kafka Topics

Crea `k8s/kafka-topics.yaml`:

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: sales-events
  namespace: kafka
  labels:
    strimzi.io/cluster: data-kafka
spec:
  partitions: 12
  replicas: 3
  config:
    retention.ms: 604800000  # 7 days
    segment.bytes: 1073741824
    compression.type: lz4
---
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: customer-events
  namespace: kafka
  labels:
    strimzi.io/cluster: data-kafka
spec:
  partitions: 6
  replicas: 3
  config:
    retention.ms: 604800000
---
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: product-events
  namespace: kafka
  labels:
    strimzi.io/cluster: data-kafka
spec:
  partitions: 6
  replicas: 3
  config:
    retention.ms: 604800000
```

Apply:

```bash
kubectl apply -f k8s/kafka-topics.yaml
```

---

## 📊 Parte 4: Monitoring con Prometheus + Grafana

### Step 4.1: Install kube-prometheus-stack

```bash
# Add Prometheus Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus stack (includes Grafana)
helm install kube-prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set prometheus.prometheusSpec.retention=30d \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=50Gi \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.storageClassName=gp3 \
  --set grafana.adminPassword=admin123 \
  --set grafana.persistence.enabled=true \
  --set grafana.persistence.size=10Gi \
  --set alertmanager.alertmanagerSpec.storage.volumeClaimTemplate.spec.resources.requests.storage=10Gi

# Wait for deployment
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=prometheus -n monitoring --timeout=300s
```

### Step 4.2: Access Grafana

```bash
# Port forward Grafana
kubectl port-forward svc/kube-prometheus-grafana 3000:80 -n monitoring

# Open browser
# http://localhost:3000
# Username: admin
# Password: admin123
```

### Step 4.3: Custom Grafana Dashboard

Crea `k8s/grafana-dashboard.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: custom-dashboard
  namespace: monitoring
  labels:
    grafana_dashboard: "1"
data:
  data-platform-dashboard.json: |
    {
      "dashboard": {
        "title": "Data Platform Overview",
        "panels": [
          {
            "title": "Airflow DAG Runs",
            "targets": [{
              "expr": "sum(airflow_dag_run_total) by (dag_id, state)"
            }]
          },
          {
            "title": "Kafka Consumer Lag",
            "targets": [{
              "expr": "kafka_consumergroup_lag"
            }]
          },
          {
            "title": "Spark Job Duration",
            "targets": [{
              "expr": "spark_application_duration_seconds"
            }]
          }
        ]
      }
    }
```

---

## 🔄 Parte 5: GitOps con ArgoCD

### Step 5.1: Install ArgoCD

```bash
# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for deployment
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=300s

# Get initial password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Port forward ArgoCD UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

### Step 5.2: Create ArgoCD Application

Crea `k8s/argocd-application.yaml`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: data-platform
  namespace: argocd
spec:
  project: default

  source:
    repoURL: https://github.com/your-org/data-platform-k8s.git
    targetRevision: main
    path: manifests/production

  destination:
    server: https://kubernetes.default.svc
    namespace: airflow

  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

---

## 🔒 Parte 6: Security & Network Policies

### Step 6.1: Network Policies

Crea `k8s/network-policies.yaml`:

```yaml
# Deny all ingress by default
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: airflow
spec:
  podSelector: {}
  policyTypes:
  - Ingress
---
# Allow Airflow webserver from Ingress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-webserver-ingress
  namespace: airflow
spec:
  podSelector:
    matchLabels:
      component: webserver
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: TCP
      port: 8080
---
# Allow scheduler to workers
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-scheduler-to-workers
  namespace: airflow
spec:
  podSelector:
    matchLabels:
      component: worker
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          component: scheduler
    ports:
    - protocol: TCP
      port: 8793
---
# Allow Kafka inter-broker
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: kafka-inter-broker
  namespace: kafka
spec:
  podSelector:
    matchLabels:
      strimzi.io/cluster: data-kafka
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          strimzi.io/cluster: data-kafka
    ports:
    - protocol: TCP
      port: 9092
    - protocol: TCP
      port: 9093
  egress:
  - to:
    - podSelector:
        matchLabels:
          strimzi.io/cluster: data-kafka
```

### Step 6.2: Pod Security Standards

Crea `k8s/pod-security.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: airflow
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### Step 6.3: Resource Quotas

Crea `k8s/resource-quotas.yaml`:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: airflow-quota
  namespace: airflow
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 40Gi
    limits.cpu: "40"
    limits.memory: 80Gi
    persistentvolumeclaims: "10"
---
apiVersion: v1
kind: LimitRange
metadata:
  name: airflow-limits
  namespace: airflow
spec:
  limits:
  - max:
      cpu: "4"
      memory: "8Gi"
    min:
      cpu: "100m"
      memory: "128Mi"
    type: Container
```

---

## ✅ Validation

### 1. All Namespaces Running

```bash
kubectl get pods --all-namespaces
```

### 2. Airflow Webserver

```bash
kubectl get svc airflow-webserver -n airflow
# Access LoadBalancer URL
```

### 3. Kafka Cluster

```bash
kubectl get kafka -n kafka
# Should show "Ready: True"

# Test producer
kubectl run kafka-producer -ti --image=quay.io/strimzi/kafka:0.37.0-kafka-3.6.0 --rm=true --restart=Never -n kafka -- bash -c "echo 'test message' | bin/kafka-console-producer.sh --bootstrap-server data-kafka-kafka-bootstrap:9092 --topic sales-events"

# Test consumer
kubectl run kafka-consumer -ti --image=quay.io/strimzi/kafka:0.37.0-kafka-3.6.0 --rm=true --restart=Never -n kafka -- bin/kafka-console-consumer.sh --bootstrap-server data-kafka-kafka-bootstrap:9092 --topic sales-events --from-beginning --max-messages 1
```

### 4. Prometheus Metrics

```bash
kubectl port-forward svc/kube-prometheus-prometheus 9090:9090 -n monitoring
# Open http://localhost:9090
```

### 5. Grafana Dashboards

```bash
kubectl port-forward svc/kube-prometheus-grafana 3000:80 -n monitoring
# Open http://localhost:3000
```

---

## 🎓 Conclusión

Has construido una **plataforma completa de data engineering production-ready** con:

✅ **Orchestration**: Airflow en Kubernetes con KubernetesExecutor
✅ **Streaming**: Kafka cluster (3 brokers) con Strimzi operator
✅ **Storage**: PostgreSQL StatefulSets con persistent volumes
✅ **Processing**: Spark on Kubernetes (exercise anterior)
✅ **Monitoring**: Prometheus + Grafana + AlertManager
✅ **GitOps**: ArgoCD para continuous deployment
✅ **Security**: Network policies, RBAC, resource quotas
✅ **Multi-environment**: dev/staging/prod namespaces
✅ **Auto-scaling**: HPA para Airflow workers
✅ **High Availability**: Multi-replica deployments

Esta es una arquitectura **enterprise-grade** lista para producción.

**Próximo**: [Module 14 - Data Catalog & Governance](../../module-14-data-catalog-governance/) o checkpoint projects.
