# Exercise 04: Kubernetes Basics con EKS

## 📋 Información General

- **Level**: Intermedio
- **Duration estimada**: 3-4 hours
- **Prerequisites**:
  - Exercises 01-03 completeds
  - Docker fundamentals
  - AWS account con permisos EKS

## 🎯 Objectives de Aprendizaje

1. Crear tu primer cluster EKS
2. Deployar aplicaciones con Pods y Deployments
3. Exponer servicios con Services e Ingress
4. Configurar storage con PersistentVolumes
5. Manejar secrets y configuration
6. Monitoreo básico con CloudWatch Container Insights

---

## 📚 Context

Construirás una **aplicación de data engineering completa en Kubernetes**:

```
┌─────────────────────────────────────────────────────────┐
│                    EKS Cluster                          │
│                                                         │
│  ┌──────────────────────────────────────────┐          │
│  │           Namespace: data-pipeline        │          │
│  │                                           │          │
│  │  ┌─────────────┐      ┌─────────────┐   │          │
│  │  │   FastAPI   │◄─────┤  Ingress    │   │          │
│  │  │   Service   │      │   (ALB)     │   │          │
│  │  │  (3 pods)   │      └─────────────┘   │          │
│  │  └──────┬──────┘                         │          │
│  │         │                                 │          │
│  │         ▼                                 │          │
│  │  ┌──────────────┐                        │          │
│  │  │  PostgreSQL  │                        │          │
│  │  │  StatefulSet │                        │          │
│  │  │  (PVC/EBS)   │                        │          │
│  │  └──────────────┘                        │          │
│  │                                           │          │
│  │  ┌──────────────┐                        │          │
│  │  │ ETL CronJob  │                       │          │
│  │  │ (daily 2AM)  │                       │          │
│  │  └──────────────┘                        │          │
│  └───────────────────────────────────────────┘          │
│                                                         │
│  Monitoring: CloudWatch Container Insights              │
└─────────────────────────────────────────────────────────┘
```

---

## 🏗️ Parte 1: Crear el Cluster EKS

### Step 1.1: Cluster Configuration

Crea `terraform/eks-cluster.tf`:

```hcl
# EKS Cluster
resource "aws_eks_cluster" "main" {
  name     = "data-engineering-cluster"
  role_arn = aws_iam_role.eks_cluster.arn
  version  = "1.28"

  vpc_config {
    subnet_ids              = concat(aws_subnet.private[*].id, aws_subnet.public[*].id)
    endpoint_private_access = true
    endpoint_public_access  = true
    public_access_cidrs     = ["0.0.0.0/0"]
  }

  enabled_cluster_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
    aws_iam_role_policy_attachment.eks_vpc_resource_controller
  ]
}

# IAM Role for EKS Cluster
resource "aws_iam_role" "eks_cluster" {
  name = "eks-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "eks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster.name
}

resource "aws_iam_role_policy_attachment" "eks_vpc_resource_controller" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSVPCResourceController"
  role       = aws_iam_role.eks_cluster.name
}

# EKS Node Group
resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "data-engineering-nodes"
  node_role_arn   = aws_iam_role.eks_node.arn
  subnet_ids      = aws_subnet.private[*].id

  instance_types = ["t3.medium"]

  scaling_config {
    desired_size = 2
    max_size     = 4
    min_size     = 1
  }

  update_config {
    max_unavailable = 1
  }

  labels = {
    role = "data-engineering"
  }

  tags = {
    Name = "data-engineering-nodes"
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_node_AmazonEKSWorkerNodePolicy,
    aws_iam_role_policy_attachment.eks_node_AmazonEKS_CNI_Policy,
    aws_iam_role_policy_attachment.eks_node_AmazonEC2ContainerRegistryReadOnly
  ]
}

# IAM Role for EKS Nodes
resource "aws_iam_role" "eks_node" {
  name = "eks-node-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_node_AmazonEKSWorkerNodePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_node.name
}

resource "aws_iam_role_policy_attachment" "eks_node_AmazonEKS_CNI_Policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_node.name
}

resource "aws_iam_role_policy_attachment" "eks_node_AmazonEC2ContainerRegistryReadOnly" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.eks_node.name
}

# EBS CSI Driver addon
resource "aws_eks_addon" "ebs_csi" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "aws-ebs-csi-driver"
}

# CloudWatch Container Insights
resource "aws_iam_role_policy_attachment" "eks_node_CloudWatchAgentServerPolicy" {
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
  role       = aws_iam_role.eks_node.name
}

# Output
output "cluster_endpoint" {
  value = aws_eks_cluster.main.endpoint
}

output "cluster_name" {
  value = aws_eks_cluster.main.name
}
```

### Step 1.2: Deploy Cluster

