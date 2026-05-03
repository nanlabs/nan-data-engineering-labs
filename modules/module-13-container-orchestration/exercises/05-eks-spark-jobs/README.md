# Exercise 05: Apache Spark on EKS

## 📋 Información General

- **Level**: Avanzado
- **Duration estimada**: 4-5 hours
- **Prerequisites**:
  - Exercise 04 completed
  - Cluster EKS funcionando
  - Conocimiento básico de Spark

## 🎯 Objectives de Aprendizaje

1. Instalar Spark Operator en EKS
2. Configurar IRSA para acceso a S3
3. Deployar SparkApplication CRDs
4. Large-scale ETL con PySpark
5. Monitorear Spark jobs
6. Auto-scaling de executors

---

## 📚 Context

Construirás un **sistema de procesamiento distribuido** con Apache Spark en Kubernetes:

```
┌───────────────────────────────────────────────────────────────┐
│                     EKS Cluster                               │
│                                                               │
│  ┌────────────────────────────────────────────────┐          │
│  │        Namespace: spark-operator               │          │
│  │  ┌──────────────────────────────────┐         │          │
│  │  │     Spark Operator Pod            │         │          │
│  │  │  (watches SparkApplication CRDs)  │         │          │
│  │  └──────────────┬───────────────────┘         │          │
│  └─────────────────┼────────────────────────────────┘          │
│                    │                                          │
│  ┌─────────────────▼──────────────────────────────┐          │
│  │        Namespace: spark-jobs                   │          │
│  │                                                 │          │
│  │  ┌────────────────────────────────┐           │          │
│  │  │   Spark Driver Pod             │           │          │
│  │  │   (PySpark Application)        │           │          │
│  │  └──────────┬─────────────────────┘           │          │
│  │             │                                   │          │
│  │    ┌────────┴────────┐                        │          │
│  │    │                 │                        │          │
│  │    ▼                 ▼                        │          │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐   │          │
│  │  │ Executor │  │ Executor │  │ Executor │   │          │
│  │  │  Pod 1   │  │  Pod 2   │  │  Pod 3   │   │          │
│  │  └──────────┘  └──────────┘  └──────────┘   │          │
│  │                                                │          │
│  │  Auto-scaling: 2-10 executors                 │          │
│  └─────────────────────────────────────────────────┘          │
│                          │                                    │
│                          ▼                                    │
│                    ┌────────────┐                            │
│                    │   IRSA     │                            │
│                    │ S3 Access  │                            │
│                    └────────────┘                            │
└───────────────────────────────────────────────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    S3 Bucket    │
                    │  /raw/          │
                    │  /processed/    │
                    └─────────────────┘
```

---

## 🏗️ Parte 1: Install Spark Operator

### Step 1.1: Install Operator with Helm

```bash
# Add Spark Operator Helm repo
helm repo add spark-operator https://googlecloudplatform.github.io/spark-on-k8s-operator
helm repo update

# Create namespace
kubectl create namespace spark-operator

# Install operator
helm install spark-operator spark-operator/spark-operator \
  --namespace spark-operator \
  --set webhook.enable=true \
  --set image.repository=gcr.io/spark-operator/spark-operator \
  --set image.tag=v1beta2-1.3.8-3.1.1

# Verify installation
kubectl get pods -n spark-operator
kubectl get crd | grep spark
```

### Step 1.2: Create Spark Jobs Namespace

```bash
kubectl create namespace spark-jobs
```

### Step 1.3: Configure RBAC

Create `k8s/spark-rbac.yaml`:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: spark
  namespace: spark-jobs
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: spark-role
  namespace: spark-jobs
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps"]
  verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: spark-role-binding
  namespace: spark-jobs
subjects:
- kind: ServiceAccount
  name: spark
  namespace: spark-jobs
roleRef:
  kind: Role
  name: spark-role
  apiGroup: rbac.authorization.k8s.io
```

Apply:

```bash
kubectl apply -f k8s/spark-rbac.yaml
```

---

## 🔐 Parte 2: Configure IRSA for S3 Access

### Step 2.1: Create IAM Policy

Create `terraform/spark-s3-policy.tf`:

```hcl
resource "aws_iam_policy" "spark_s3_access" {
  name        = "SparkS3AccessPolicy"
  description = "Allow Spark pods to access S3"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          "${aws_s3_bucket.data.arn}/*",
          aws_s3_bucket.data.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListAllMyBuckets"
        ]
        Resource = "*"
      }
    ]
  })
}

