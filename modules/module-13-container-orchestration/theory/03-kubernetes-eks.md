# Kubernetes & Amazon EKS para Data Engineering

## 📋 Índice

1. [Introducción a Kubernetes](#intro-kubernetes)
2. [Amazon EKS Overview](#eks-overview)
3. [Kubernetes Core Concepts](#kubernetes-core-concepts)
4. [Deployments y StatefulSets](#deployments-statefulsets)
5. [Services y Networking](#services-networking)
6. [Storage en Kubernetes](#storage-kubernetes)
7. [ConfigMaps y Secrets](#configmaps-secrets)
8. [Spark on Kubernetes](#spark-kubernetes)
9. [Monitoring y Logging](#monitoring-logging)
10. [Production Best Practices](#production-best-practices)

---

## 1. Introducción a Kubernetes

**Kubernetes (K8s)** es un sistema open-source para automatizar deployment, scaling y management de aplicaciones containerizadas.

### ¿Por qué Kubernetes para Data Engineering?

```text
✅ Unified Platform
   - Batch jobs (Spark, dbt)
   - Streaming (Kafka, Flink)
   - APIs (FastAPI, Flask)
   - Databases (PostgreSQL, Cassandra)

✅ Resource Management
   - CPU, memory, GPU allocation
   - QoS classes (Guaranteed, Burstable, BestEffort)
   - Resource quotas por namespace

✅ Advanced Scheduling
   - Node affinity/anti-affinity
   - Taints and tolerations
   - Priority classes

✅ Ecosystem
   - Helm charts (Airflow, Superset, MLflow)
   - Operators (Spark, Flink, Airflow)
   - Service mesh (Istio, Linkerd)
```text

---

## 2. Amazon EKS Overview

**Amazon Elastic Kubernetes Service (EKS)** es Kubernetes administrado por AWS.

### Arquitectura EKS

```text
┌──────────────────────────────────────────────────────────────┐
│                    Amazon EKS Architecture                    │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌───────────────────────────────────────────────────────┐   │
│  │  EKS Control Plane (AWS Managed)                      │   │
│  │  • API Server (HA across 3 AZs)                       │   │
│  │  • etcd (persistent key-value store)                  │   │
│  │  • Controller Manager                                 │   │
│  │  • Scheduler                                          │   │
│  └────────────────────┬──────────────────────────────────┘   │
│                       │                                       │
│         ┌─────────────┴──────────────┐                       │
│         │                            │                       │
│         ▼                            ▼                       │
│  ┌─────────────┐             ┌─────────────┐                │
│  │  Node Group │             │  Fargate    │                │
│  │  (EC2)      │             │  Profile    │                │
│  ├─────────────┤             └─────────────┘                │
│  │             │                                             │
│  │ ┌─────────┐ │                                             │
│  │ │  Pod 1  │ │  ┌──────────────────────────┐              │
│  │ │ [nginx] │ │  │      Supporting Services │              │
│  │ └─────────┘ │  │  • VPC CNI Plugin        │              │
│  │             │  │  • CoreDNS               │              │
│  │ ┌─────────┐ │  │  • kube-proxy            │              │
│  │ │  Pod 2  │ │  │  • EBS CSI Driver        │              │
│  │ │ [spark] │ │  │  • EFS CSI Driver        │              │
│  │ └─────────┘ │  │  • AWS Load Balancer     │              │
│  │             │  │    Controller            │              │
│  └─────────────┘  └──────────────────────────┘              │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### EKS vs Self-Managed K8s

| Aspecto | EKS | Self-Managed |
|---------|-----|--------------|
| **Control Plane** | AWS-managed (HA) | You manage |
| **Upgrades** | Managed | Manual |
| **Pricing** | $0.10/hour/cluster + nodes | Only nodes |
| **IAM Integration** | Native | Manual OIDC |
| **VPC Integration** | AWS VPC CNI | Calico, Flannel |
| **Storage** | EBS, EFS CSI drivers | Manual setup |
| **Load Balancer** | ALB/NLB integration | Manual |

---

## 3. Kubernetes Core Concepts

### Pods

Un **Pod** es la unidad de ejecución más pequeña en K8s (1+ containers).

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: etl-job
  labels:
    app: etl
    env: production
spec:
  containers:
  - name: etl
    image: 123456789.dkr.ecr.us-east-1.amazonaws.com/data-etl:v1.0
    resources:
      requests:
        memory: "2Gi"
        cpu: "1000m"
      limits:
        memory: "4Gi"
        cpu: "2000m"
    env:
    - name: DATABASE_URL
      valueFrom:
        secretKeyRef:
          name: db-credentials
          key: url
    - name: BATCH_SIZE
      value: "1000"
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: efs-pvc
  restartPolicy: OnFailure
```text

### Namespaces

Aislamiento lógico de recursos:

```bash
# Create namespace
kubectl create namespace data-engineering

# Set context namespace
kubectl config set-context --current --namespace=data-engineering

# Apply manifest to namespace
kubectl apply -f deployment.yaml -n data-engineering
```text

### Labels y Selectors

```yaml
# Deployment with labels
metadata:
  labels:
    app: airflow
    component: webserver
    version: "2.7.0"
    env: production

# Service selector
spec:
  selector:
    app: airflow
    component: webserver
```text

---

## 4. Deployments y StatefulSets

### Deployment

Para **stateless applications** (APIs, workers):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-api
  namespace: data-engineering
spec:
  replicas: 3
  selector:
    matchLabels:
      app: data-api
  template:
    metadata:
      labels:
        app: data-api
    spec:
      containers:
      - name: api
        image: data-api:v2.0
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
```

### StatefulSet

Para **stateful applications** (databases, Kafka, Zookeeper):

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres
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
        image: postgres:15
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: gp3
      resources:
        requests:
          storage: 100Gi
```text

**Diferencias clave**:

- StatefulSet: Pods tienen identidad estable (postgres-0, postgres-1, postgres-2)
- Deployment: Pods tienen nombres aleatorios (api-7d8f9-xyz)
- StatefulSet: Persistent Volume por pod
- Deployment: Shared volume (o ephemeral)

---

## 5. Services y Networking

### Service Types

**ClusterIP** (default) - Internal only:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: data-api
spec:
  type: ClusterIP
  selector:
    app: data-api
  ports:
  - port: 80
    targetPort: 8080
```text

**LoadBalancer** - External access (creates AWS ALB/NLB):

```yaml
apiVersion: v1
kind: Service
metadata:
  name: data-api-external
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
spec:
  type: LoadBalancer
  selector:
    app: data-api
  ports:
  - port: 443
    targetPort: 8080
```text

**Headless Service** - For StatefulSets (DNS without load balancing):

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres-headless
spec:
  clusterIP: None  # Headless
  selector:
    app: postgres
  ports:
  - port: 5432
```

DNS resolution:

```text
postgres-0.postgres-headless.data-engineering.svc.cluster.local
postgres-1.postgres-headless.data-engineering.svc.cluster.local
postgres-2.postgres-headless.data-engineering.svc.cluster.local
```text

### Ingress (AWS Load Balancer Controller)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: data-platform
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:us-east-1:123:certificate/abc
spec:
  ingressClassName: alb
  rules:
  - host: api.data.company.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: data-api
            port:
              number: 80
  - host: airflow.data.company.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: airflow-webserver
            port:
              number: 8080
```text

---

## 6. Storage en Kubernetes

### EBS Volumes (gp3)

**StorageClass**:

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
```

**PersistentVolumeClaim**:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: spark-data
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: gp3
  resources:
    requests:
      storage: 500Gi
```text

### EFS Volumes (Shared Storage)

**StorageClass**:

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: efs-sc
provisioner: efs.csi.aws.com
parameters:
  provisioningMode: efs-ap
  fileSystemId: fs-12345678
  directoryPerms: "700"
```text

**Usage**:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: shared-data
spec:
  accessModes:
  - ReadWriteMany  # Multiple pods can read/write
  storageClassName: efs-sc
  resources:
    requests:
      storage: 100Gi
```text

---

## 7. ConfigMaps y Secrets

### ConfigMap

Para configuration non-sensitive:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  database.properties: |
    db.host=postgres.data-engineering.svc.cluster.local
    db.port=5432
    db.name=analytics

  spark.conf: |
    spark.executor.memory=4g
    spark.executor.cores=2
    spark.dynamicAllocation.enabled=true
```

**Usage**:

```yaml
spec:
  containers:
  - name: spark
    image: spark:3.5.0
    volumeMounts:
    - name: config
      mountPath: /opt/spark/conf
  volumes:
  - name: config
    configMap:
      name: app-config
      items:
      - key: spark.conf
        path: spark-defaults.conf
```text

### Secrets

Para credentials:

```bash
# Create secret from literals
kubectl create secret generic db-credentials \
  --from-literal=username=admin \
  --from-literal=password=supersecret123

# Create secret from file
kubectl create secret generic ssh-key \
  --from-file=id_rsa=~/.ssh/id_rsa

# From AWS Secrets Manager (with External Secrets Operator)
```text

**External Secrets Operator** (best practice):

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secretsmanager
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: database-credentials
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secretsmanager
    kind: SecretStore
  target:
    name: db-credentials
  data:
  - secretKey: password
    remoteRef:
      key: prod/database/password
```text

---

## 8. Spark on Kubernetes

### Spark Operator

Install Spark Operator:

```bash
helm repo add spark-operator https://googlecloudplatform.github.io/spark-on-k8s-operator
helm install spark-operator spark-operator/spark-operator \
  --namespace spark-operator \
  --create-namespace
```

### SparkApplication CRD

```yaml
apiVersion: sparkoperator.k8s.io/v1beta2
kind: SparkApplication
metadata:
  name: sales-etl
  namespace: data-engineering
spec:
  type: Python
  pythonVersion: "3"
  mode: cluster
  image: "123456789.dkr.ecr.us-east-1.amazonaws.com/spark:3.5.0-python3.11"
  imagePullPolicy: Always
  mainApplicationFile: "s3a://my-bucket/etl/sales_etl.py"

  sparkVersion: "3.5.0"

  driver:
    cores: 2
    memory: "4g"
    serviceAccount: spark
    labels:
      version: "3.5.0"
    volumeMounts:
    - name: spark-data
      mountPath: /data

  executor:
    cores: 4
    instances: 10
    memory: "8g"
    labels:
      version: "3.5.0"
    volumeMounts:
    - name: spark-data
      mountPath: /data

  volumes:
  - name: spark-data
    persistentVolumeClaim:
      claimName: efs-shared-data

  sparkConf:
    "spark.kubernetes.allocation.batch.size": "10"
    "spark.sql.adaptive.enabled": "true"
    "spark.sql.adaptive.coalescePartitions.enabled": "true"
    "spark.hadoop.fs.s3a.impl": "org.apache.hadoop.fs.s3a.S3AFileSystem"
    "spark.hadoop.fs.s3a.aws.credentials.provider": "com.amazonaws.auth.WebIdentityTokenCredentialsProvider"

  deps:
    packages:
    - "org.apache.hadoop:hadoop-aws:3.3.4"
    - "com.amazonaws:aws-java-sdk-bundle:1.12.262"

  restartPolicy:
    type: OnFailure
    onFailureRetries: 3
    onFailureRetryInterval: 10
    onSubmissionFailureRetries: 5
    onSubmissionFailureRetryInterval: 20
```text

**IRSA (IAM Roles for Service Accounts)**:

```hcl
# Terraform: Create IAM role for Spark
resource "aws_iam_role" "spark" {
  name = "eks-spark-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.eks.arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:sub" = "system:serviceaccount:data-engineering:spark"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "spark_s3" {
  role       = aws_iam_role.spark.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}
```text

**Kubernetes ServiceAccount**:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: spark
  namespace: data-engineering
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789:role/eks-spark-role
```text

### Monitor Spark Jobs

```bash
# List Spark applications
kubectl get sparkapplications -n data-engineering

# Describe application
kubectl describe sparkapplication sales-etl -n data-engineering

# View driver logs
kubectl logs sales-etl-driver -n data-engineering

# Port-forward to Spark UI
kubectl port-forward sales-etl-driver 4040:4040
# Open http://localhost:4040
```

---

## 9. Monitoring y Logging

### Prometheus Stack

Install kube-prometheus-stack:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false
```text

**ServiceMonitor** para custom metrics:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: data-api
  namespace: data-engineering
spec:
  selector:
    matchLabels:
      app: data-api
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```text

### Container Insights (AWS)

Enable CloudWatch Container Insights:

```bash
# Deploy Fluent Bit
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/quickstart/cwagent-fluent-bit-quickstart.yaml
```text

**CloudWatch Logs Insights Query**:

```sql
fields @timestamp, kubernetes.namespace_name, kubernetes.pod_name, log
| filter kubernetes.namespace_name = "data-engineering"
| filter log like /ERROR/
| stats count() by kubernetes.pod_name
| sort count desc
```

### Grafana Dashboards

Import community dashboards:

- **Kubernetes Cluster Monitoring**: Dashboard ID 7249
- **Kubernetes Pod Resources**: Dashboard ID 6417
- **Node Exporter Full**: Dashboard ID 1860

---

## 10. Production Best Practices

### Resource Management

```yaml
spec:
  containers:
  - name: app
    resources:
      # Requests: Minimum guaranteed
      requests:
        memory: "2Gi"
        cpu: "1000m"  # 1 CPU core

      # Limits: Maximum allowed
      limits:
        memory: "4Gi"
        cpu: "2000m"  # 2 CPU cores
```text

**QoS Classes**:

1. **Guaranteed**: requests = limits (highest priority)
2. **Burstable**: requests < limits
3. **BestEffort**: no requests/limits (lowest priority)

### Node Affinity

```yaml
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: workload-type
            operator: In
            values:
            - data-processing
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        preference:
          matchExpressions:
          - key: instance-type
            operator: In
            values:
            - r5.4xlarge  # Memory-optimized
```text

### Pod Disruption Budget

Previene downtime durante node maintenance:

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: data-api-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: data-api
```text

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: data-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: data-api
  minReplicas: 3
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
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
      - type: Pods
        value: 4
        periodSeconds: 15
      selectPolicy: Max
```

### Cluster Autoscaler

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-autoscaler-priority-expander
  namespace: kube-system
data:
  priorities: |-
    10:
      - .*-spot-.*  # Prefer spot instances
    5:
      - .*-ondemand-.*
```text

---

## 🎯 Comparación Final: ECS vs EKS

| Criterio | ECS Fargate | ECS EC2 | EKS |
|----------|-------------|---------|-----|
| **Management Overhead** | Muy bajo | Medio | Alto |
| **Learning Curve** | Bajo | Bajo | Alto |
| **Flexibility** | Medio | Alto | Muy Alto |
| **Ecosystem** | AWS-only | AWS-only | Multi-cloud |
| **Cost (small workload)** | $ | $ | $$ |
| **Cost (large 24/7)** | $$$ | $$ | $$ |
| **Spark Support** | Limited | Good | Excellent |
| **Stateful Apps** | Limited | Good | Excellent |
| **Best For** | Serverless ETL | GPU workloads | Complex platforms |

### Recomendaciones

**Usa ECS Fargate si**:

- Equipos pequeños sin experiencia K8s
- Workloads serverless/esporádicos
- No necesitas features avanzados de K8s

**Usa ECS EC2 si**:

- Necesitas GPUs
- Workload 24/7 predecible
- Quieres control sobre instances

**Usa EKS si**:

- Multi-cloud strategy
- Ecosistema K8s (Helm, Operators)
- Stateful applications complejas
- Spark, Flink, Airflow at scale
- Ya tienes expertise K8s

---

## 📚 Referencias

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [EKS Best Practices Guide](https://aws.github.io/aws-eks-best-practices/)
- [Spark on Kubernetes](https://spark.apache.org/docs/latest/running-on-kubernetes.html)
- [AWS Load Balancer Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/)

---

**¡Has completed la theory de Container Orchestration!** Ahora continúa con los exercises prácticos.