```bash
cd terraform
terraform init
terraform apply

# Configure kubectl
aws eks update-kubeconfig --name data-engineering-cluster --region us-east-1

# Verify cluster
kubectl cluster-info
kubectl get nodes
```

---

## 🚀 Parte 2: Deploy FastAPI Application

### Step 2.1: Application Code

Crea `app/main.py`:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import os
from datetime import datetime

app = FastAPI(title="Data Engineering API")

def get_db_connection():
    return psycopg2.connect(
        host=os.environ['DB_HOST'],
        port=os.environ.get('DB_PORT', 5432),
        database=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD']
    )

class DataRecord(BaseModel):
    key: str
    value: str

@app.get("/")
def root():
    return {
        "service": "Data Engineering API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
def health():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")

@app.post("/data")
def create_data(record: DataRecord):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO data_records (key, value, created_at) VALUES (%s, %s, %s)",
        (record.key, record.value, datetime.utcnow())
    )
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "created", "key": record.key}

@app.get("/data")
def list_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value, created_at FROM data_records ORDER BY created_at DESC LIMIT 100")
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    return {
        "count": len(results),
        "records": [
            {"key": r[0], "value": r[1], "created_at": r[2].isoformat()}
            for r in results
        ]
    }
```

Dockerfile:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0", "--port", "8000"]
```

requirements.txt:

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
psycopg2-binary==2.9.9
pydantic==2.5.0
```

Build and push:

```bash
docker build -t data-api:latest app/
docker tag data-api:latest $(aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(terraform output -raw ecr_url))
docker push $(terraform output -raw ecr_url)/data-api:latest
```

### Step 2.2: Kubernetes Manifests

Crea `k8s/namespace.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: data-pipeline
  labels:
    name: data-pipeline
```

Crea `k8s/configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: data-pipeline
data:
  DB_HOST: "postgres-service"
  DB_PORT: "5432"
  DB_NAME: "dataeng"
```

Crea `k8s/secret.yaml` (usando External Secrets o manual):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
  namespace: data-pipeline
type: Opaque
stringData:
  DB_USER: "dataeng"
  DB_PASSWORD: "your-secure-password"  # Use Secrets Manager in production
```

Crea `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-api
  namespace: data-pipeline
  labels:
    app: data-api
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
        image: YOUR_ECR_URL/data-api:latest
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: DB_HOST
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: DB_HOST
        - name: DB_PORT
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: DB_PORT
        - name: DB_NAME
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: DB_NAME
        - name: DB_USER
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: DB_USER
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: DB_PASSWORD
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

Crea `k8s/service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: data-api-service
  namespace: data-pipeline
spec:
  selector:
    app: data-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

---

## 💾 Parte 3: PostgreSQL StatefulSet

### Step 3.1: Storage Class

Crea `k8s/storageclass.yaml`:

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-gp3
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

### Step 3.2: PostgreSQL StatefulSet

Crea `k8s/postgres-statefulset.yaml`:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: data-pipeline
spec:
  serviceName: postgres-service
  replicas: 1
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
          name: postgres
        env:
        - name: POSTGRES_DB
          value: "dataeng"
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: DB_USER
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: DB_PASSWORD
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: "ebs-gp3"
      resources:
        requests:
          storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: data-pipeline
spec:
  selector:
    app: postgres
  ports:
  - protocol: TCP
    port: 5432
    targetPort: 5432
  clusterIP: None  # Headless service for StatefulSet
```

### Step 3.3: Initialize Database

Crea `k8s/init-db-job.yaml`:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: init-db
  namespace: data-pipeline
spec:
  template:
    spec:
      containers:
      - name: init
        image: postgres:15
        command:
        - /bin/sh
        - -c
        - |
          until pg_isready -h postgres-service -U dataeng; do
            echo "Waiting for postgres..."
            sleep 2
          done

          psql -h postgres-service -U dataeng -d dataeng <<EOF
          CREATE TABLE IF NOT EXISTS data_records (
            id SERIAL PRIMARY KEY,
            key VARCHAR(255) NOT NULL,
            value TEXT,
            created_at TIMESTAMP NOT NULL
          );
          CREATE INDEX IF NOT EXISTS idx_created_at ON data_records(created_at);
          EOF
        env:
        - name: PGPASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: DB_PASSWORD
      restartPolicy: Never
  backoffLimit: 5
```

---

## 🌐 Parte 4: Ingress con AWS Load Balancer Controller

### Step 4.1: Install AWS Load Balancer Controller