output "spark_s3_policy_arn" {
  value = aws_iam_policy.spark_s3_access.arn
}
```

### Step 2.2: Create IRSA (IAM Roles for Service Accounts)

```bash
# Create IAM role with IRSA
eksctl create iamserviceaccount \
  --cluster=data-engineering-cluster \
  --namespace=spark-jobs \
  --name=spark \
  --attach-policy-arn=$(terraform output -raw spark_s3_policy_arn) \
  --override-existing-serviceaccounts \
  --approve

# Verify
kubectl describe sa spark -n spark-jobs
# Should see annotation: eks.amazonaws.com/role-arn
```

---

## 📊 Parte 3: PySpark ETL Application

### Step 3.1: Create PySpark Script

Create `spark-jobs/etl_large_dataset.py`:

```python
"""
Large-scale ETL with PySpark on Kubernetes
Process 100M+ rows from S3
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, year, month, sum as _sum, count, avg
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, TimestampType
import sys

def create_spark_session(app_name):
    """Create Spark session with S3 configuration"""
    return SparkSession.builder \
        .appName(app_name) \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.aws.credentials.provider", "com.amazonaws.auth.WebIdentityTokenCredentialsProvider") \
        .getOrCreate()

def main():
    # Get parameters
    input_path = sys.argv[1]  # s3a://bucket/raw/sales/
    output_path = sys.argv[2]  # s3a://bucket/processed/sales_summary/

    print(f"Starting ETL: {input_path} -> {output_path}")

    # Create Spark session
    spark = create_spark_session("Large Scale ETL")
    spark.sparkContext.setLogLevel("INFO")

    # Define schema
    schema = StructType([
        StructField("order_id", StringType(), True),
        StructField("customer_id", StringType(), True),
        StructField("product_id", StringType(), True),
        StructField("quantity", IntegerType(), True),
        StructField("price", DoubleType(), True),
        StructField("order_date", TimestampType(), True),
        StructField("region", StringType(), True)
    ])

    # Read data
    print("Reading data from S3...")
    df = spark.read \
        .schema(schema) \
        .option("header", "true") \
        .csv(input_path)

    input_count = df.count()
    print(f"Input records: {input_count:,}")

    # Transformations
    print("Applying transformations...")

    # Calculate revenue
    df_with_revenue = df.withColumn("revenue", col("quantity") * col("price"))

    # Extract date parts
    df_with_date = df_with_revenue \
        .withColumn("year", year(col("order_date"))) \
        .withColumn("month", month(col("order_date")))

    # Aggregate by year, month, region
    sales_summary = df_with_date.groupBy("year", "month", "region") \
        .agg(
            _sum("revenue").alias("total_revenue"),
            count("order_id").alias("total_orders"),
            avg("revenue").alias("avg_order_value")
        ) \
        .orderBy("year", "month", "region")

    output_count = sales_summary.count()
    print(f"Output records: {output_count:,}")

    # Write results
    print("Writing results to S3...")
    sales_summary.write \
        .mode("overwrite") \
        .partitionBy("year", "month") \
        .parquet(output_path)

    print("ETL completed successfully!")

    # Show sample
    print("\nSample output:")
    sales_summary.show(20, truncate=False)

    spark.stop()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: etl_large_dataset.py <input_path> <output_path>")
        sys.exit(1)

    main()
```

### Step 3.2: Build Custom Spark Image

Create `spark-jobs/Dockerfile`:

```dockerfile
FROM apache/spark-py:v3.4.1

USER root

# Install additional Python packages
RUN pip install --no-cache-dir \
    boto3==1.28.85 \
    pandas==2.1.3

# Copy PySpark application
COPY etl_large_dataset.py /opt/spark/work-dir/

USER 185

CMD ["python3", "/opt/spark/work-dir/etl_large_dataset.py"]
```

Build and push:

```bash
# Build
docker build -t spark-etl:3.4.1 spark-jobs/

# Tag and push to ECR
ECR_URL=$(terraform output -raw ecr_url)
docker tag spark-etl:3.4.1 $ECR_URL/spark-etl:3.4.1
docker push $ECR_URL/spark-etl:3.4.1
```

---

## 🚀 Parte 4: SparkApplication CRD

### Step 4.1: Create SparkApplication

Create `k8s/spark-application.yaml`:

```yaml
apiVersion: sparkoperator.k8s.io/v1beta2
kind: SparkApplication
metadata:
  name: sales-etl
  namespace: spark-jobs
spec:
  type: Python
  pythonVersion: "3"
  mode: cluster
  image: YOUR_ECR_URL/spark-etl:3.4.1
  imagePullPolicy: Always
  mainApplicationFile: local:///opt/spark/work-dir/etl_large_dataset.py
  arguments:
    - "s3a://YOUR_BUCKET/raw/sales/"
    - "s3a://YOUR_BUCKET/processed/sales_summary/"

  sparkVersion: "3.4.1"

  restartPolicy:
    type: OnFailure
    onFailureRetries: 3
    onFailureRetryInterval: 10
    onSubmissionFailureRetries: 5
    onSubmissionFailureRetryInterval: 20

  driver:
    cores: 1
    coreLimit: "1200m"
    memory: "2g"
    labels:
      version: "3.4.1"
      spark-role: driver
    serviceAccount: spark
    env:
      - name: AWS_REGION
        value: "us-east-1"
    volumeMounts:
      - name: spark-local-dir
        mountPath: /tmp/spark-local

  executor:
    cores: 2
    instances: 3
    memory: "4g"
    labels:
      version: "3.4.1"
      spark-role: executor
    serviceAccount: spark
    env:
      - name: AWS_REGION
        value: "us-east-1"
    volumeMounts:
      - name: spark-local-dir
        mountPath: /tmp/spark-local

  volumes:
    - name: spark-local-dir
      emptyDir: {}

  dynamicAllocation:
    enabled: true
    initialExecutors: 2
    minExecutors: 2
    maxExecutors: 10
    shuffleTrackingTimeout: 60

  monitoring:
    exposeDriverMetrics: true
    exposeExecutorMetrics: true
    prometheus:
      jmxExporterJar: "/prometheus/jmx_prometheus_javaagent-0.17.0.jar"
      port: 8090
```

### Step 4.2: Deploy SparkApplication

```bash
# Apply
kubectl apply -f k8s/spark-application.yaml

# Watch status
kubectl get sparkapplication sales-etl -n spark-jobs -w

# View driver logs
kubectl logs sales-etl-driver -n spark-jobs -f

# View executor logs
kubectl logs -l spark-role=executor -n spark-jobs -f
```

---

## 📊 Parte 5: Sample Data Generation

### Step 5.1: Generate Large Dataset

Create `scripts/generate_sales_data.py`:

```python
"""
Generate large sales dataset (100M rows) for testing
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import boto3
import io