```bash
# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Add EKS chart repo
helm repo add eks https://aws.github.io/eks-charts
helm repo update

# Create IAM policy
curl -o iam_policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/main/docs/install/iam_policy.json

aws iam create-policy \
    --policy-name AWSLoadBalancerControllerIAMPolicy \
    --policy-document file://iam_policy.json

# Create IAM role with IRSA
eksctl create iamserviceaccount \
  --cluster=data-engineering-cluster \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --attach-policy-arn=arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/AWSLoadBalancerControllerIAMPolicy \
  --override-existing-serviceaccounts \
  --approve

# Install controller
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=data-engineering-cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller

# Verify installation
kubectl get deployment -n kube-system aws-load-balancer-controller
```

### Step 4.2: Create Ingress

Crea `k8s/ingress.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: data-api-ingress
  namespace: data-pipeline
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/healthcheck-path: /health
    alb.ingress.kubernetes.io/healthcheck-interval-seconds: "15"
    alb.ingress.kubernetes.io/healthcheck-timeout-seconds: "5"
    alb.ingress.kubernetes.io/healthy-threshold-count: "2"
    alb.ingress.kubernetes.io/unhealthy-threshold-count: "2"
spec:
  ingressClassName: alb
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: data-api-service
            port:
              number: 80
```

---

## ⏰ Parte 5: ETL CronJob

Crea `k8s/etl-cronjob.yaml`:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: daily-etl
  namespace: data-pipeline
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM UTC
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: etl
            image: YOUR_ECR_URL/etl-job:latest
            env:
            - name: DB_HOST
              valueFrom:
                configMapKeyRef:
                  name: app-config
                  key: DB_HOST
            - name: DB_USER
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: DB_USER
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: DB_PASSWORD
            resources:
              requests:
                memory: "1Gi"
                cpu: "1"
              limits:
                memory: "2Gi"
                cpu: "2"
          restartPolicy: OnFailure
```

---

## 📊 Parte 6: Monitoring con CloudWatch Container Insights

### Step 6.1: Install CloudWatch Agent

```bash
# Add metrics namespace
kubectl create namespace amazon-cloudwatch

# Deploy CloudWatch agent
curl https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/quickstart/cwagent-fluentd-quickstart.yaml | \
  sed "s/{{cluster_name}}/data-engineering-cluster/;s/{{region_name}}/us-east-1/" | \
  kubectl apply -f -
```

### Step 6.2: View Metrics

```bash
# Get CloudWatch console URL
echo "https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#container-insights:performance/EKS:Cluster?~(query~(controls~(CW*3a*3aEKS*2eCluster~(~'data-engineering-cluster))))"
```

---

## ✅ Deploy Todo

```bash
# Apply all manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/storageclass.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/postgres-statefulset.yaml

# Wait for postgres
kubectl wait --for=condition=ready pod -l app=postgres -n data-pipeline --timeout=300s

# Initialize database
kubectl apply -f k8s/init-db-job.yaml
kubectl wait --for=condition=complete job/init-db -n data-pipeline --timeout=120s

# Deploy API
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Deploy CronJob
kubectl apply -f k8s/etl-cronjob.yaml

# Get Ingress URL
kubectl get ingress data-api-ingress -n data-pipeline -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

---

## ✅ Validation

### 1. Check Pods

```bash
kubectl get pods -n data-pipeline
# Should see 3 data-api pods + 1 postgres pod running
```

### 2. Test API

```bash
INGRESS_URL=$(kubectl get ingress data-api-ingress -n data-pipeline -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

curl http://$INGRESS_URL/
curl http://$INGRESS_URL/health

# Create data
curl -X POST http://$INGRESS_URL/data \
  -H "Content-Type: application/json" \
  -d '{"key": "test1", "value": "Hello Kubernetes"}'

# List data
curl http://$INGRESS_URL/data
```

### 3. Check Persistent Volume

```bash
kubectl get pvc -n data-pipeline
# Should see postgres-storage-postgres-0 bound to EBS volume
```

### 4. Test Database Persistence

```bash
# Delete postgres pod
kubectl delete pod postgres-0 -n data-pipeline

# Wait for recreation
kubectl wait --for=condition=ready pod/postgres-0 -n data-pipeline --timeout=60s

# Data should still be there
curl http://$INGRESS_URL/data
```

---

## 🧹 Cleanup

```bash
# Delete resources
kubectl delete namespace data-pipeline

# Delete cluster
cd terraform
terraform destroy
```

---

## 🎓 Conclusión

Has aprendido:
✅ Crear cluster EKS con Terraform
✅ Deployments y ReplicaSets
✅ Services (ClusterIP) y Ingress (ALB)
✅ StatefulSets con PersistentVolumes
✅ ConfigMaps y Secrets
✅ CronJobs para ETL scheduling
✅ CloudWatch Container Insights

**Próximo**: [Exercise 05 - EKS Spark Jobs](../05-eks-spark-jobs/) - Apache Spark on Kubernetes.