def generate_chunk(chunk_size, start_date, regions):
    """Generate a chunk of data"""
    np.random.seed()

    data = {
        'order_id': [f'ORD-{i:010d}' for i in range(chunk_size)],
        'customer_id': [f'CUST-{np.random.randint(1, 100000):06d}' for _ in range(chunk_size)],
        'product_id': [f'PROD-{np.random.randint(1, 10000):05d}' for _ in range(chunk_size)],
        'quantity': np.random.randint(1, 21, chunk_size),
        'price': np.random.uniform(10, 500, chunk_size).round(2),
        'order_date': [start_date + timedelta(days=np.random.randint(0, 365*3)) for _ in range(chunk_size)],
        'region': np.random.choice(regions, chunk_size)
    }

    return pd.DataFrame(data)

def upload_to_s3(df, bucket, key):
    """Upload dataframe to S3"""
    s3 = boto3.client('s3')
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    s3.put_object(Bucket=bucket, Key=key, Body=csv_buffer.getvalue())

def main():
    bucket = 'your-data-bucket'
    total_rows = 100_000_000  # 100M rows
    chunk_size = 1_000_000    # 1M rows per file
    num_chunks = total_rows // chunk_size

    regions = ['US-East', 'US-West', 'EU', 'APAC', 'LATAM']
    start_date = datetime(2021, 1, 1)

    print(f"Generating {total_rows:,} rows in {num_chunks} chunks...")

    for i in range(num_chunks):
        print(f"Generating chunk {i+1}/{num_chunks}...", end=' ')

        df = generate_chunk(chunk_size, start_date, regions)

        # Upload to S3
        key = f'raw/sales/part-{i:04d}.csv'
        upload_to_s3(df, bucket, key)

        print(f"Uploaded to s3://{bucket}/{key}")

    print(f"\nGenerated {total_rows:,} rows successfully!")

if __name__ == '__main__':
    main()
```

Run:

```bash
python scripts/generate_sales_data.py
```

---

## 📈 Parte 6: Monitoring Spark Jobs

### Step 6.1: Spark UI Port Forward

```bash
# Forward Spark UI (driver pod)
kubectl port-forward sales-etl-driver 4040:4040 -n spark-jobs

# Open browser
open http://localhost:4040
```

### Step 6.2: Create Spark History Server

Create `k8s/spark-history-server.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: spark-history-config
  namespace: spark-jobs
data:
  spark-defaults.conf: |
    spark.eventLog.enabled true
    spark.eventLog.dir s3a://YOUR_BUCKET/spark-logs/
    spark.history.fs.logDirectory s3a://YOUR_BUCKET/spark-logs/
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: spark-history-server
  namespace: spark-jobs
spec:
  replicas: 1
  selector:
    matchLabels:
      app: spark-history-server
  template:
    metadata:
      labels:
        app: spark-history-server
    spec:
      serviceAccountName: spark
      containers:
      - name: spark-history-server
        image: apache/spark:3.4.1
        command:
          - /opt/spark/sbin/start-history-server.sh
        ports:
        - containerPort: 18080
          name: web-ui
        volumeMounts:
        - name: spark-config
          mountPath: /opt/spark/conf
        env:
        - name: SPARK_HISTORY_OPTS
          value: "-Dspark.history.fs.logDirectory=s3a://YOUR_BUCKET/spark-logs/"
        - name: AWS_REGION
          value: "us-east-1"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
      volumes:
      - name: spark-config
        configMap:
          name: spark-history-config
---
apiVersion: v1
kind: Service
metadata:
  name: spark-history-server
  namespace: spark-jobs
spec:
  selector:
    app: spark-history-server
  ports:
  - protocol: TCP
    port: 18080
    targetPort: 18080
  type: LoadBalancer
```

Deploy:

```bash
kubectl apply -f k8s/spark-history-server.yaml

# Get LoadBalancer URL
kubectl get svc spark-history-server -n spark-jobs
```

### Step 6.3: CloudWatch Logs

Enable CloudWatch logging in SparkApplication:

```yaml
spec:
  monitoring:
    cloudWatch:
      enabled: true
      logGroupName: /aws/eks/spark-jobs
      logStreamNamePrefix: spark-
```

---

## 🔄 Parte 7: Scheduled Spark Jobs

### Step 7.1: ScheduledSparkApplication

Create `k8s/scheduled-spark-application.yaml`:

```yaml
apiVersion: sparkoperator.k8s.io/v1beta2
kind: ScheduledSparkApplication
metadata:
  name: daily-sales-etl
  namespace: spark-jobs
spec:
  schedule: "0 3 * * *"  # Daily at 3 AM
  concurrencyPolicy: Forbid
  successfulRunHistoryLimit: 3
  failedRunHistoryLimit: 3
  template:
    type: Python
    pythonVersion: "3"
    mode: cluster
    image: YOUR_ECR_URL/spark-etl:3.4.1
    mainApplicationFile: local:///opt/spark/work-dir/etl_large_dataset.py
    arguments:
      - "s3a://YOUR_BUCKET/raw/sales/"
      - "s3a://YOUR_BUCKET/processed/sales_summary/"
    sparkVersion: "3.4.1"
    driver:
      cores: 1
      memory: "2g"
      serviceAccount: spark
    executor:
      cores: 2
      instances: 3
      memory: "4g"
      serviceAccount: spark
    dynamicAllocation:
      enabled: true
      minExecutors: 2
      maxExecutors: 10
```

Deploy:

```bash
kubectl apply -f k8s/scheduled-spark-application.yaml

# View schedule
kubectl get scheduledsparkapplication -n spark-jobs
```

---

## ✅ Validation

### 1. Check SparkApplication Status

```bash
kubectl get sparkapplication sales-etl -n spark-jobs
# STATUS should be "COMPLETED"
```

### 2. Verify Driver Pod

```bash
kubectl get pods -l spark-role=driver -n spark-jobs
kubectl logs sales-etl-driver -n spark-jobs | grep "ETL completed"
```

### 3. Check Executors

```bash
kubectl get pods -l spark-role=executor -n spark-jobs
# Should see 2-10 executor pods (dynamic allocation)
```

### 4. Verify Output in S3

```bash
aws s3 ls s3://YOUR_BUCKET/processed/sales_summary/ --recursive --human-readable
```

### 5. Check Spark UI

```bash
kubectl port-forward sales-etl-driver 4040:4040 -n spark-jobs
# Open http://localhost:4040
# Verify stages, tasks, storage
```

---

## 🧹 Cleanup

```bash
# Delete Spark applications
kubectl delete sparkapplication sales-etl -n spark-jobs
kubectl delete scheduledsparkapplication daily-sales-etl -n spark-jobs

# Delete namespace
kubectl delete namespace spark-jobs

# Uninstall operator
helm uninstall spark-operator -n spark-operator
kubectl delete namespace spark-operator
```

---

## 🎓 Conclusión

Has aprendido:
✅ Instalar Spark Operator en EKS
✅ Configurar IRSA para acceso seguro a S3
✅ Deployar SparkApplication CRDs
✅ Large-scale ETL con PySpark (100M+ rows)
✅ Dynamic allocation de executors
✅ Monitoring con Spark UI y History Server
✅ Scheduled Spark jobs con CronJobs
✅ Production best practices (resource limits, retry policies)

**Próximo**: [Exercise 06 - Production Kubernetes](../06-production-k8s/) - Complete data platform on EKS.
